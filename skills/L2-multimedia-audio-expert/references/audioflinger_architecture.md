# AudioFlinger Architecture

> Android 14 — `frameworks/av/services/audioflinger/`

## Process Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  mediaserver process (or audioserver in A7+)                 │
│                                                              │
│  AudioFlinger                                                │
│    ├── MixerThread (for each output stream)                  │
│    │     ├── AudioMixer — combines multiple AudioTracks      │
│    │     └── FastMixer (optional) — low-latency path         │
│    ├── DirectOutputThread — passthrough to HAL               │
│    ├── DuplicatingThread — mirrors output to multiple sinks  │
│    └── RecordThread — handles AudioRecord input              │
│                                                              │
│  AudioPolicyService                                          │
│    └── AudioPolicyManager — routing decisions                │
└─────────────────────────────────────────────────────────────┘
```

## Thread Model

Each output device gets its own `PlaybackThread`. The thread runs at real-time priority (`SCHED_FIFO`) to meet the audio hardware's deadline.

```
MixerThread::threadLoop() — runs every <period> ms
  │
  ├── prepareTracks()         ← collect all active AudioTracks
  ├── AudioMixer::process()   ← mix all tracks into output buffer
  ├── HAL write()             ← deliver buffer to Audio HAL
  │    └── BLOCKS here until HAL accepts data (driver reads it)
  └── sleep/wait for next period
```

**BUFFER TIMEOUT** occurs when `HAL write()` blocks longer than the configured timeout (typically 2–3x the normal period). This indicates the HAL or downstream DSP is not consuming data.

## AudioTrack Buffer Path

```
App writes audio data
       │
   AudioTrack::write()
       │ shared memory (FifoBuffer)
       ▼
   AudioFlinger MixerThread
       │ reads from shared mem, mixes
       ▼
   HAL output buffer (hardware_output_buffer)
       │
   Kernel ALSA DMA
       │
   DAC / DSP
```

**Latency components:** app → AudioFlinger mix period + HAL buffer count × period + driver DMA latency

## AudioPolicy Routing

AudioPolicyManager decides which output device/stream to use based on:
- Audio attributes (usage, content type)
- Connected devices (Bluetooth A2DP, wired headset, USB)
- Volume streams
- Audio focus state

```cpp
// AudioPolicyManager selects output:
audio_io_handle_t getOutput(audio_stream_type_t stream,
    uint32_t samplingRate, audio_format_t format,
    audio_channel_mask_t channelMask,
    audio_output_flags_t flags,
    const audio_offload_info_t *offloadInfo);
```

## Audio HAL AIDL Interface (A14)

```
IModule                        ← Top-level HAL module
  ├── IStreamIn                ← Input stream (microphone)
  ├── IStreamOut               ← Output stream (speaker, headphones)
  └── ISoundDose               ← Sound exposure tracking (A14+)

IStreamOut methods:
  write(AudioBuffer buffer) → long   ← Main audio data path
  getParameters()
  setVolume(float left, float right)
  drain(AudioDrain type)
  flush()
```

## SurfaceFlinger Display Pipeline

```
App renders frame (GL/Vulkan)
       │ via BufferQueue
       ▼
SurfaceFlinger
  ├── Receives layer updates from all windows
  ├── Composition decision per VSYNC:
  │     GPU (GLES) composition   ← slow path (SurfaceFlinger renders)
  │     HWC composition          ← fast path (display hardware composites)
  └── Calls IComposer HAL
       │
HWC HAL (Hardware Composer)
       │
Display hardware
       │
Screen
```

## VSYNC and Frame Timing

```
VSYNC period (e.g., 16.67ms for 60Hz):

       │← app render window →│← SF composite window →│← display →│
       ▼                     ▼                        ▼
[VSYNC]──────────────────[VSYNC]──────────────────[VSYNC]

App must complete rendering within app render window or frame is dropped.
SurfaceFlinger must complete composition within composite window.
```

**Dropped frame diagnosis:**
```bash
adb shell dumpsys SurfaceFlinger | grep -E "missed|jank|deadline"
adb shell dumpsys gfxinfo <package> framestats
# Look for: JANKY_FRAMES, MISSED_VSYNC
```

## Camera Request Pipeline

```
configureStreams(StreamConfiguration)
       │
processCaptureRequest(CaptureRequest)
       │
ISP processes frame
       │
processCaptureResult(CaptureResult + buffer)
       │ metadata + image buffer returned to CameraService
       ▼
App receives frame via ImageReader
```

**Pipeline stall indicators:**
- `processCaptureResult` not called within expected time → ISP stuck
- Buffer queue full → downstream consumer (ImageReader) not draining fast enough
- `REQUEST_ERROR` in result → HAL failed to process request

## Key Diagnostic Commands

```bash
# Audio latency report
adb shell dumpsys media.audio_flinger | grep -A3 "latency\|Output thread"

# SurfaceFlinger composition mode
adb shell dumpsys SurfaceFlinger | grep "HWC\|GPU\|composition"

# Camera HAL state
adb shell dumpsys media.camera | head -50

# MediaCodec codec list with capabilities
adb shell media list-codecs

# Audio focus events
adb logcat -s AudioManager:V AudioFocusDeathHandler:V
```

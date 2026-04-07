---
name: multimedia-audio-expert
layer: L2
path_scope: frameworks/av/, frameworks/native/services/surfaceflinger/, hardware/interfaces/audio/, hardware/interfaces/camera/, hardware/interfaces/graphics/
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `frameworks/av/` | Audio, Video, Camera, MediaCodec stack (AV framework) |
| `frameworks/av/services/audioflinger/` | AudioFlinger — central audio mixing daemon |
| `frameworks/av/services/audiopolicy/` | AudioPolicyService — routing decisions |
| `frameworks/av/services/mediacodec/` | MediaCodec service — hardware video codec |
| `frameworks/av/services/camera/` | CameraService |
| `frameworks/av/media/` | MediaExtractor, MediaPlayer, NuPlayer |
| `frameworks/native/services/surfaceflinger/` | SurfaceFlinger — display compositor |
| `hardware/interfaces/audio/` | Audio HAL AIDL interfaces |
| `hardware/interfaces/camera/` | Camera HAL AIDL interfaces |
| `hardware/interfaces/graphics/` | Graphics / HWC HAL interfaces |
| `hardware/interfaces/media/` | MediaCodec HAL interfaces |

---

## Trigger Conditions

Load this skill when the task involves:
- AudioFlinger errors: `BUFFER TIMEOUT`, `write blocked`, underruns
- AudioPolicy routing — output stream selection, audio focus
- MediaCodec failures — codec negotiation, format mismatch
- CameraService — HAL open failures, session lifecycle
- SurfaceFlinger — dropped frames, HWC layer scheduling
- Display pipeline — composition mode (GPU vs HWC), fence synchronization
- Camera HAL debugging — request pipeline stalls, metadata issues
- Video playback pipeline — NuPlayer, MediaExtractor, DRM
- Audio HAL AIDL interface questions
- `IComposer`, `IHwcComposerClient` (HWC2/HWC3) interface questions
- Latency tuning for audio or graphics

---

## Architecture Intelligence

### Audio Stack

```
App
 │  AudioTrack / MediaPlayer API
 ▼
AudioFlinger  (frameworks/av/services/audioflinger/)
 │  Mixing engine — combines all audio tracks
 │  Applies effects, handles focus
 ▼
AudioPolicy   (frameworks/av/services/audiopolicy/)
 │  Decides which output device / stream to use
 ▼
Audio HAL     (hardware/interfaces/audio/)
 │  AIDL interface: IModule, IStreamIn, IStreamOut
 ▼
Kernel ALSA   (/dev/snd/*)
 ▼
DSP / Codec Hardware
```

### Audio Buffer Path

```
AudioTrack (app) → shared memory (AudioTrackShared)
                         │
                 AudioFlinger MixerThread
                         │
                 HAL write() call
                         │  ← BUFFER TIMEOUT occurs here if HAL blocks
                 Audio HAL implementation
                         │
                 Kernel driver (ALSA)
```

**BUFFER TIMEOUT diagnosis:**
1. Check if HAL `write()` is blocking → DSP not consuming data.
2. Check `AudioFlinger` thread period vs HAL buffer size mismatch.
3. Look for priority inversion — AudioFlinger thread must be `SCHED_FIFO`.

### SurfaceFlinger / Display Pipeline

```
App renders → BufferQueue → SurfaceFlinger
                                  │
                        Composition decision:
                          GPU (GLES) composition   ← fallback
                          HWC (hardware) composition ← preferred
                                  │
                        Display HAL (IComposer)
                                  │
                        Panel / HDMI output
```

**Dropped frame diagnosis:**
1. `adb shell dumpsys SurfaceFlinger` — check missed deadlines, jank.
2. Check HWC layer count — exceeding HWC plane limit forces GPU composition.
3. Check fence signaling — missing `acquireFence` signal = stall.
4. `systrace` with `gfx` and `view` categories for frame timeline.

### Camera Pipeline

```
CameraService (frameworks/av/services/camera/)
      │  ICameraDevice AIDL
      ▼
Camera HAL3 (hardware/interfaces/camera/)
      │  IDevice, ICaptureSession, ICaptureRequest
      ▼
ISP driver / Kernel
      ▼
Sensor

Request pipeline:
  configureStreams() → repeatingRequest() → processCaptureResult()
  Stall indicators: result metadata delay, buffer queue full
```

### MediaCodec

```
App uses MediaCodec API
      │
MediaCodec service (frameworks/av/services/mediacodec/)
      │
OmxStore / Codec2 component store
      │
Hardware decoder/encoder (via Media HAL)
      │
Video codec hardware

Key failure modes:
  - ERROR_INSUFFICIENT_OUTPUT_PROTECTION: DRM policy block
  - INFO_OUTPUT_FORMAT_CHANGED: codec renegotiated format mid-stream
  - BUFFER TIMEOUT in dequeueOutputBuffer: downstream consumer stalled
```

### Android 15 Multimedia Changes

| Change | Impact |
|--------|--------|
| Low Light Boost | New camera auto exposure mode for low-light preview brightness adjustment |
| Camera feature combination query API | Platform API to query supported camera feature combinations |
| Head tracking over LE Audio | Latency mode adjustments based on head tracking transport |
| Region of Interest (RoI) video encoding | Standardized RoI integration for video encoding pipelines |
| Audio AIDL HAL: CAP not ported | Configurable Audio Policy not available in AIDL HAL for A14/A15; blocks OEM migration |

---

## Forbidden Actions

1. **Forbidden:** Modifying AudioFlinger mixing logic to add new audio effects — custom effects belong in the Audio Effects HAL (`hardware/interfaces/audio/effect/`), not AudioFlinger core.
2. **Forbidden:** Bypassing AudioPolicy routing by writing directly to ALSA from an app — all audio must go through AudioFlinger; direct ALSA access requires root and breaks audio focus.
3. **Forbidden:** Setting SurfaceFlinger buffer queue depths without profiling — increasing `NUM_BUFFER_SLOTS` increases latency; always measure jank before and after.
4. **Forbidden:** Opening a Camera HAL session from multiple clients simultaneously without using `CameraManager` arbitration — CameraService enforces exclusive access.
5. **Forbidden:** Routing ALSA kernel driver issues to this skill — kernel driver changes belong to `L2-kernel-gki-expert`.
6. **Forbidden:** Modifying `hardware/interfaces/audio/` AIDL without bumping the interface version — all HAL interface changes must follow the versioning procedure in `L2-hal-vendor-interface-expert`.

---

## Tool Calls

```bash
# Dump AudioFlinger state
adb shell dumpsys media.audio_flinger

# Dump AudioPolicy routing
adb shell dumpsys media.audio_policy

# Check SurfaceFlinger composition stats
adb shell dumpsys SurfaceFlinger | grep -A5 "VSYNC\|jank\|dropped"

# Capture systrace for graphics pipeline
python3 systrace.py gfx view -o trace.html

# List camera devices and their status
adb shell dumpsys media.camera

# Check MediaCodec codec list
adb shell media list-codecs

# Monitor audio underruns in real time
adb logcat -s AudioFlinger:V AudioPolicyManager:V
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| Audio/Camera HAL AIDL interface version bump | `L2-hal-vendor-interface-expert` |
| SELinux denial for media daemon | `L2-security-selinux-expert` |
| Build failure in `frameworks/av/` | `L2-build-system-expert` |
| Kernel ALSA driver or V4L2 driver issue | `L2-kernel-gki-expert` |
| MediaCodec service `.rc` or startup issue | `L2-init-boot-sequence-expert` |

Emit `[L2 MEDIA → HANDOFF]` before transferring.

---

## References

- `references/audioflinger_architecture.md` — AudioFlinger threading model, mixing pipeline, and HAL interface.
- `frameworks/av/services/audioflinger/README.md` — upstream docs.
- `frameworks/native/services/surfaceflinger/docs/` — SurfaceFlinger internals.
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

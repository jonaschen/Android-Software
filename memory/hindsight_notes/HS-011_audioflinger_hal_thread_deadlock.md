# HS-011: AudioFlinger HAL Thread Deadlock Pattern

**Category:** Multimedia / Audio
**Skills involved:** L2-multimedia-audio-expert, L2-hal-vendor-interface-expert
**Android versions:** All

## Insight

A common AudioFlinger deadlock occurs when the audio HAL implementation calls back into the framework from within a HAL callback (e.g., `IStreamOutEventListener::onCodecFormatChanged`). If the framework holds `AudioFlinger::mLock` at that point, a deadlock results:

```
Thread A (AudioFlinger): holds mLock → calls HAL method
Thread B (HAL callback): called from HAL → tries to call framework → waits for mLock
```

**Detection:** `adb shell debuggerd -b <audioserver_pid>` will show the two threads in a BLOCKED state waiting for each other.

**Fix pattern:** HAL callbacks that need to call back into the framework must post to a separate thread (e.g., `AudioFlinger::mAsyncCallbackThread`) rather than calling directly.

**Alternative:** If using AIDL HAL, use asynchronous notification via `oneway` methods to avoid synchronous re-entry.

## Why This Matters

Audio glitches from deadlocks are intermittent and hard to reproduce. The lock graph must be explicitly reviewed whenever a new HAL callback is added.

## Trigger

When an `android.hardware.audio` HAL AIDL interface adds a new callback method, always route to `L2-multimedia-audio-expert` to review the threading model.

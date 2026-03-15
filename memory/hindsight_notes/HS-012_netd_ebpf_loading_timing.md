# HS-012: netd eBPF Programs Load After Kernel Init — Don't Race

**Category:** Connectivity / Kernel
**Skills involved:** L2-connectivity-network-expert, L2-kernel-gki-expert
**Android versions:** Android 12+ (eBPF in netd)

## Insight

Android's `netd` loads eBPF programs (`.o` files compiled from BPF C source) at startup via `bpf_obj_get`. These programs are pinned to the BPF filesystem at `/sys/fs/bpf/`. However, the BPF filesystem is only available after the kernel has mounted it, which happens in the `post-fs` phase.

**Race condition:** Services that try to use netd eBPF features immediately after `netd` starts (before eBPF programs finish loading) get `ENOENT` on `bpf_obj_get`. The window is typically 100–500ms on first boot.

**Fix:**
1. `netd` uses an internal "ready" flag — wait for `ConnectivityService.onNetdEvent(NETD_EVENT_AIDL_STARTED)` before using eBPF-backed APIs.
2. For new BPF programs: add them to `netd/bpf_progs/` and ensure they are listed in `NetdUpdatablePublicDeps.h`.

**Debugging:** `adb shell bpftool prog list` to see loaded programs; `adb shell cat /proc/sys/net/core/bpf_jit_enable` to confirm JIT.

## Why This Matters

eBPF loading failures manifest as silent traffic metering errors or missing firewall rules — there is no obvious crash. The race is only visible in production at scale.

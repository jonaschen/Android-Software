# HS-032: Android 15 Framework, Boot, Media, and Connectivity Changes

> **Date:** 2026-04-08
> **Skills:** L2-framework-services-expert, L2-init-boot-sequence-expert, L2-multimedia-audio-expert, L2-connectivity-network-expert, L2-bootloader-lk-expert
> **Source:** Phase 4.5 A15 validation pass

## Insight

Android 15 introduces changes across multiple subsystems that share a common theme: tightening restrictions and adding new capabilities.

### Framework Services
- **Foreground service restrictions from BOOT_COMPLETED:** Receivers for `BOOT_COMPLETED` can no longer launch certain FGS types. This throws `ForegroundServiceStartNotAllowedException`. OEMs with vendor daemons started via broadcast receivers must audit their startup paths.
- **New `mediaProcessing` FGS type:** Dedicated foreground service type for transcoding and media processing; previously these used generic types.
- **Soft restart deprecated:** The `SoftRestart` mechanism (restarting userspace without kernel reboot) is removed. Full reboots are now required.

### Init / Boot Sequence
- **Virtual A/B v3:** Faster and smaller OTA updates. Boot slot selection logic updated to support the new update mechanism.
- **16KB page size boot support:** Bootloaders must determine page size from the kernel image header. Dual OTA images (4K + 16K) enable page size toggling.
- **Soft restart removal** also impacts init, which previously supported the soft restart trigger path.

### Multimedia / Audio
- **Low Light Boost:** New auto exposure mode in the camera subsystem for adjusting preview brightness in low-light conditions.
- **Camera feature combination query API:** Allows apps to check if a specific combination of camera features is supported before attempting to use them.
- **Audio AIDL HAL CAP gap persists:** Configurable Audio Policy is not ported to AIDL HAL in A14 or A15. OEMs relying on CAP must continue using HIDL audio HAL.

### Connectivity / Networking
- **Android Packet Filter v6 (APF v6):** Adds counters for debugging and packet transmission support. Significant change to the netd packet filtering path.
- **802.11az Wi-Fi RTT:** Support for IEEE 802.11az protocol improves Wi-Fi ranging accuracy.

### Bootloader
- **16KB page size support** requires bootloader awareness of kernel page size via image header inspection. The new `ro.boot.hardware.cpu.pagesize` property signals page size to userspace.

## Cross-Skill Impact

When an OEM vendor daemon fails to start after A15 upgrade:
1. Check FGS restrictions (framework-services-expert) — is it launched from BOOT_COMPLETED?
2. Check init .rc class ordering (init-boot-sequence-expert) — did startup sequence change with V A/B v3?
3. Check SELinux denials (security-selinux-expert) — new domain boundaries for Private Space may affect adjacent domains.

## AOSP Paths

- `frameworks/base/services/` — FGS restriction enforcement
- `system/core/init/` — Virtual A/B v3, soft restart removal
- `frameworks/av/` — Low Light Boost, camera feature query
- `packages/modules/Connectivity/` — APF v6
- `bootable/` — Virtual A/B v3 update mechanism

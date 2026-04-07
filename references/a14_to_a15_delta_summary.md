# Android 14 → Android 15 Delta Summary

> **Date:** 2026-04-08
> **Purpose:** Per-skill impact summary for the A14→A15 validation pass (Phase 4.5)
> **Baseline:** Android 14.0.0_r1 → Android 15 (API level 35, Vanilla Ice Cream)

---

## Overview

Android 15 shipped October 2024. Key platform themes:
- **VNDK deprecation** — former VNDK libraries treated as ordinary vendor/product libraries
- **16KB page size support** — build-time and runtime support for 16KB page-aligned devices
- **AIDL mandatory for new HALs** — HIDL fully deprecated, AIDL is the only path forward
- **GKI android15-6.6** — new kernel baseline (Linux 6.6 LTS), one GKI per release
- **AVF enhancements** — updatable VMs, remote attestation, experimental device assignment
- **Virtual A/B v3** — faster, smaller OTA updates
- **Privacy & security hardening** — private space, signature permission allowlist, mobile network transparency

---

## Per-Skill Delta

### L1-aosp-root-router

| Change | Impact |
|--------|--------|
| VNDK deprecation | `system/vndk/` path scope may reduce in relevance; routing still valid |
| No new top-level directories | Routing table unchanged |

**Action:** Update `android_version_tested` to Android 15. No routing table changes needed.

---

### L2-build-system-expert

| Change | Impact |
|--------|--------|
| Sandboxed genrules | Genrules can only access listed `srcs`; breaks builds relying on implicit inputs |
| Python 2 fully removed | All build scripts must be Python 3 |
| Sysprop library reference change | Direct cc_module deps on `sysprop_library` disallowed; use generated `libfoo` |
| Gensrcs depfile removal | `depfile` property disallowed; use explicit deps or `tool_files` |
| Genrule directory inputs banned | Must specify individual files, not directories |
| Module name validation | Characters restricted to `a-z A-Z 0-9 _.+-=,@~` |
| System property duplication error | Multiple assignments per partition now fail build |
| Dexpreopt uses-library checks | Java modules must declare `uses_libs` / `optional_uses_libs` |
| Soong plugin validation | Restricted to existing plugins in vendor/hardware dirs |

**Action:** Update Architecture Intelligence with sandboxed genrules, Python 2 removal, and new validation rules.

---

### L2-security-selinux-expert

| Change | Impact |
|--------|--------|
| Signature permission allowlist | Platform enforces explicit allowlist for signature perms requested by non-system apps |
| Private space isolation | New SELinux domain boundaries for private space feature |
| FBE `dusize_4k` flag | New file-based encryption configuration option |
| Mobile network transparency | New privacy settings and network security notifications |
| 2G toggle enforcement | `KEY_HIDE_ENABLE_2G` deprecated; carriers cannot hide toggle |

**Action:** Update Architecture Intelligence to note signature permission allowlist enforcement and private space domain boundaries.

---

### L2-hal-vendor-interface-expert

| Change | Impact |
|--------|--------|
| VNDK deprecated | Former VNDK libraries treated as regular vendor/product libs |
| AIDL mandatory for all new HALs | No new HIDL interfaces accepted |
| Health HAL 3.0 | Updated health interface |
| Thermal HAL 2.0 | Updated thermal interface |
| Domain Selection Service | New IMS vs circuit-switched domain selection API |
| Camera feature combination query | New platform API for querying supported camera feature combos |

**Action:** Update Architecture Intelligence: VNDK deprecation impact, AIDL-only enforcement, new HAL versions.

---

### L2-framework-services-expert

| Change | Impact |
|--------|--------|
| Foreground service restrictions | BOOT_COMPLETED receivers cannot launch certain FGS types; `ForegroundServiceStartNotAllowedException` |
| New `mediaProcessing` FGS type | New foreground service type for transcoding/media processing |
| Minimum targetSdkVersion 24 | Apps below API 24 blocked from installation |
| Compiler filter override API | `setAdjustCompilerFilterCallback` for package-specific compiler filters |
| Soft restart deprecated | `SoftRestart` mechanism removed in A15 |
| Subscription-level carrier capabilities | Carriers specify per-subscription service capabilities |

**Action:** Update Architecture Intelligence to note FGS restriction changes and soft restart deprecation.

---

### L2-init-boot-sequence-expert

| Change | Impact |
|--------|--------|
| Virtual A/B v3 | New OTA update mechanism affecting boot slot selection and update flow |
| 16KB page size boot support | Bootloader must determine page size from kernel header; dual OTA (4K + 16K) |
| Soft restart deprecated | No more runtime restarts via soft restart path |

**Action:** Update Architecture Intelligence with Virtual A/B v3 notes and 16KB boot implications.

---

### L2-version-migration-expert

| Change | Impact |
|--------|--------|
| All of the above | This skill's A14→A15 migration table is the primary consumer |
| 16KB page size mandatory timeline | Mandatory for Play Store apps targeting A15+ by May 2026 |

**Action:** Already tracks A14→A15; verify migration table accuracy, update version field.

---

### L2-multimedia-audio-expert

| Change | Impact |
|--------|--------|
| Low Light Boost | New camera auto exposure mode for low-light preview |
| Camera feature combination query API | Platform API for querying supported feature combos |
| Head tracking over LE Audio | Latency mode adjustments for head tracking transport |
| Region of Interest (RoI) video encoding | Standardized RoI integration for video encoding |
| Audio AIDL HAL: CAP not ported | Configurable Audio Policy not available in AIDL HAL for A14/A15 |

**Action:** Update Architecture Intelligence with new camera APIs and audio AIDL CAP gap note.

---

### L2-connectivity-network-expert

| Change | Impact |
|--------|--------|
| Android Packet Filter v6 (APF v6) | Adds counters, packet transmission; significant netd change |
| 802.11az Wi-Fi RTT | IEEE 802.11az support for ranging |
| NFC: proprietary NCI commands | New Android Proprietary NCI Commands interface |
| Watch companion profile update | `POST_NOTIFICATIONS` permission added |

**Action:** Update Architecture Intelligence with APF v6 in netd section.

---

### L2-kernel-gki-expert

| Change | Impact |
|--------|--------|
| GKI android15-6.6 (Linux 6.6 LTS) | New kernel baseline; one GKI per release (no android15-6.1) |
| KMI break | android14-6.1 → android15-6.6 requires full module rebuild |
| 16KB page size GKI builds | Available as on-demand builds alongside 4KB |
| android14-6.1 forward-compatible | Can run on A15 devices but KMI not interchangeable |

**Action:** Update `android_version_tested` to reflect GKI 6.6 baseline. Note KMI break.

---

### L2-bootloader-lk-expert

| Change | Impact |
|--------|--------|
| 16KB page size boot | Bootloader must read page size from kernel header |
| `ro.boot.hardware.cpu.pagesize` | OEM-specific property for page size signaling |
| Virtual A/B v3 | New update mechanism affects slot selection logic |
| Dual kernel OTA | Two boot images (4K + 16K) for page size toggle |

**Action:** Update Architecture Intelligence with 16KB boot implications.

---

### L2-trusted-firmware-atf-expert

| Change | Impact |
|--------|--------|
| AVF device assignment (experimental) | Peripheral devices assigned to protected VMs at firmware level |
| No direct ATF API changes documented | ATF changes are vendor-driven, not in AOSP mainline |

**Action:** Update `android_version_tested`. Note AVF device assignment experimental feature.

---

### L2-virtualization-pkvm-expert

| Change | Impact |
|--------|--------|
| Already at Android 15 | Updatable VMs, remote attestation, device assignment documented |

**Action:** Already validated at A15. No changes needed.

---

## Sources

- [Android 15 and Android 15-QPR1 Release Notes](https://source.android.com/docs/whatsnew/android-15-release)
- [Android 15 Features and Changes Summary](https://developer.android.com/about/versions/15/summary)
- [Android 15 Behavior Changes](https://developer.android.com/about/versions/15/behavior-changes-15)
- [Build System Changes](https://android.googlesource.com/platform/build/+/main/Changes.md)
- [GKI android15-6.6 Release Builds](https://source.android.com/docs/core/architecture/kernel/gki-android15-6_6-release-builds)
- [16KB Page Size Support](https://source.android.com/docs/core/architecture/16kb-page-size/16kb)
- [AIDL for HALs](https://source.android.com/docs/core/architecture/aidl/aidl-hals)

---

*Generated by steward agent — Phase 4.5 A15 validation pass (2026-04-08)*

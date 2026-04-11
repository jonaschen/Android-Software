# Android 15 → 16 Per-Skill Delta Summary

> **Date:** 2026-04-12
> **Source:** Hindsight notes HS-033 through HS-039, Phase 5 research sessions
> **Status:** Based on available A16 intelligence. Full source verification pending AOSP A16 source drop (expected Q2 2026).

---

## Overview

Android 16 introduces significant changes across kernel, security, multimedia, connectivity, virtualization, bootloader, and build system layers. This document summarizes the per-skill impact for all 12 L2 skills in the Android-Software-Owner skill set.

---

## Per-Skill Delta

### L2-kernel-gki-expert (DIRTY → CLEAN)

**Kernel baseline:** GKI android16-6.12 (Linux 6.12 LTS)

| Change | Impact | Reference |
|--------|--------|-----------|
| KMI break from android15-6.6 | Full vendor module rebuild required | HS-033 |
| EEVDF replaces CFS | Scheduling latency changes; audit SCHED_FIFO/RT-priority code | HS-033 |
| Per-VMA locks | Replaces `mmap_lock`; audit driver code using `mmap_lock` directly | HS-033 |
| Proxy Execution | New scheduling feature mitigating priority inversion | HS-033 |
| RCU_LAZY | Deferred RCU callbacks for power savings | HS-033 |
| CONFIG_ZRAM_MULTI_COMP | Multi-algorithm ZRAM compression | HS-033 |
| Memory allocation profiling | `CONFIG_MEM_ALLOC_PROFILING` attributes allocations to source | HS-033 |
| Clang 19.0.1 stricter bounds | `__counted_by` enforces runtime bounds; size field must be set before access | HS-033 |
| CONFIG_OF_DYNAMIC default on | Exposes driver DT node refcount bugs | HS-033 |
| 16KB page GKI on-demand | Available for android16-6.12 | HS-033 |

---

### L2-security-selinux-expert (DIRTY → CLEAN)

| Change | Impact | Reference |
|--------|--------|-----------|
| IOCTL hardening macro (QPR2) | New SELinux macro blocks restricted IOCTLs in production; GPU drivers primary target | HS-038 |
| KeyMint 4.0 moduleHash | New attestation field for APEX module integrity verification | HS-038 |
| KeyMint in pVM | Security domain model changes with pKVM early boot VMs | HS-037, HS-038 |

---

### L2-multimedia-audio-expert (DIRTY → CLEAN)

| Change | Impact | Reference |
|--------|--------|-----------|
| CAP AIDL fixed | Configurable Audio Policy AIDL gap resolved; automotive audio can use AIDL backend | HS-035 |
| APV codec | Advanced Professional Video codec for high-bitrate intra-frame video | HS-035 |
| AV1 transition | Platform transitioning to AV1 as preferred codec; affects MediaCodec defaults | HS-035 |
| HDR enhancements | SDR fallback, HDR screenshot, HLG/DolbyVision capture | HS-035 |
| Media Quality Framework | Standardized API for Android TV picture/audio quality | HS-035 |
| EEVDF scheduler impact | May change AudioFlinger thread scheduling latency | HS-033 |

---

### L2-connectivity-network-expert (DIRTY → CLEAN)

| Change | Impact | Reference |
|--------|--------|-----------|
| Unified Ranging Module | Aggregates UWB, BT Channel Sounding, BT RSSI, WiFi RTT APIs | HS-039 |
| AIS Bluetooth GATT | New characteristic lets BT devices read Android API level | HS-039 |
| IMS Service API expansion | Traffic session management, EPS fallback, EmergencyCallbackModeListener | HS-039 |
| SoftAp disconnect callback | `onClientsDisconnected` with disconnect reasons | HS-039 |
| BT bond loss intents | ACTION_KEY_MISSING, ACTION_ENCRYPTION_CHANGE | HS-039 |
| BT LE Audio Sharing | Multi-device audio routing with LE Audio | HS-039 |
| CDM removeBond API | Programmatic BT unpairing via CompanionDeviceManager | HS-039 |

---

### L2-trusted-firmware-atf-expert (DIRTY → CLEAN)

| Change | Impact | Reference |
|--------|--------|-----------|
| FF-A support | Standardized pKVM↔TrustZone communication replaces ad-hoc SMCs | HS-037 |
| Trusty OS in pVMs | TAs can run in pVMs, not just TrustZone; blurs ATF/pKVM boundary | HS-037 |
| Early boot VMs for KeyMint | pVMs before framework start; changes boot dependency chain | HS-037 |
| KeyMint 4.0 moduleHash | Hardware RoT tied to software module state | HS-038 |
| Device assignment promoted | IOMMU/SMMU config needed for device passthrough to pVMs | HS-037 |

---

### L2-virtualization-pkvm-expert (DIRTY → CLEAN)

| Change | Impact | Reference |
|--------|--------|-----------|
| AVF LL-NDK | Vendors can launch VMs from vendor partition; new API surface | HS-037 |
| Early boot VMs | VMs run before full framework; KeyMint-in-pVM pattern | HS-037 |
| FF-A support | Standardized secure communication for pKVM↔TrustZone | HS-037 |
| Ferrochrome | Debian-based Linux terminal in VM via AVF/crosvm | HS-037 |
| Microdroid 16K + resizable storage | 16KB page pVM support; encrypted resizable storage | HS-037 |
| Trusty in pVMs | TrustZone-style TAs inside pVMs | HS-037 |
| Device assignment promoted | Platform devices directly assigned to pVMs | HS-037 |
| Hypervisor tracing | Structured pKVM debug logging | HS-037 |

---

### L2-build-system-expert (CLEAN — A16 content added)

| Change | Impact | Reference |
|--------|--------|-----------|
| Partition image isolation | Only `PRODUCT_PACKAGES`-listed modules included; implicit inheritance gone | HS-036 |
| Module name validation enforced | Special characters in names break build | HS-036 |
| Genrule directory inputs disallowed | Must specify individual files | HS-036 |
| M4 removed from PATH | Explicit prebuilt path required | HS-036 |
| Ninja environment isolation | `ALLOW_NINJA_ENV=false` default | HS-036 |
| BOARD_HAL_STATIC_LIBRARIES deprecated | Migrate to AIDL HAL definitions | HS-036 |
| Bazel incremental migration | New plugins restricted to vendor/hardware | HS-036 |

---

### L2-bootloader-lk-expert (CLEAN — already updated in Phase 5.2)

| Change | Impact | Reference |
|--------|--------|-----------|
| GBL (Generic Bootloader) | Standardized UEFI-based bootloader replacing LK for new devices | HS-034 |
| ESP partition layout | EFI System Partition required for GBL | HS-034, HS-040 |
| UEFI firmware required | BL33 must provide UEFI services for GBL | HS-034 |

Skill was refreshed to v2.0.0 in Phase 5.2 with comprehensive GBL coverage.

---

### L2-version-migration-expert (CLEAN — A16 migration table added)

A15→A16 migration table added to skill covering all areas above. 16KB page size deadline May 31, 2026 confirmed.

---

### L2-hal-vendor-interface-expert (CLEAN — no direct A16 delta)

Cross-skill impacts from other A16 changes:
- BOARD_HAL_STATIC_LIBRARIES deprecated (from build skill)
- AIDL mandatory for all new HALs (ongoing since A14)
- CAP AIDL completion enables automotive audio HAL migration
- Unified ranging may affect ranging HAL interfaces
- KeyMint 4.0 HAL interface update

---

### L2-framework-services-expert (CLEAN — no direct A16 delta)

Cross-skill impacts:
- IMS system APIs are new SystemApi surfaces
- VirtualMachineManager API surface changes from AVF LL-NDK
- CDM removeBond is a new public API

---

### L2-init-boot-sequence-expert (CLEAN — no direct A16 delta)

Cross-skill impacts:
- Early boot VMs run before full init (from pKVM skill)
- GBL changes bootloader→kernel handoff (from bootloader skill)

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Skills with direct A16 deltas | 9 of 12 |
| Skills marked dirty pre-update | 6 |
| Hindsight notes consumed | HS-033 through HS-039 |
| Key cross-skill themes | FF-A, early boot VMs, IOCTL hardening, unified ranging, GBL |

---

*Delta summary v1.0 — 2026-04-12. Based on pre-source-drop intelligence. Pending verification against AOSP A16 source when available.*

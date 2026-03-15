# AOSP Top-Level Path Reference

> **Version:** 1.0
> **Android Version:** Android 14.0.0_r1
> **Purpose:** Canonical mapping of all AOSP root-level directories to their owning subsystem and L2 Expert Skill.
> **Source of Truth:** `skills/L1-aosp-root-router/SKILL.md` (routing decisions always defer to SKILL.md)

---

## Directory Map

> ¹ **Vendor-supplied paths** — not present in standard AOSP; provided by the SoC/OEM BSP.

| Path | Description | Owning Subsystem | L2 Expert Skill |
|------|-------------|------------------|-----------------|
| `art/` | Android Runtime — dex compiler, GC, interpreter | ART / Runtime | Future: `L2-art-runtime-expert` |
| `atf/` ¹ | ARM Trusted Firmware (TF-A) — BL1/BL2/BL31/BL32, EL3 Secure Monitor | Trusted Firmware / ATF | `L2-trusted-firmware-atf-expert` |
| `arm-trusted-firmware/` ¹ | Alternative root name for ATF tree in some BSPs | Trusted Firmware / ATF | `L2-trusted-firmware-atf-expert` |
| `bionic/` | Android C library, dynamic linker, math library | Bionic / Libc | `L2-build-system-expert` (ABI); `L2-kernel-gki-expert` (linker ABI) |
| `bootable/` | Bootloader support code, recovery image | Boot / Init | `L2-init-boot-sequence-expert` |
| `bootable/bootloader/` | Legacy AOSP bootloader hook (mostly stubs in standard AOSP) | Bootloader | `L2-bootloader-lk-expert` |
| `bootloader/` ¹ | Root-level bootloader tree — present in Qualcomm and other vendor BSPs | Bootloader | `L2-bootloader-lk-expert` |
| `bootloader/lk/` ¹ | little-kernel (LK) / ABL source — fastboot, partition, aboot, AVB | Bootloader / LK | `L2-bootloader-lk-expert` |
| `build/` | Soong, Kati, Ninja build system infrastructure | Build System | `L2-build-system-expert` |
| `build/make/` | Legacy GNU Make infrastructure, `envsetup.sh` | Build System | `L2-build-system-expert` |
| `build/soong/` | Blueprint / Soong build rules and module types | Build System | `L2-build-system-expert` |
| `cts/` | Compatibility Test Suite | Testing / Migration | `L2-version-migration-expert` |
| `dalvik/` | Legacy Dalvik VM (historical reference only, superseded by ART) | ART / Legacy | Reference only |
| `developers/` | Sample applications and developer guides | Apps / Docs | Not routed — reference only |
| `development/` | SDK tools, emulator, VNDK snapshot tools | SDK / Build | `L2-build-system-expert` |
| `device/` | Device-specific configurations, board configs, `.rc` overlays | Device / OEM | Route by content: build→build, sepolicy→security, HAL→hal, init→init |
| `external/` | Upstream open-source mirrors (LLVM, OpenSSL, etc.) | External Deps | Route to consuming subsystem's L2; do NOT edit directly |
| `frameworks/` | Android framework — Java services, native libs, AV stack | Framework | Multiple L2 — see sub-paths below |
| `frameworks/av/` | Audio, Video, Camera, MediaCodec stack | Multimedia | `L2-multimedia-audio-expert` |
| `frameworks/base/` | Core Java framework, SystemServer, system APIs | Framework | `L2-framework-services-expert` |
| `frameworks/base/api/` | Public/System API surface, API tracking files | API / Migration | `L2-framework-services-expert`, `L2-version-migration-expert` |
| `frameworks/base/services/` | System services (ActivityManagerService, PackageManagerService, etc.) | Framework | `L2-framework-services-expert` |
| `frameworks/compile/` | Shader compiler, `slang`, `rs2dex` | Build / Media | `L2-build-system-expert` |
| `frameworks/native/` | Native C++ services: SurfaceFlinger, libbinder, inputflinger | Framework / Native | `L2-framework-services-expert` |
| `frameworks/native/libs/binder/` | libbinder — core Binder IPC library | HAL / IPC | `L2-hal-vendor-interface-expert` |
| `frameworks/native/services/surfaceflinger/` | SurfaceFlinger display compositor | Multimedia | `L2-multimedia-audio-expert` |
| `hardware/` | HAL interface definitions and hardware abstraction | HAL / Vendor | `L2-hal-vendor-interface-expert` |
| `hardware/interfaces/` | AIDL and HIDL interface files (canonical HAL contracts) | HAL | `L2-hal-vendor-interface-expert` |
| `hardware/libhardware/` | Legacy `hw_module_t` HAL API | HAL / Legacy | `L2-hal-vendor-interface-expert` |
| `kernel/` | GKI kernel source, common kernel configs | Kernel | `L2-kernel-gki-expert` |
| `libcore/` | Java core libraries (OpenJDK subset for Android) | Framework | `L2-framework-services-expert` |
| `libnativehelper/` | JNI helper utilities | Framework / Native | `L2-framework-services-expert` |
| `packages/` | System apps, services packaged as APKs | Apps / Connectivity | Route by package: Connectivity→connectivity, Bluetooth→connectivity, apps→framework |
| `packages/apps/Bluetooth/` | Bluetooth system app | Connectivity | `L2-connectivity-network-expert` |
| `packages/modules/Connectivity/` | Network stack mainline module | Connectivity | `L2-connectivity-network-expert` |
| `packages/modules/Wifi/` | Wi-Fi mainline module | Connectivity | `L2-connectivity-network-expert` |
| `pdk/` | Platform Development Kit — HAL compliance testing stubs | HAL / Testing | `L2-hal-vendor-interface-expert` |
| `platform_testing/` | Platform-level integration test harness | Testing | Route to subsystem under test |
| `prebuilts/` | Pre-compiled binaries: compilers, NDK, SDK tools | Build | `L2-build-system-expert` |
| `sdk/` | Android SDK generation and tools | SDK / Build | `L2-build-system-expert` |
| `system/` | Core OS userspace — init, sepolicy, netd, hwservicemanager | Multiple | Route by sub-path (see below) |
| `system/bt/` | Bluetooth stack (Fluoride/BlueDroid) | Connectivity | `L2-connectivity-network-expert` |
| `system/core/` | Core utilities: `adb`, `logd`, `fastboot`, `ueventd` | Init / Core | `L2-init-boot-sequence-expert` |
| `system/core/init/` | `init` process source, `.rc` parser, service manager | Init | `L2-init-boot-sequence-expert` |
| `system/netd/` | Network daemon — routing, firewall, DNS | Connectivity | `L2-connectivity-network-expert` |
| `system/sepolicy/` | Platform SELinux policy — `.te`, `file_contexts`, `property_contexts` | Security | `L2-security-selinux-expert` |
| `system/vndk/` | VNDK library list and snapshot tooling | HAL / Build | `L2-hal-vendor-interface-expert` |
| `test/` | VTS, CTS infrastructure, test runners | Testing | Route to subsystem under test |
| `toolchain/` | Clang/LLVM toolchain used by AOSP | Build | `L2-build-system-expert` |
| `tools/` | Development utilities, IDE plugins, `aidl` compiler | Build / HAL | `L2-build-system-expert`; `L2-hal-vendor-interface-expert` for `aidl/` |
| `trusty/` ¹ | Trusty TEE OS — runs as ATF BL32 in TrustZone Secure EL1 | Trusted Firmware / ATF | `L2-trusted-firmware-atf-expert` |
| `vendor/` | OEM/SoC proprietary code, device BSP, vendor sepolicy | Vendor / OEM | Route by content type — always check sub-path |

---

## Critical Partition Boundaries (Treble)

```
/system   ← AOSP-controlled. Changes here require CTS/VTS validation.
/vendor   ← SoC/OEM-controlled. Cannot call private /system APIs.
/product  ← Product-specific APKs and overlays.
/odm      ← ODM (device maker) layer, sits between vendor and product.
```

**The `/system` ↔ `/vendor` ABI boundary is enforced by Treble. Never assume code can freely cross it.**

---

## Partition → Skill Mapping Quick Reference

| Partition | Primary Skill | Secondary Skill |
|-----------|--------------|-----------------|
| `/system/sepolicy/` | `L2-security-selinux-expert` | — |
| `/system/core/init/` | `L2-init-boot-sequence-expert` | — |
| `/system/core/` (other) | `L2-init-boot-sequence-expert` | `L2-build-system-expert` |
| `/system/netd/` | `L2-connectivity-network-expert` | — |
| `/frameworks/base/` | `L2-framework-services-expert` | — |
| `/frameworks/av/` | `L2-multimedia-audio-expert` | — |
| `/frameworks/native/libs/binder/` | `L2-hal-vendor-interface-expert` | — |
| `/hardware/interfaces/` | `L2-hal-vendor-interface-expert` | — |
| `/build/` | `L2-build-system-expert` | — |
| `/kernel/` | `L2-kernel-gki-expert` | — |
| `/vendor/` | Varies by content | Check sub-path |
| `/device/` | Varies by content | Check sub-path |
| `/bootloader/lk/` ¹ | `L2-bootloader-lk-expert` | `L2-init-boot-sequence-expert` (boot overlap) |
| `/atf/` ¹ | `L2-trusted-firmware-atf-expert` | — |
| `/trusty/` ¹ | `L2-trusted-firmware-atf-expert` | — |

---

*Reference document v1.1 (2026-03-15): Added LK bootloader (`bootloader/lk/`, `bootable/bootloader/`) and ATF (`atf/`, `trusty/`) path entries. Vendor-supplied paths marked ¹.*

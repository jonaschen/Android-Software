---
name: aosp-root-router
layer: L1
path_scope: /  # Root of the AOSP tree — all top-level directories
version: 1.0.0
android_version_tested: Android 14
parent_skill: null
---

## Role

You are the **AOSP Root Router** — the Layer 1 Page Directory. Every task MUST pass through this skill first. Your sole job is to:
1. Parse the user's intent.
2. Map it to one or more authoritative AOSP physical paths.
3. Hand off to the correct Layer 2 Expert Skill.
4. Enforce cross-domain guardrails to prevent hallucinations.

Do **not** answer domain questions directly. Route, then yield.

---

## Path Scope

This skill covers the entire AOSP root. All paths below are authoritative physical locations.

### Intent-to-Path Mapping Table (≥30 entries)

| Semantic Intent | Authoritative AOSP Path(s) | L2 Skill to Load |
|---|---|---|
| Build system, Android.bp, Soong, Ninja, Kati, make errors | `build/`, `build/soong/`, `build/make/` | `L2-build-system-expert` |
| Android.bp module syntax, blueprint files | `Android.bp` (any path), `*.bp` | `L2-build-system-expert` |
| Android.mk legacy makefiles | `Android.mk` (any path), `*.mk` | `L2-build-system-expert` |
| SELinux policy, `.te` files, `avc: denied`, `audit2allow` | `system/sepolicy/`, `vendor/*/sepolicy/`, `device/*/sepolicy/` | `L2-security-selinux-expert` |
| SELinux file contexts, property contexts | `system/sepolicy/private/`, `system/sepolicy/public/`, `system/sepolicy/vendor/` | `L2-security-selinux-expert` |
| HAL interface definitions, AIDL, HIDL | `hardware/interfaces/`, `vendor/*/interfaces/` | `L2-hal-vendor-interface-expert` |
| VNDK, Treble compliance, vendor partition | `vendor/`, `system/vndk/`, `development/vndk/` | `L2-hal-vendor-interface-expert` |
| Binder IPC, libbinder, binder driver | `frameworks/native/libs/binder/`, `drivers/android/` | `L2-hal-vendor-interface-expert` |
| System services, SystemServer, Java framework services | `frameworks/base/services/`, `frameworks/base/core/` | `L2-framework-services-expert` |
| @SystemApi, @TestApi, SDK API surface | `frameworks/base/api/`, `frameworks/base/core/java/android/` | `L2-framework-services-expert` |
| ANR, Watchdog, system health | `frameworks/base/services/core/java/com/android/server/` | `L2-framework-services-expert` |
| Native framework, libgui, libui, SurfaceFlinger | `frameworks/native/`, `frameworks/native/services/surfaceflinger/` | `L2-framework-services-expert` |
| init process, `.rc` files, `init.rc`, service definitions | `system/core/init/`, `*.rc` (any path) | `L2-init-boot-sequence-expert` |
| Boot sequence, early init, property service, ueventd | `system/core/`, `system/core/init/`, `system/core/property_service/` | `L2-init-boot-sequence-expert` |
| Bootloader, fastboot, recovery | `bootable/`, `bootable/recovery/` | `L2-init-boot-sequence-expert` |
| Android OS version migration, A14→A15 diff, upgrade impact | Cross-cutting (diff analysis) | `L2-version-migration-expert` |
| 16KB page size migration, alignment requirements | `bionic/`, `build/soong/`, cross-cutting | `L2-version-migration-expert` |
| API compatibility, CTS, API level changes | `cts/`, `frameworks/base/api/`, `compatibility/` | `L2-version-migration-expert` |
| Audio, AudioFlinger, AudioPolicy, sound | `frameworks/av/services/audioflinger/`, `frameworks/av/services/audiopolicy/`, `hardware/interfaces/audio/` | `L2-multimedia-audio-expert` |
| MediaCodec, MediaExtractor, media stack | `frameworks/av/media/`, `frameworks/av/services/mediacodec/` | `L2-multimedia-audio-expert` |
| Camera HAL, CameraService, camera2 | `frameworks/av/services/camera/`, `hardware/interfaces/camera/` | `L2-multimedia-audio-expert` |
| SurfaceFlinger, display, graphics HAL, HWC | `frameworks/native/services/surfaceflinger/`, `hardware/interfaces/graphics/` | `L2-multimedia-audio-expert` |
| Network stack, ConnectivityService, netd | `packages/modules/Connectivity/`, `system/netd/` | `L2-connectivity-network-expert` |
| Wi-Fi, wpa_supplicant, Wi-Fi HAL | `packages/modules/Wifi/`, `hardware/interfaces/wifi/` | `L2-connectivity-network-expert` |
| Bluetooth, BluetoothService, BT HAL | `packages/apps/Bluetooth/`, `system/bt/`, `hardware/interfaces/bluetooth/` | `L2-connectivity-network-expert` |
| GKI kernel modules, loadable modules, Kconfig | `kernel/`, `drivers/`, `common/` | `L2-kernel-gki-expert` |
| Kernel driver interface, vendor kernel module | `drivers/`, `kernel/configs/` | `L2-kernel-gki-expert` |
| little-kernel bootloader, LK source, fastboot protocol, ABL (Android Boot Loader) | `bootloader/lk/`, `bootable/bootloader/` | `L2-bootloader-lk-expert` |
| Partition table, boot image layout, fastboot commands, `aboot`, download mode | `bootloader/lk/`, `bootloader/` | `L2-bootloader-lk-expert` |
| ARM Trusted Firmware, ATF, TF-A, BL1, BL2, BL31, BL32, Secure Monitor | `atf/`, `arm-trusted-firmware/`, `trusty/` | `L2-trusted-firmware-atf-expert` |
| TrustZone, EL3 firmware, secure boot chain, OP-TEE, Trusty OS | `trusty/`, `atf/`, `vendor/*/trustzone/` | `L2-trusted-firmware-atf-expert` |
| ART runtime, dex compilation, garbage collection | `art/` | (Future: `L2-art-runtime-expert`) — use `L2-framework-services-expert` as interim |
| Bionic libc, linker, dynamic linking | `bionic/`, `bionic/linker/` | `L2-build-system-expert` (build boundary) or `L2-kernel-gki-expert` (linker/ABI) |
| Device-specific config, board config | `device/`, `device/<OEM>/<product>/` | Route to relevant L2 by content type (sepolicy → security, HAL → hal, build → build) |
| OEM/SoC vendor extensions | `vendor/<OEM>/` | Route by content type; flag for Layer 3 extension if OEM-specific skill exists |
| Prebuilts, toolchain, NDK, SDK | `prebuilts/`, `toolchain/`, `sdk/` | `L2-build-system-expert` |
| Platform testing, test harness | `platform_testing/`, `test/` | Route to relevant L2 by subsystem under test |
| External open-source libraries | `external/` | Route to relevant L2 by consuming subsystem |

---

## Trigger Conditions

This skill is **always** the first to load. There are no exceptions. Activate on any Android platform task including but not limited to:
- Build failures or Android.bp changes
- SELinux / permission denials
- HAL / AIDL / HIDL modifications
- Boot sequence or init.rc changes
- Framework service modifications
- OS version upgrade planning
- Any query referencing an AOSP path

---

## Routing Algorithm

```
1. Extract all AOSP paths or subsystem keywords from the user's task.
2. Look up each in the Intent-to-Path Mapping Table above.
3. If ONE L2 skill covers all matched paths → load that skill exclusively.
4. If MULTIPLE L2 skills are needed → load in priority order:
     Security > Build > HAL > Framework > Init > Bootloader > ATF > Migration > Media > Connectivity > Kernel
5. If NO path match → ask the user for clarification; do NOT guess.
6. Record the routing decision as a one-line log before handing off.
```

---

## Forbidden Actions

The following actions are **absolutely prohibited** by this router. Violating these creates cross-domain hallucinations.

1. **Forbidden:** Searching for Java system services in `system/core/` — Java services live in `frameworks/base/services/`.
2. **Forbidden:** Modifying SELinux policy files in `frameworks/` — all SELinux changes go to `system/sepolicy/` or `device/*/sepolicy/`.
3. **Forbidden:** Editing `init.rc` directly inside `/system/` partition — use `vendor/` overlays or device-specific `.rc` files.
4. **Forbidden:** Treating `external/` as an editable AOSP component — `external/` contains upstream open-source mirrors; changes must go upstream.
5. **Forbidden:** Assuming a HAL interface lives in `frameworks/` — AIDL/HIDL definitions are in `hardware/interfaces/` or `vendor/*/interfaces/`.
6. **Forbidden:** Writing Binder IPC code directly in `system/core/` — libbinder lives in `frameworks/native/libs/binder/`.
7. **Forbidden:** Applying kernel module changes to `system/` — GKI modules belong in `kernel/` or `drivers/`; never patch kernel from userspace paths.
8. **Forbidden:** Routing build errors to `L2-framework-services-expert` — build issues always go to `L2-build-system-expert` first.
9. **Forbidden:** Routing any `avc: denied` log to a non-security skill — SELinux denials are always routed to `L2-security-selinux-expert` exclusively.
10. **Forbidden:** Answering subsystem-specific questions at the L1 layer — L1 routes only; all answers come from the appropriate L2 expert.
11. **Forbidden:** Modifying AOSP source files in this repository — the AOSP tree is reference-only per `CLAUDE.md`.
12. **Forbidden:** Assuming `vendor/` and `system/` are the same partition — Treble enforces a strict ABI boundary between them.
13. **Forbidden:** Routing little-kernel (LK) bootloader issues to `L2-init-boot-sequence-expert` — LK runs before the kernel/init and lives in `bootloader/lk/`; route to `L2-bootloader-lk-expert`.
14. **Forbidden:** Routing ARM Trusted Firmware (ATF/TF-A) tasks to `L2-kernel-gki-expert` — ATF runs in EL3 (secure monitor) and lives in `atf/` or `trusty/`; route to `L2-trusted-firmware-atf-expert`.
15. **Forbidden:** Conflating Trusty OS with the Linux kernel — Trusty is a secure-world OS running on ATF BL32; it lives in `trusty/`, not `kernel/`.

---

## Handoff Rules

After routing, emit a handoff block in this exact format:

```
[L1 ROUTING DECISION]
Intent: <one-line summary of the task>
Path(s): <matched AOSP path(s)>
L2 Skill: <skill name>
Reason: <why this skill was chosen>
[END ROUTING → loading L2 skill now]
```

Then load the identified L2 `SKILL.md` and yield control.

---

## Tool Calls

When verification is needed before routing:
- `read_file(path)` — confirm a path exists before asserting its owner skill.
- `grep(pattern, path)` — identify subsystem by code signature (e.g., `AIDL`, `@SystemService`).
- `git_diff(path)` — during migration tasks, identify changed paths to determine which skills are affected.

---

## References

- `references/aosp_top_level_paths.md` — canonical list of all top-level AOSP directories and their owners.
- `ANDROID_SW_OWNER_DEV_PLAN.md §2` — MMU memory model design rationale.
- `ANDROID_SW_OWNER_DEV_PLAN.md §4` — full L1 router design spec.
- `memory/dirty_pages.json` — check here during version migration tasks to see if any L2 skills are stale.

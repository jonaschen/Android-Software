---
name: hal-vendor-interface-expert
layer: L2
path_scope: hardware/interfaces/, vendor/, system/vndk/, frameworks/native/libs/binder/, pdk/
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `hardware/interfaces/` | Canonical AIDL and HIDL interface definitions |
| `hardware/interfaces/<subsystem>/<version>/` | Versioned HAL contracts |
| `vendor/<OEM>/interfaces/` | OEM-specific AIDL/HIDL extensions |
| `vendor/<OEM>/` | Proprietary vendor code, BSP, vendor blobs |
| `system/vndk/` | VNDK library list, VNDK snapshots |
| `frameworks/native/libs/binder/` | libbinder — core Binder IPC library |
| `frameworks/hardware/interfaces/` | Framework-side HAL client stubs |
| `pdk/` | Platform Development Kit — HAL compliance testing |

---

## Trigger Conditions

Load this skill when the task involves:
- AIDL or HIDL interface definition, versioning, or bumping
- Adding a new HAL (Hardware Abstraction Layer)
- Binder IPC errors or interface registration failures
- VNDK library list — adding, checking, or violating VNDK boundaries
- Treble compliance — system/vendor ABI boundary questions
- `hwservicemanager` or `servicemanager` registration
- VTS (Vendor Test Suite) HAL test failures
- `stability: vintf` or `@VintfStability` annotation questions
- Vendor partition layout or `vendor.img` content

---

## Architecture Intelligence

### Treble Architecture

```
┌─────────────────────────────────────┐
│           /system partition          │
│   Android Framework (AOSP-owned)    │
│   Calls HAL via AIDL/HIDL client    │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  AIDL/HIDL Interface Def    │   │
│   │  hardware/interfaces/       │   │ ← Stable ABI boundary
│   └─────────────────────────────┘   │
└──────────────────┬──────────────────┘
                   │ Binder IPC (VNDK boundary)
┌──────────────────▼──────────────────┐
│           /vendor partition          │
│   HAL Implementation (OEM-owned)   │
│   vendor/<OEM>/hardware/            │
└─────────────────────────────────────┘
```

### AIDL vs HIDL

| Aspect | HIDL (legacy) | AIDL (current) |
|--------|--------------|----------------|
| File extension | `.hal` | `.aidl` |
| Tool | `hidl-gen` | `aidl` |
| Stability annotation | `@1.0::IFoo` versioning | `@VintfStability` |
| Backend | C++, Java | C++, Java, Rust, NDK |
| Status | Frozen (no new HALs) | All new HALs use AIDL |
| Registration | `hwservicemanager` | `servicemanager` |

### AIDL Interface Versioning

```
hardware/interfaces/<subsystem>/aidl/
└── Android.bp                     ← aidl_interface module
└── <package>/
    └── I<Name>.aidl               ← Interface definition

Android.bp key fields:
  name: "android.hardware.foo"
  srcs: ["android/hardware/foo/*.aidl"]
  stability: "vintf"               ← Required for HAL interfaces
  versions_with_info: [
    { version: "1", imports: [] },
    { version: "2", imports: [] }, ← Current frozen version
  ]
  frozen: true                     ← Locks current version

Bumping procedure:
  1. Unfreeze: set frozen: false (or remove)
  2. Make changes to .aidl files
  3. Run: m <module>-update-api
  4. Review generated API diff
  5. Freeze again: frozen: true, add new version entry
```

### VNDK (Vendor Native Development Kit)

- **VNDK libraries:** System libraries a vendor module is allowed to link against.
- **VNDK-SP:** Subset of VNDK available to same-process HALs (SP-HALs).
- **LL-NDK:** Lowest-level stable NDK available to all vendor code (`libc`, `libm`, `libdl`, `liblog`).

```
To check if a library is VNDK:
  cat build/make/target/product/vndk/current.txt | grep <libname>

To add a library to VNDK:
  Edit: build/make/target/product/vndk/<version>.txt
  (Requires careful ABI stability review)
```

### Binder IPC Fundamentals

```
Client (system partition)          Server (vendor partition)
IBinder proxy                ←→    BBinder implementation
                │                         │
                └─────── Binder ───────────┘
                          driver
                        /dev/binder          ← system ↔ system
                        /dev/vndbinder       ← vendor ↔ vendor
                        /dev/hwbinder        ← HIDL (legacy)

RULE: System code uses /dev/binder.
      Vendor code uses /dev/vndbinder.
      Cross-boundary calls go through the HAL interface only.
```

### servicemanager vs hwservicemanager

| Manager | Serves | Registration |
|---------|--------|-------------|
| `servicemanager` | AIDL services | `android.os.IServiceManager` |
| `hwservicemanager` | HIDL services (legacy) | `android.hidl.manager@1.0` |

New HALs use AIDL → register with `servicemanager`.

### Android 15 HAL / Vendor Interface Changes

| Change | Impact |
|--------|--------|
| VNDK deprecated | Former VNDK libraries treated as regular vendor/product libs; `system/vndk/` path scope reduced |
| AIDL mandatory for all new HALs | No new HIDL interfaces accepted; HIDL frozen |
| Health HAL 3.0 | Updated health interface version |
| Thermal HAL 2.0 | Updated thermal interface version |
| Domain Selection Service | New system API for IMS vs circuit-switched domain selection |
| Camera feature combination query | New platform API for querying supported camera feature combos |

---

## Forbidden Actions

1. **Forbidden:** Adding new HIDL `.hal` interfaces — all new HAL interfaces must use AIDL. HIDL is frozen.
2. **Forbidden:** Directly calling private `system/` APIs from vendor code — must go through a declared AIDL/HIDL interface.
3. **Forbidden:** Modifying a frozen AIDL interface version without running `m <module>-update-api` — frozen version files are immutable ABI contracts.
4. **Forbidden:** Linking a `vendor: true` module against a non-VNDK system library — this is a Treble violation caught by build system checks.
5. **Forbidden:** Placing HAL interface `.aidl` files outside `hardware/interfaces/` or `vendor/*/interfaces/` — framework `.aidl` files in `frameworks/` are not HAL contracts.
6. **Forbidden:** Using `/dev/binder` in vendor code or `/dev/vndbinder` in system code — the binder domain split is a hard kernel-level boundary.
7. **Forbidden:** Registering a VINTF HAL without a corresponding VINTF manifest entry — the VINTF manifest (`manifest.xml`) is the runtime declaration of HAL support.

---

## Tool Calls

```bash
# Check current AIDL interface version
cat hardware/interfaces/<subsystem>/aidl/Android.bp | grep -A5 "versions_with_info"

# List all registered HAL services on device (via adb)
adb shell dumpsys -l | grep android.hardware

# Check VNDK membership
grep <libname> build/make/target/product/vndk/current.txt

# Find VINTF manifest for a device
find device/ -name "manifest.xml" | xargs grep -l "<hal>"

# Generate API for an AIDL interface after changes
m android.hardware.<subsystem>-update-api

# Run VTS HAL test
atest VtsHal<Subsystem>V<Version>TargetTest
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| SELinux `hwservice_contexts` or `service_contexts` needed | `L2-security-selinux-expert` |
| VNDK build error in `Android.bp` | `L2-build-system-expert` |
| HAL server process init `.rc` file | `L2-init-boot-sequence-expert` |
| Framework-side HAL client in `frameworks/base/` | `L2-framework-services-expert` |

Emit `[L2 HAL → HANDOFF]` before transferring.

---

## References

- `references/aidl_hidl_treble_guide.md` — deep-dive on AIDL versioning, Treble ABI, and VNDK.
- `hardware/interfaces/README.md` — HAL interface directory conventions.
- `system/vndk/` — VNDK snapshot and library lists.
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

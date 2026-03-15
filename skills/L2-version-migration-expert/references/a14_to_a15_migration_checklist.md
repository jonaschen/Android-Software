# Android 14 → Android 15 Migration Checklist

> Reference version: Android 14.0.0_r1 → Android 15.0.0_r1

## Priority Order

Address items in this order: **Boot blockers → CTS/VTS failures → Feature regressions → Performance**

---

## 1. Build System Changes

| Item | Change | Action |
|------|--------|--------|
| Soong | `soong_config_variables` syntax updated | Audit all `soong_config_module_type` usages |
| NDK | API level 35 is A15 target | Update `minSdkVersion` / `targetSdkVersion` in manifests |
| 16KB page size | Mandatory in GKI 6.12+ | See Section 4 |
| Clang | Toolchain bumped (check exact version) | Recompile all vendor code; check for new warnings-as-errors |
| `LOCAL_*` macros | Further deprecations | Migrate remaining Android.mk modules to Android.bp |

**Skill:** `L2-build-system-expert`

---

## 2. HAL Interface Changes

| HAL | Change | Action |
|-----|--------|--------|
| Health | v3.0 AIDL mandatory (v2.0 HIDL dropped) | Migrate to `android.hardware.health@3` AIDL implementation |
| Thermal | v2.0 AIDL mandatory | Update VINTF manifest, migrate implementation |
| Audio | AudioHAL v4.0 AIDL enhancements | Review new `IModule` methods; implement or stub |
| Camera | CameraDevice v3.8 | Implement new capture request keys if supported |
| Vibrator | v2.0 AIDL additions | Implement new `IVibrator` methods |
| Sensors | MultiHAL 2.1 updates | Review `ISensors` changes |

**After each migration:** Update `vendor/etc/vintf/manifest.xml` and run `adb shell vintf --check-compat`

**Skill:** `L2-hal-vendor-interface-expert`

---

## 3. SELinux Policy Changes

| Item | Change | Action |
|------|--------|--------|
| New neverallow | Stricter `vendor_data_file` access | Audit vendor daemons writing to `/data/vendor/`; add explicit labels |
| `untrusted_app` restrictions | New restrictions on socket access | Check apps using Unix domain sockets to services |
| `ioctl` allowlists | More ioctl commands require explicit allow | Run CTS SELinux tests; add missing ioctl allows |
| Vendor policy version | Bump in `system/sepolicy/prebuilts/` | Verify vendor policy version matches system expectation |

**Skill:** `L2-security-selinux-expert`

---

## 4. 16KB Page Size Migration

> This is the highest-effort item for most devices on A15.

### What Changed
GKI 6.12 targets systems with 16KB hardware page granule. All ELF binaries must have LOAD segments aligned to 16KB (0x4000).

### Detection

```bash
# Check a specific library
readelf -lW /vendor/lib64/libfoo.so | grep LOAD
# Good: offset and alignment values divisible by 0x4000
# Bad:  alignment = 0x1000 (4KB only)

# Batch check all vendor libs on device
adb shell find /vendor /system/vendor -name "*.so" | while read f; do
    result=$(adb shell readelf -lW "$f" 2>/dev/null | grep "LOAD.*0x1000$" || true)
    [ -n "$result" ] && echo "NOT 16KB aligned: $f"
done
```

### Fix

In `Android.bp`:
```python
cc_library_shared {
    name: "libfoo",
    ldflags: ["-Wl,-z,max-page-size=16384"],
    ...
}
```

In `Android.mk` (legacy):
```makefile
LOCAL_LDFLAGS += -Wl,-z,max-page-size=16384
```

**Prebuilt blobs:** Must be rebuilt by SoC vendor with updated toolchain. File a request with your SoC vendor — this cannot be fixed by AOSP patching.

**Skill:** `L2-version-migration-expert` + `L2-build-system-expert`

---

## 5. Kernel Changes (GKI 6.6 / 6.12)

| Item | Change | Action |
|------|--------|--------|
| KMI symbol list | New exports added, some removed | Re-validate vendor modules against updated `abi_gki_aarch64.xml` |
| GKI 6.12 | New baseline for A15 | Retest all vendor modules; resign modules |
| `io_uring` | New restrictions in GKI | Audit apps using `io_uring` |
| Binder | `binder_get_node_refs_for_txn_id` removed | Check vendor modules using this |

**Skill:** `L2-kernel-gki-expert`

---

## 6. Framework API Changes

| Item | Change | Action |
|------|--------|--------|
| API level 35 | New APIs added | Update `targetSdkVersion`; test for behavior changes |
| `JobScheduler` | New constraints | Review background job scheduling |
| `BlobStoreManager` | API changes | Audit callers |
| `MediaProjection` | New confirmation requirement | Update screen recording flows |
| `PackageManager` | `queryIntentActivities` filtering tightened | Review intent resolution code |

**Skill:** `L2-framework-services-expert`

---

## 7. Boot / Init Changes

| Item | Change | Action |
|------|--------|--------|
| `init` | New `.rc` parser strictness | Run `validate_rc_syntax.py` on all vendor `.rc` files |
| `ueventd` | New device permissions model | Audit `/dev/` node permissions in `ueventd.rc` |
| Dynamic partitions | Metadata format update | Verify `super` partition layout with `lpdump` |
| First stage init | New ramdisk changes | Verify `init_boot.img` format compatibility |

**Skill:** `L2-init-boot-sequence-expert`

---

## 8. Connectivity Changes

| Item | Change | Action |
|------|--------|--------|
| Wi-Fi | WPA3-SAE mandatory for new certifications | Ensure Wi-Fi HAL supports SAE |
| Bluetooth | LE Audio updates | Update BT HAL if LE Audio is supported |
| Network stack | Mainline module updates | Accept mainline updates; do not override |
| `netd` | New firewall chain for per-app network isolation | Audit custom netd rules for conflicts |

**Skill:** `L2-connectivity-network-expert`

---

## 9. Validation Checklist

Run these in order after migration:

```bash
# 1. Build
m -j$(nproc)

# 2. Flash and boot
fastboot flashall

# 3. VINTF compatibility
adb shell vintf --check-compat

# 4. SELinux (audit log should be empty after settling)
adb logcat -b all | grep "avc: denied" | head -20

# 5. CTS core tests
cts-tradefed run cts -m CtsSELinuxHostTestCases
cts-tradefed run cts -m CtsOsTestCases
cts-tradefed run cts -m CtsBionicTestCases     # includes 16KB tests

# 6. VTS HAL tests
vts-tradefed run vts -m VtsHalHealthV3_0TargetTest
vts-tradefed run vts -m VtsHalThermalV2_0TargetTest
vts-tradefed run vts   # Full VTS suite

# 7. Update dirty_pages.json
python3 tests/routing_accuracy/../../../skills/L2-version-migration-expert/scripts/check_api_compatibility.py \
    --dirty-pages memory/dirty_pages.json
```

---

## Dirty Pages to Mark After A14→A15 Migration

Update `memory/dirty_pages.json` for each affected skill:

```json
"dirty_reason": "android_version_bump",
"affected_paths": ["<paths that changed in git diff>"]
```

Skills likely to be dirty after A14→A15:
- `L2-build-system-expert` (Soong, Clang, 16KB)
- `L2-hal-vendor-interface-expert` (Health, Thermal, Audio HAL)
- `L2-kernel-gki-expert` (KMI changes)
- `L2-version-migration-expert` (self-update — update baseline version)

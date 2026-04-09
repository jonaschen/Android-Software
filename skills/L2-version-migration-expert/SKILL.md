---
name: version-migration-expert
layer: L2
path_scope: cross-cutting (diff analysis across all paths)
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

## Path Scope

This skill does not own a single physical path. It performs **cross-cutting analysis** across any AOSP path affected by an OS version transition. Key areas of focus:

| Area | Relevant Paths |
|------|---------------|
| API compatibility | `frameworks/base/api/`, `cts/` |
| Boot image / partition format | `bootable/`, `build/make/core/` |
| 16KB page size migration | `bionic/`, `build/soong/`, all `.so` and executables |
| SELinux policy changes | `system/sepolicy/` (coordinate with security skill) |
| HAL interface version bumps | `hardware/interfaces/` (coordinate with HAL skill) |
| Build system changes | `build/soong/`, `build/make/` (coordinate with build skill) |
| Kernel ABI changes | `kernel/` (coordinate with kernel skill) |
| VNDK snapshot refresh | `system/vndk/` |

---

## Trigger Conditions

Load this skill when the task involves:
- Android OS version upgrade planning (e.g., A14 → A15)
- Impact assessment for a version bump on any subsystem
- CTS (Compatibility Test Suite) failures on a new Android version
- 16KB page size alignment failures or migration
- API level change — new, changed, or removed APIs
- `android_version_tested` field is stale in a `SKILL.md`
- `memory/dirty_pages.json` shows `dirty` skills needing refresh
- Deprecated feature removal affecting device code
- VINTF manifest compatibility check for OS upgrade

---

## Architecture Intelligence

### Migration Framework

```
Step 1: DIFF ANALYSIS
  git diff android-14.0.0_r1..android-15.0.0_r1 -- <path>
  Focus on: API changes, build system changes, policy changes

Step 2: IMPACT MAPPING
  For each changed path → identify affected L2 skill
  Build, HAL, Security, Framework, Init, Media, Connectivity, Kernel

Step 3: DIRTY PAGE MARKING
  Update memory/dirty_pages.json:
    skill → status: "dirty", dirty_reason: "android_version_bump"

Step 4: SKILL REFRESH
  For each dirty skill: update SKILL.md to reflect new version behavior
  Update android_version_tested field

Step 5: VALIDATION
  Run CTS, VTS, atest suites
  Check: routing accuracy still ≥95% with updated knowledge
```

### Android 14 → 15 Key Changes

| Area | Change | Action Required |
|------|--------|----------------|
| 16KB page size | Mandatory support in GKI 6.12+ | Realign `.so` ELF segments; recompile all vendor binaries |
| Health HAL | Health 3.0 AIDL replaces HIDL | Migrate HAL implementation |
| Thermal HAL | Thermal 2.0 AIDL mandatory | Update VINTF manifest |
| Dynamic partitions | Super partition layout changes | Update `lpdump` configuration |
| SELinux | New neverallow rules for vendor data access | Review `vendor_data_file` access |
| Java API | `android.os.StrictMode` new methods | Update callers |
| Build | `soong_config_module_type` syntax changes | Audit all `soong_config_variables` blocks |
| Kernel | GKI 6.6 → 6.12 transition | Module ABI re-validation required |

### 16KB Page Size Migration

Android 15+ is page-size agnostic: devices can run with 4KB or 16KB kernels. Google Play mandates 16KB compliance by **May 31, 2026** for all apps with native code targeting Android 15+.

**Scope of impact:**

| Component | Affected? | Key Action |
|-----------|-----------|------------|
| Shared libraries (`.so`) | Yes | ELF PT_LOAD alignment must be 0x4000 (16384) |
| Executables | Yes | Same alignment requirement |
| JNI libraries | Yes | Recompile with `-Wl,-z,max-page-size=16384` |
| Prebuilt vendor blobs | Yes | Must be rebuilt by SoC vendor (linker flag alone won't fix) |
| APKs with native code | Yes | ZIP alignment to 16KB required (AGP 8.5.1+ handles automatically) |
| Kernel modules (`.ko`) | Yes | Rebuild against 16KB GKI kernel |
| Native code with `mmap()` | Yes | Offsets must be multiples of 16KB; no hardcoded `4096` |
| Pure Java/Kotlin apps | No | No changes needed |

**Quick detection:**

```bash
# Check a single .so
readelf -lW lib.so | grep LOAD
# FAIL if Align = 0x1000 (4KB); PASS if Align = 0x4000 (16KB)

# Batch scan vendor libraries
find out/target/product/*/vendor/lib64/ -name "*.so" -exec sh -c '
  a=$(readelf -lW "$1" 2>/dev/null | grep LOAD | head -1 | awk "{print \$NF}")
  [ "$a" = "0x1000" ] && echo "FAIL: $1"
' _ {} \;

# Check APK alignment
zipalign -v -c -P 16 4 my_app.apk
```

**Quick fix (Android.bp):**

```
cc_library_shared {
    name: "my_library",
    ldflags: ["-Wl,-z,max-page-size=16384"],
}
```

**Build-time enforcement (Android 16+):**

```makefile
PRODUCT_MAX_PAGE_SIZE_SUPPORTED := 16384
PRODUCT_NO_BIONIC_PAGE_SIZE_MACRO := true
PRODUCT_CHECK_PREBUILT_MAX_PAGE_SIZE := true
```

**Key anti-patterns to audit:** hardcoded `4096`/`0x1000`, `#define PAGE_SIZE`, `mmap()` with non-page-aligned offsets, `MAP_FIXED` with 4KB addresses, buffer sizes as `N * 4096`, alignment checks `% 4096`.

> **Full audit checklist:** See `references/16kb_page_migration_guide.md` for 8 concrete audit steps covering ELF alignment, APK ZIP alignment, hardcoded constants, mmap usage, kernel config, bootloader detection, prebuilt libraries, and platform build configuration.

### VINTF Compatibility Check

```
Before upgrade: capture baseline
  adb shell cat /vendor/etc/vintf/manifest.xml > manifest_before.xml

After upgrade: compare
  diff manifest_before.xml manifest_after.xml

Key fields to verify:
  <hal format="aidl">         ← AIDL HALs and their versions
  <hal format="hidl">         ← Legacy HIDL HALs (must still be supported)
  <sepolicy><version>         ← SELinux policy version

Matrix check:
  compatibility-matrix.xml (in system image) must be satisfied by manifest.xml (in vendor image)
  Failure = device fails VTS VINTF test
```

### CTS / VTS Failure Triage

| Failure Type | First Response |
|---|---|
| CTS API test | Check `frameworks/base/api/` for removed/changed method — route to framework skill |
| VTS HAL test | HAL interface version mismatch — route to HAL skill |
| CTS SELinux test | New neverallow violation — route to security skill |
| CTS 16KB alignment | ELF alignment failure — use migration checklist above |
| CTS permission test | Permission model change — route to framework skill |
| VTS kernel test | GKI ABI mismatch — route to kernel skill |

### Dirty Page Workflow

After completing any migration task, update `memory/dirty_pages.json`:

```json
"<skill-name>": {
  "status": "dirty",
  "android_version_tested": "Android 14",
  "dirty_reason": "android_version_bump",
  "affected_paths": ["hardware/interfaces/health/", "vendor/*/hal/health/"]
}
```

Then create a hindsight note in `memory/hindsight_notes/` with the migration insight.

---

## Forbidden Actions

1. **Forbidden:** Making migration recommendations without first running `git diff` between target versions — all assertions must be grounded in actual diff output.
2. **Forbidden:** Marking a skill as `clean` without validating against the new Android version — only mark clean after the `android_version_tested` field has been updated and verified.
3. **Forbidden:** Attempting to resolve HAL version bumps in this skill — route to `L2-hal-vendor-interface-expert` for AIDL/HIDL changes.
4. **Forbidden:** Providing a migration plan without an impact map — always enumerate which L2 skills are affected before recommending changes.
5. **Forbidden:** Treating 16KB page size as a build-only change — it also affects prebuilt blobs from the SoC vendor which must be rebuilt externally.
6. **Forbidden:** Ignoring the VINTF compatibility matrix during a version upgrade — a mismatch between `manifest.xml` and `compatibility-matrix.xml` causes boot failure.

---

## Tool Calls

```bash
# Diff between Android versions for a specific path
git diff android-14.0.0_r1..android-15.0.0_r1 -- system/sepolicy/

# Check ELF page alignment
readelf -lW <path/to/lib.so> | grep LOAD

# Check API diff
diff frameworks/base/api/current.txt <new_version>/frameworks/base/api/current.txt

# Find all VINTF manifests on device
adb shell find /vendor /odm /product -name "manifest.xml"

# Run full CTS (requires test infrastructure)
cts-tradefed run cts -m <module>

# Check dirty pages
cat memory/dirty_pages.json | python3 -m json.tool | grep -A5 '"dirty"'
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| HAL interface version bump details | `L2-hal-vendor-interface-expert` |
| SELinux neverallow changes in new version | `L2-security-selinux-expert` |
| Build system syntax changes | `L2-build-system-expert` |
| API surface changes in `frameworks/base/` | `L2-framework-services-expert` |
| GKI / kernel ABI changes | `L2-kernel-gki-expert` |
| 16KB alignment in audio/media binaries | `L2-multimedia-audio-expert` |

Emit `[L2 MIGRATION → HANDOFF]` before transferring.

---

## References

- `references/a14_to_a15_migration_checklist.md` — itemized A14→A15 change log with required actions.
- `references/16kb_page_migration_guide.md` — 16KB page size audit checklist with 8 concrete audit steps.
- `memory/dirty_pages.json` — current skill refresh status by Android version.
- `cts/` — CTS test modules organized by feature area.
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

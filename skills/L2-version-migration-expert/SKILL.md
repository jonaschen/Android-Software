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

```
Why: ARM64 chips increasingly use 16KB hardware page granule.
     Android 15 requires ALL binaries to be 16KB-page-aligned.

Impact:
  - Shared libraries (.so): ELF segment alignment must be 16KB (0x4000)
  - Executables: Same
  - JNI libraries: Must be recompiled with updated linker flags
  - Prebuilt blobs: Must be rebuilt by SoC vendor

Detection:
  python3 tools/extract-utils/check_elf_alignment.py <lib.so>
  adb shell cat /proc/cpuinfo | grep "CPU architecture"

Fix (Android.bp):
  cc_library_shared {
      ...
      ldflags: ["-Wl,-z,max-page-size=16384"],
  }

Verification:
  readelf -lW <lib.so> | grep LOAD   ← Check all LOAD segments are 0x4000 aligned
```

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
- `memory/dirty_pages.json` — current skill refresh status by Android version.
- `cts/` — CTS test modules organized by feature area.
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

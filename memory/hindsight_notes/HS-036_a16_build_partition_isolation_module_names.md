---
id: HS-036
title: "Build system: partition image isolation, module name validation, M4 removal"
skill: L2-build-system-expert
date: 2026-04-08
source: research-session
---

## Insight

Additional build system changes beyond HS-030 (genrule sandboxing, Python 2
removal) that affect BSP developers:

1. **Partition image isolation**: Partition builds now only include modules
   explicitly listed in `PRODUCT_PACKAGES`. Previous builds could inherit
   artifacts from prior builds. Use `BUILD_BROKEN_INCORRECT_PARTITION_IMAGES`
   to temporarily revert.

2. **Module name validation**: Module names now restricted to `a-z`, `A-Z`,
   `0-9`, and `_.+-=,@~`. Modules with `/` in names must move directories to
   `LOCAL_MODULE_RELATIVE_PATH`.

3. **Genrule directory inputs disallowed**: Genrules must specify individual
   files, not directories. Use `BUILD_BROKEN_INPUT_DIR_MODULES` to allowlist.

4. **M4 removed from PATH**: Must use the prebuilt version and set the `M4`
   environment variable explicitly in rules.

5. **Ninja environment isolation**: `ALLOW_NINJA_ENV=false` becoming default.
   Environment variables must be passed explicitly in command lines.

6. **BOARD_HAL_STATIC_LIBRARIES deprecated**: Use HIDL/Stable AIDL HAL
   definitions instead.

7. **Bazel migration status**: Incremental — each Soong plugin requires manual
   migration. Bazel is being used alongside Soong, not replacing it yet.
   Restriction: new plugins only allowed in vendor/hardware dirs.

## Lesson

BSP engineers must audit their `PRODUCT_PACKAGES` for completeness — implicit
partition inheritance is gone. Module names with special characters will break.
M4-dependent build rules need explicit path setup.

## Cross-Skill Impact

- **L2-hal-vendor-interface-expert**: BOARD_HAL_STATIC_LIBRARIES removal affects
  legacy HAL builds.
- **L2-version-migration-expert**: Partition isolation and module name rules are
  A16 migration items.

---
name: build-system-expert
layer: L2
path_scope: build/, Android.bp, Android.mk, *.bp, *.mk, prebuilts/, toolchain/, bionic/
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

## Path Scope

Primary paths owned by this skill:

| Path | Responsibility |
|------|---------------|
| `build/` | Soong, Kati, Ninja infrastructure |
| `build/soong/` | Blueprint parser, module type definitions, `Android.bp` rules |
| `build/make/` | GNU Make layer, `envsetup.sh`, `lunch` target |
| `build/make/core/` | Core build logic: `main.mk`, `base_rules.mk`, partition image rules |
| `Android.bp` (any path) | Per-module build definitions |
| `Android.mk` (any path) | Legacy make-based build definitions |
| `prebuilts/` | Pre-compiled compilers, NDK, SDK tools |
| `toolchain/` | Clang/LLVM toolchain used by AOSP |
| `development/` | VNDK snapshot tools, SDK generation |
| `bionic/` | libc, linker ABI — consulted for ABI compatibility questions |

---

## Trigger Conditions

Load this skill when the task involves:
- Build failures: `ninja`, `soong`, `kati` errors
- `Android.bp` module definition or syntax questions
- `Android.mk` to `Android.bp` migration
- Adding new modules: `cc_library`, `java_library`, `prebuilt_*`, `filegroup`, etc.
- Partition image construction (`system.img`, `vendor.img`, `product.img`)
- VNDK snapshot generation
- NDK or SDK toolchain issues
- Dependency errors: "depends on disabled module", "missing dependency"
- `m`, `mm`, `mmm`, `mma` command failures

---

## Architecture Intelligence

### Build System Layers

```
User runs: m <target>
           │
           ▼
    envsetup.sh / lunch        ← Selects product/variant combo
           │
           ▼
    Soong (build/soong/)       ← Parses all Android.bp files
    Blueprint → Ninja rules
           │
           ▼
    Kati (build/make/)         ← Parses Android.mk files (legacy)
    GNU Make → Ninja rules
           │
           ▼
    Ninja                      ← Executes the build graph
```

### Key Soong Module Types

| Module Type | Purpose | Example |
|-------------|---------|---------|
| `cc_library_shared` | Shared `.so` library | `libfoo.so` |
| `cc_library_static` | Static `.a` library | `libfoo.a` |
| `cc_library_headers` | Header-only library | Include path export |
| `cc_binary` | Native executable | `my_daemon` |
| `cc_prebuilt_library_shared` | Prebuilt `.so` | Vendor blobs |
| `java_library` | Java `.jar` for platform | Framework lib |
| `android_app` | APK | System app |
| `filegroup` | Group files for reuse | Shared srcs |
| `soong_config_module_type` | Conditional modules | OEM switches |
| `phony` | Alias target | `m mygroup` |

### Visibility and Dependency Rules

- `visibility: ["//visibility:public"]` — accessible from any module.
- `visibility: ["//frameworks/base:__subpackages__"]` — restricted to a subtree.
- `apex_available` — required for modules included in a Mainline APEX.
- `vendor: true` — module lives on the vendor partition; cannot link against non-VNDK system libs.
- `product_specific: true` — module lives on the product partition.

### Common Build Error Patterns

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `depends on disabled module` | A dependency has `enabled: false` or wrong variant | Check `disabled` flag, `product_variables` |
| `ninja: error: unknown target` | Module name typo or missing `Android.bp` | Verify `name:` field |
| `VNDK violation` | Vendor module links non-VNDK system lib | Use VNDK equivalent or move to vendor |
| `duplicate module` | Same `name:` in two `Android.bp` files | Rename one module |
| `missing required module` | `required:` entry not built for this config | Add module to product makefile |
| `out of date .mk` | `LOCAL_` variable used in `.bp` context | Migrate to Soong syntax |

### Partition Image Rules

- `system.img` ← modules without `vendor:`, `product_specific:`, `device_specific:` flags.
- `vendor.img` ← modules with `vendor: true` or `soc_specific: true`.
- `product.img` ← modules with `product_specific: true`.
- `odm.img` ← modules with `device_specific: true`.

### Android 15 Build System Changes

| Change | Impact |
|--------|--------|
| Sandboxed genrules | Genrules can only access listed `srcs`; builds relying on implicit inputs break |
| Python 2 fully removed | All build scripts must use Python 3 |
| Sysprop library reference change | Direct `cc_module` deps on `sysprop_library` disallowed; use generated `libfoo` |
| `depfile` property removed from gensrcs | Use explicit deps or `tool_files` instead |
| Directory inputs banned in genrules | Must specify individual files |
| Module name character validation | Only `a-z A-Z 0-9 _.+-=,@~` allowed |
| System property duplication error | Multiple assignments for same property per partition now fail |
| Dexpreopt uses-library checks | Java modules must declare `uses_libs` / `optional_uses_libs` |
| Soong plugin validation | New plugins restricted to vendor/hardware directories |

---

## Forbidden Actions

1. **Forbidden:** Routing VNDK boundary violations to this skill alone — VNDK compliance also requires `L2-hal-vendor-interface-expert` for the interface side.
2. **Forbidden:** Editing `Android.bp` files inside `system/sepolicy/` for SELinux reasons — route to `L2-security-selinux-expert`.
3. **Forbidden:** Modifying prebuilt blobs in `vendor/` without understanding Treble implications — consult `L2-hal-vendor-interface-expert`.
4. **Forbidden:** Using `LOCAL_MODULE_TAGS := eng` in new code — this tag is deprecated; use `product_packages` in device makefiles.
5. **Forbidden:** Adding `//visibility:public` to a module inside `frameworks/base/` without API review — escalate to `L2-framework-services-expert`.
6. **Forbidden:** Modifying `build/make/core/main.mk` without understanding full build graph implications — this file controls all partition image generation.
7. **Forbidden:** Treating `Android.mk` and `Android.bp` as interchangeable — `.mk` is processed by Kati, `.bp` by Soong; they have different variable scopes and no shared state.

---

## Tool Calls

```bash
# Find all Android.bp files under a path
find <path> -name "Android.bp"

# Check which modules are defined in a directory
grep -r "^cc_\|^java_\|^android_app\|^filegroup" <path>/Android.bp

# Find what depends on a module
grep -r '"<module_name>"' $(find . -name "Android.bp") | grep -v "^Binary"

# Check VNDK status of a library
grep -r "<lib_name>" build/make/target/product/vndk/

# Dump the build graph for a target (run from AOSP root)
# m <target> SOONG_EXPLAIN=true
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| VNDK list or partition boundary question | `L2-hal-vendor-interface-expert` |
| SELinux label needed for new module install path | `L2-security-selinux-expert` |
| New system service `.rc` file required | `L2-init-boot-sequence-expert` |
| API surface impact of a new java_library | `L2-framework-services-expert` |
| Build error caused by kernel module config | `L2-kernel-gki-expert` |
| `rust_binary` or `rust_library` build failure in AVF/crosvm | `L2-virtualization-pkvm-expert` |

Emit `[L2 BUILD → HANDOFF]` before transferring.

---

## References

- `references/soong_module_types.md` — complete Soong module type reference with field descriptions.
- `build/soong/README.md` — official Soong documentation.
- `build/make/core/main.mk` — master build orchestration (read-only reference).
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

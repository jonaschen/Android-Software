# HS-031: Android 15 Build, HAL, and Kernel Platform Changes

> **Date:** 2026-04-08
> **Skills:** L2-build-system-expert, L2-hal-vendor-interface-expert, L2-kernel-gki-expert
> **Source:** Phase 4.5 A15 validation pass

## Insight

Android 15 introduces three interconnected platform changes that affect build, HAL, and kernel skills simultaneously:

### Build System
- **Sandboxed genrules** are the most impactful change. Genrules can now only access their listed `srcs`. Any genrule relying on implicit file access will silently fail or produce incorrect output. This is a frequent source of post-upgrade build breaks.
- **Python 2 is fully removed.** Any remaining `python_binary_host` or `python_test_host` modules using `version: { py2: ... }` will fail.
- **Sysprop library references** changed: direct cc_module deps on `sysprop_library` are no longer supported; use the generated `libfoo` module instead.

### HAL / Vendor Interface
- **VNDK is deprecated.** Former VNDK libraries are now treated as regular vendor/product libraries. The `system/vndk/` path is reduced in relevance but still exists for backwards compatibility with older vendor images.
- **AIDL is mandatory for all new HALs.** No new HIDL interfaces are accepted. Existing HIDL interfaces remain frozen but functional.
- **Health HAL bumped to 3.0, Thermal HAL to 2.0.** OEMs must validate against new interface versions.

### Kernel / GKI
- **GKI android15-6.6 (Linux 6.6 LTS)** is the sole kernel baseline. There is no android15-6.1; one GKI per release starting A15.
- **KMI break from A14:** android14-6.1 modules are not compatible with android15-6.6. Full vendor module rebuild required.
- **16KB page size GKI builds** are available on-demand. Not default, but OEMs preparing for A16 mandatory compliance should test now.

## Cross-Skill Impact

When debugging a post-A15-upgrade build failure:
1. Check genrule sandboxing first (build-system-expert)
2. Check VNDK deprecation link errors (hal-vendor-interface-expert)
3. Check KMI symbol compatibility if kernel modules fail to load (kernel-gki-expert)

## AOSP Paths

- `build/soong/` — genrule sandboxing enforcement
- `system/vndk/` — deprecated, reduced scope
- `hardware/interfaces/` — AIDL-only for new HALs
- `kernel/` — android15-6.6 baseline

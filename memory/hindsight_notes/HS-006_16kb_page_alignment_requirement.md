# HS-006: 16KB Page Size Requires ELF Alignment Changes

**Category:** Version Migration + Build
**Skills involved:** L2-version-migration-expert, L2-build-system-expert
**Android versions:** Android 15+

## Insight

Android 15 introduces support for 16KB page size. Binaries and shared libraries must be built with 16KB-aligned ELF segments or they will fail to load on 16KB-page devices:

```
dlopen failed: "/vendor/lib64/libfoo.so" has load address X not aligned to 16384
```

Required changes:
1. **Linker flag:** Add `-Wl,-z,max-page-size=16384` to all `cc_library_shared` and `cc_binary` targets in `Android.bp`
2. **Prebuilts:** Any prebuilt `.so` must be recompiled — a wrapper flag does not fix prebuilt alignment
3. **JNI libraries:** Must also be aligned; `PackageManager` will reject APKs with misaligned JNI libs

**Detection tool:** `aarch64-linux-android-readelf -l <lib.so> | grep LOAD` — check `Align` field shows `0x4000` (16384).

## Why This Matters

16KB page size is mandatory for GKI compliance on future SoCs. Non-aligned binaries silently work on 4KB-page devices but crash on 16KB-page devices with confusing `dlopen` errors.

## Trigger

Add to the A14→A15 migration checklist. Route to `L2-version-migration-expert` for impact assessment, then `L2-build-system-expert` for the Android.bp fixes.

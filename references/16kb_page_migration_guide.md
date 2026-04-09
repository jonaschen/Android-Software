# 16KB Page Size Migration Guide

> **Version:** 1.0.0
> **Date:** 2026-04-10
> **Applies to:** Android 15+ (page-size agnostic); mandatory for Google Play by May 31, 2026
> **Audience:** Android SW Owners, BSP engineers, platform integration teams

---

## Overview

Android 15 introduces **page-size agnostic** support, allowing devices to run with either 4KB or 16KB kernel page sizes. ARM64 CPUs with 16KB TLB granules (ARMv8.1+) achieve measurable performance gains from larger pages:

| Metric | Improvement |
|--------|-------------|
| App launch time (average) | ~3.2% faster |
| Camera cold start | ~6.6% faster |
| System boot | ~8% faster (~950ms) |
| Power draw during app launch | ~4.6% reduction |
| TLB pressure (64MB mapping) | 4x fewer page table entries |
| Trade-off: memory overhead | ~9% increase |

**Deadline:** Google Play requires 16KB page-size compliance for all apps with native code targeting Android 15+ by **May 31, 2026**. Non-compliant apps may be blocked from publishing updates.

---

## Who Is Affected

| Component | Affected? | Action |
|-----------|-----------|--------|
| Pure Java/Kotlin apps | No | No changes needed |
| Apps with JNI / NDK native code | **Yes** | Recompile with 16KB alignment |
| Prebuilt vendor `.so` libraries | **Yes** | Must be rebuilt by SoC vendor |
| HAL implementations (native) | **Yes** | Recompile all HAL binaries |
| Kernel modules (`.ko`) | **Yes** | Rebuild against 16KB GKI kernel |
| Bootloader | **Yes** | Must detect page size from kernel header |
| Init scripts (`.rc`) | No | No changes (unless hardcoding page sizes) |

---

## Audit Checklist

Use this checklist for a systematic 16KB migration audit. Each section includes concrete detection commands and fix patterns.

### Audit 1: ELF Alignment

**What to check:** All shared libraries (`.so`) and executables must have PT_LOAD segments aligned to 16KB (0x4000 = 16384).

**Detection:**

```bash
# Check a single library
llvm-objdump -p lib.so | grep -A1 LOAD
# Expected: align 2**14 (16384) for ALL LOAD segments

# Alternative using readelf
readelf -lW lib.so | grep LOAD
# Expected: Align column shows 0x4000 (not 0x1000)

# Batch check all .so files in a directory
find /path/to/out/target/product/<device>/vendor/lib64/ -name "*.so" -exec sh -c '
  align=$(readelf -lW "$1" 2>/dev/null | grep LOAD | head -1 | awk "{print \$NF}")
  if [ "$align" = "0x1000" ]; then echo "FAIL: $1 (4KB aligned)"; fi
' _ {} \;
```

**Fix (Android.bp):**

```
cc_library_shared {
    name: "my_library",
    srcs: ["*.cpp"],
    ldflags: ["-Wl,-z,max-page-size=16384"],
}
```

**Fix (CMake / NDK):**

```cmake
target_link_options(${CMAKE_PROJECT_NAME} PRIVATE "-Wl,-z,max-page-size=16384")
```

**Fix (ndk-build / Application.mk):**

```makefile
APP_SUPPORT_FLEXIBLE_PAGE_SIZES := true
```

**Fix (Gradle + CMake, NDK r27):**

```groovy
android {
    defaultConfig {
        externalNativeBuild {
            cmake {
                arguments "-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON"
            }
        }
    }
}
```

> **NDK r28+:** Compiles with 16KB alignment by default. No extra flags needed.

**Verification:**

```bash
readelf -lW lib.so | grep LOAD
# ALL LOAD segments must show Align = 0x4000
```

---

### Audit 2: APK ZIP Alignment

**What to check:** Uncompressed `.so` files inside APKs must be 16KB ZIP-aligned.

**Detection:**

```bash
# Check APK alignment
zipalign -v -c -P 16 4 my_app.apk

# Check AAB bundle alignment
bundletool dump config --bundle=my.aab
# Expected: PAGE_ALIGNMENT_16K
```

**Fix:** Use AGP 8.5.1+ which handles 16KB ZIP alignment automatically. For older AGP:

| AGP Version | Action |
|-------------|--------|
| 8.5.1+ | Automatic 16KB ZIP alignment (recommended) |
| 8.3-8.5 | Aligned locally, but bundletool may not zipalign APKs from bundles |
| < 8.3 | Use `useLegacyPackaging = true` (compressed `.so`, fallback) |

---

### Audit 3: Hardcoded Page Size Constants

**What to check:** Native code must NOT hardcode `4096` or `PAGE_SIZE` as a compile-time constant. The page size must be determined at runtime.

**Detection:**

```bash
# Search for hardcoded 4096 page size assumptions
grep -rn '\b4096\b' vendor/ --include="*.c" --include="*.cpp" --include="*.h"
grep -rn '0x1000\b' vendor/ --include="*.c" --include="*.cpp" --include="*.h"
grep -rn 'PAGE_SIZE' vendor/ --include="*.c" --include="*.cpp" --include="*.h"
grep -rn '#define PAGE_SIZE' vendor/ --include="*.h"

# Search for page-aligned allocation patterns
grep -rn '% 4096\|/ 4096\|\* 4096' vendor/ --include="*.c" --include="*.cpp"
```

**Anti-patterns to fix:**

```c
// BAD: Hardcoded page size
#define PAGE_SIZE 4096
#define MY_BUF_SIZE (N * 4096)
if (offset % 4096 != 0) { ... }

// GOOD: Runtime page size detection
#include <unistd.h>
long page_size = sysconf(_SC_PAGESIZE);  // or getpagesize()
#define MY_BUF_SIZE(n) ((n) * sysconf(_SC_PAGESIZE))
if (offset % sysconf(_SC_PAGESIZE) != 0) { ... }
```

**Java equivalent:**

```java
import android.system.Os;
import android.system.OsConstants;
long pageSize = Os.sysconf(OsConstants._SC_PAGE_SIZE);
```

---

### Audit 4: mmap() Usage

**What to check:** All `mmap()` calls must use page-aligned offsets and addresses. On a 16KB kernel, the `offset` parameter must be a multiple of 16384.

**Detection:**

```bash
# Find all mmap calls in native code
grep -rn '\bmmap\b\|MAP_FIXED' vendor/ --include="*.c" --include="*.cpp"

# Runtime detection using strace on device
adb shell strace -e mmap -p <pid> 2>&1 | grep -v "0x4000"
```

**Anti-patterns to fix:**

```c
// BAD: Offset not 16KB-aligned (works on 4KB, fails on 16KB)
mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 4096);

// BAD: MAP_FIXED with 4KB-aligned address that isn't 16KB-aligned
mmap((void*)0x7000, size, PROT_READ|PROT_WRITE, MAP_FIXED, fd, 0);

// GOOD: Page-aligned offset using runtime page size
long page_size = sysconf(_SC_PAGESIZE);
off_t aligned_offset = (offset / page_size) * page_size;
size_t padding = offset - aligned_offset;
void *base = mmap(NULL, size + padding, PROT_READ, MAP_PRIVATE, fd, aligned_offset);
void *actual = (char*)base + padding;
```

---

### Audit 5: Kernel Configuration

**What to check:** The kernel must be configured for 16KB page support.

**Kernel config options:**

```
# 16KB pages
CONFIG_ARM64_16K_PAGES=y

# 4KB pages (legacy default)
CONFIG_ARM64_4K_PAGES=y
```

**Kleaf build flag:**

```bash
--page_size=16k
```

**Verification on device:**

```bash
adb shell getconf PAGE_SIZE
# Expected: 16384

adb shell zcat /proc/config.gz | grep CONFIG_ARM64_16K_PAGES
# Expected: CONFIG_ARM64_16K_PAGES=y

# Kernel header encodes page size at byte offset 25:
# 0=unspecified, 1=4KB, 2=16KB, 3=64KB
```

**Minimum kernel version:** `android14-6.1` or later supports both 4KB and 16KB configurations. GKI `android16-6.12` provides 16KB builds on-demand.

---

### Audit 6: Bootloader Page Size Detection

**What to check:** The bootloader must read the page size from the kernel image header to select the correct DTB/kernel configuration.

**Key requirements:**

| Requirement | Detail |
|-------------|--------|
| Kernel header parsing | Read page size at byte offset 25 in the kernel image |
| DTB selection | Select DTB matching the kernel's page size |
| Property signaling | Set `ro.boot.hardware.cpu.pagesize` for userspace |
| Dual OTA support | Support both 4K + 16K boot images for page-size toggling |

**Verification:**

```bash
adb shell getprop ro.boot.hardware.cpu.pagesize
# Expected: 16384 (on 16KB device)
```

---

### Audit 7: Prebuilt Vendor Libraries

**What to check:** All prebuilt `.so` files from SoC vendors, third-party SDKs, ad networks, and game engines must be 16KB-aligned. The linker flag only fixes libraries you build from source.

**Detection:**

```bash
# Scan all prebuilt .so files
find vendor/ -name "*.so" -exec sh -c '
  align=$(readelf -lW "$1" 2>/dev/null | grep LOAD | head -1 | awk "{print \$NF}")
  if [ "$align" = "0x1000" ]; then echo "NEEDS REBUILD: $1"; fi
' _ {} \;
```

**Android 16 build-time enforcement:**

```makefile
# In device product config
PRODUCT_CHECK_PREBUILT_MAX_PAGE_SIZE := true
```

This causes the build to fail if any prebuilt has 4KB alignment.

**Escape hatch (temporary):**

```
// Android.bp — suppress alignment check for a single module
cc_prebuilt_library_shared {
    name: "legacy_vendor_lib",
    ignore_max_page_size: true,  // Temporary! Must fix before shipping
}
```

---

### Audit 8: Platform Build Configuration

**What to check:** Product-level build variables must enable 16KB support.

**Required build variables:**

```makefile
# In device/<OEM>/<product>/device.mk or BoardConfig.mk

# Ensures platform ELF files are built with 16KB alignment
PRODUCT_MAX_PAGE_SIZE_SUPPORTED := 16384

# Removes compile-time PAGE_SIZE define; forces runtime detection
PRODUCT_NO_BIONIC_PAGE_SIZE_MACRO := true

# (Android 16+) Verifies all prebuilts are 16KB aligned at build time
PRODUCT_CHECK_PREBUILT_MAX_PAGE_SIZE := true

# Enables 16KB toggle in Developer Options (optional, for testing)
PRODUCT_16K_DEVELOPER_OPTION := true
```

**Verification:**

```bash
get_build_var TARGET_MAX_PAGE_SIZE_SUPPORTED   # Expected: 16384
get_build_var TARGET_NO_BIONIC_PAGE_SIZE_MACRO # Expected: true
```

---

## Testing Strategy

### Emulator Testing

16KB emulator images are available in Android Studio SDK Manager:
- "Google APIs Experimental 16KB Page Size ARM 64 v8a System Image"
- "Google APIs Experimental 16KB Page Size Intel x86_64 Atom System Image"

Available under Android 15+ in SDK Manager > SDK Platforms > Show Package Details.

### Physical Device Testing (Developer Option)

Supported devices: Pixel 8/8 Pro/8a (A15 QPR1+), Pixel 9 series (A15 QPR2+), Pixel 9a (A16+).

1. Settings > System > Developer Options > "Boot with 16KB page size"
2. Device reboots with 16KB kernel
3. Verify: `adb shell getconf PAGE_SIZE` returns `16384`

### Cuttlefish (CI)

ARM64 Cuttlefish supports native 16KB kernels for automated CI testing.

### 16KB Backcompat Mode (Fallback)

When a 4KB-aligned app runs on a 16KB device, Android activates **backcompat mode**:
- The bionic linker pads 4KB-aligned ELF segments to 16KB boundaries
- A warning dialog appears: "Running in 16 KB backcompat mode"
- Performance degrades due to the padding overhead

**Control backcompat via adb:**

```bash
# Force backcompat on (all apps)
adb shell setprop bionic.linker.16kb.app_compat.enabled true
adb shell setprop pm.16kb.app_compat.disabled false

# Force backcompat off (all apps — crashes non-compliant apps)
adb shell setprop bionic.linker.16kb.app_compat.enabled false
adb shell setprop pm.16kb.app_compat.disabled true

# Force fatal on incompatible (Android 17+)
adb shell setprop bionic.linker.16kb.app_compat.enabled fatal
```

**Per-app manifest control:**

```xml
<application android:pageSizeCompat="enabled|disabled">
```

---

## Timeline

| Date | Milestone |
|------|-----------|
| Aug 2024 | Google announces 16KB page size support in Android 15 |
| Android 15 (2024) | AOSP becomes page-size agnostic; 16KB emulator images available |
| Android 15 QPR1 | Developer Option toggle on Pixel 8 series |
| Nov 1, 2025 | Google Play deadline: new apps/updates targeting A15+ must support 16KB |
| May 31, 2026 | Extended deadline (available via Play Console extension request) |
| Android 16 | `PRODUCT_CHECK_PREBUILT_MAX_PAGE_SIZE` for build-time verification |
| Android 17+ | `bionic.linker.16kb.app_compat.enabled fatal` mode available |

---

## NDK Version Matrix

| NDK Version | 16KB Behavior |
|-------------|---------------|
| r28+ | 16KB aligned by default; no changes needed |
| r27 | Add `-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON` to CMake args |
| r26 and below | Add `-Wl,-z,max-page-size=16384` manually to linker flags |
| r22 and below | Also add `-Wl,-z,common-page-size=16384`; strongly recommend upgrading |

---

## Cross-Skill Impact

| Skill | 16KB Relevance |
|-------|---------------|
| `L2-build-system-expert` | `PRODUCT_MAX_PAGE_SIZE_SUPPORTED`, linker flags in `Android.bp` |
| `L2-kernel-gki-expert` | `CONFIG_ARM64_16K_PAGES`, GKI 16KB builds, Kleaf `--page_size=16k` |
| `L2-hal-vendor-interface-expert` | HAL native libraries must be 16KB-aligned |
| `L2-bootloader-lk-expert` | Kernel header page size detection, dual OTA images |
| `L2-init-boot-sequence-expert` | `ro.boot.hardware.cpu.pagesize` property |
| `L2-multimedia-audio-expert` | Audio/media native libraries and codecs must be realigned |
| `L2-version-migration-expert` | Orchestrates the overall migration audit |
| `L2-security-selinux-expert` | No direct impact (SELinux is page-size independent) |

---

## Key Anti-Patterns Summary

| Anti-Pattern | Audit Search | Fix |
|-------------|-------------|-----|
| Hardcoded `4096` / `0x1000` | `grep -rn '\b4096\b\|0x1000\b'` | Replace with `sysconf(_SC_PAGESIZE)` |
| `#define PAGE_SIZE 4096` | `grep -rn '#define PAGE_SIZE'` | Use `getpagesize()` or `sysconf()` |
| `mmap()` with non-page-aligned offset | `grep -rn '\bmmap\b'` | Align offset to `sysconf(_SC_PAGESIZE)` |
| `MAP_FIXED` with 4KB-aligned address | `grep -rn 'MAP_FIXED'` | Ensure address is 16KB-aligned |
| Buffer size as `N * 4096` | `grep -rn '\* 4096'` | Use `N * sysconf(_SC_PAGESIZE)` |
| Alignment check `% 4096` | `grep -rn '% 4096'` | Use `% sysconf(_SC_PAGESIZE)` |
| 4KB-aligned prebuilt `.so` | `readelf -lW *.so \| grep LOAD` | Request rebuild from vendor |

---

## References

- `memory/hindsight_notes/HS-006_16kb_page_alignment_requirement.md` -- ELF alignment details
- `memory/hindsight_notes/HS-028_16kb_page_mandatory_may_2026.md` -- Google Play deadline
- `references/a14_to_a15_delta_summary.md` -- A14-to-A15 per-skill impact
- [Support 16 KB page sizes (developer.android.com)](https://developer.android.com/guide/practices/page-sizes)
- [16 KB page size (source.android.com)](https://source.android.com/docs/core/architecture/16kb-page-size/16kb)
- [Optimize for 16 KB page size (source.android.com)](https://source.android.com/docs/core/architecture/16kb-page-size/optimize)

---

*16KB Page Migration Guide v1.0.0 -- Created 2026-04-10 for Phase 5.3 deliverable.*

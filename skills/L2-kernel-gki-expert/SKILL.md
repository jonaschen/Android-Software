---
name: kernel-gki-expert
layer: L2
path_scope: kernel/, drivers/, common/
version: 1.1.0
android_version_tested: Android 16 (GKI 6.12)
parent_skill: aosp-root-router
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `kernel/` | GKI kernel source tree |
| `kernel/configs/` | Kernel configuration fragments (`.config`) |
| `common/` | Android common kernel (GKI branch) |
| `drivers/` | Out-of-tree vendor kernel modules |
| `device/<OEM>/` | Board-level kernel configs and defconfigs |
| `prebuilts/misc/linux-x86/dtc/` | Device Tree Compiler for DT overlays |

---

## Trigger Conditions

Load this skill when the task involves:
- Adding a new GKI loadable kernel module (`.ko`)
- Kernel module signature verification failures
- GKI ABI symbol allowlist — adding or removing exported symbols
- `Kconfig` options — enabling/disabling kernel features
- `defconfig` changes for device targets
- Device Tree Source (`.dts`, `.dtsi`, `.dtbo`) modifications
- Kernel panic or oops analysis
- `insmod` / `modprobe` failures
- Driver interface with userspace (`/dev/*`, `sysfs`, `ioctl`)
- Kernel version upgrade (e.g., GKI 6.1 → 6.6 → 6.12)
- `vmlinux.symvers` ABI mismatch errors
- `modinfo` — module compatibility checks

---

## Architecture Intelligence

### GKI Architecture

```
┌─────────────────────────────────────────────────────────┐
│  GKI Kernel (android-mainline / android14-6.1 branch)   │
│                                                          │
│  vmlinux — fixed, signed by Google                      │
│  GKI modules — signed by Google (e.g., ext4.ko)        │
│                                                          │
│  Stable Symbol List (android/abi_gki_aarch64.xml)       │
│    → Only symbols in this list may be used by           │
│      vendor modules                                      │
└──────────────────────┬──────────────────────────────────┘
                       │ Module ABI (KMI — Kernel Module Interface)
┌──────────────────────▼──────────────────────────────────┐
│  Vendor Modules (OEM / SoC)                              │
│                                                          │
│  my_sensor.ko, my_gpu.ko, my_codec.ko                   │
│    → Built against GKI headers only                     │
│    → May only use KMI-stable symbols                    │
│    → Signed by OEM / verified by Android Verified Boot  │
└─────────────────────────────────────────────────────────┘
```

### KMI (Kernel Module Interface)

The KMI is the set of symbols exported by `vmlinux` that vendor modules may use. It is frozen per GKI branch.

```
KMI symbol list location:
  android/abi_gki_aarch64.xml         ← authoritative list
  android/abi_gki_aarch64_<fragment>  ← per-subsystem fragments

Adding a symbol:
  1. Confirm the symbol is needed and stable (not an internal refactor target)
  2. Add to the appropriate fragment file
  3. Rebuild vmlinux and run: python3 tools/bazel/kernel_abi.py
  4. Submit to the android-mainline kernel tree (NOT vendor tree)

Checking ABI compliance:
  m kernel_abi   (from AOSP root, if integrated)
  or: scripts/abi-check.sh vmlinux vendor_module.ko
```

### Writing a GKI Vendor Module

```c
// my_driver.c
#include <linux/module.h>
#include <linux/init.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("OEM");
MODULE_DESCRIPTION("My GKI vendor module");
MODULE_VERSION("1.0");

// Only use KMI-stable symbols — verified against abi_gki_aarch64.xml
static int __init my_driver_init(void) { ... }
static void __exit my_driver_exit(void) { ... }

module_init(my_driver_init);
module_exit(my_driver_exit);
```

**Android.bp for a kernel module:**
```
// Note: Kernel modules use Android.bp only for integration packaging.
// Actual build uses Kbuild (Makefile) within the driver directory.
kernel_module {
    name: "my_driver",
    srcs: ["my_driver.c"],
    kernel_build: ":android14-6.1",
}
```

### Kconfig and defconfig

```
Kconfig structure:
  kernel/Kconfig                ← top-level
  drivers/my_driver/Kconfig     ← driver-level

Adding a new option:
  config MY_DRIVER
      tristate "My Driver"
      depends on ARCH_ARM64
      help
        Enable My Driver support.

defconfig for device:
  device/<OEM>/<product>/kernel_defconfig  ← device-specific config
  kernel/configs/android-base.config       ← GKI mandatory options

GKI mandatory Kconfig options (android-base.config) MUST NOT be disabled.
```

### Module Signing

```
GKI kernel requires module signature verification:
  - Google signs GKI modules
  - OEM signs vendor modules with their key

Signing process:
  scripts/sign-file sha256 <key.pem> <cert.pem> my_driver.ko

Verification:
  modinfo my_driver.ko | grep sig
  insmod my_driver.ko  → kernel checks signature against enrolled cert

Android Verified Boot 2.0:
  Vendor module signing key must be enrolled in AVB trust chain.
  Failure = module load rejected at runtime.
```

### Kernel Panic / Oops Triage

```
Typical oops output:
  Unable to handle kernel NULL pointer dereference at virtual address 0000...
  Call trace:
    my_function+0x1c/0x40 [my_driver]
    ...

Steps:
  1. Decode the call trace with addr2line or scripts/faddr2line
  2. Check if the oops is in a GKI module or vendor module
  3. If vendor module → check KMI symbol usage and pointer lifecycle
  4. If GKI kernel → file upstream bug; do not patch locally

addr2line usage:
  aarch64-linux-android-addr2line -e vmlinux <address>
```

### sysfs / ioctl Driver Interface

```
sysfs attribute (read):
  static ssize_t my_attr_show(struct device *dev, ...) { ... }
  DEVICE_ATTR_RO(my_attr);
  → Appears as: /sys/devices/.../my_attr

ioctl interface:
  Defined in: include/uapi/linux/my_driver.h   ← UAPI; userspace-visible
  Command: _IOR('M', 1, struct my_data)

RULE: All userspace-visible interfaces (sysfs, ioctl, /dev nodes) must be
stable. Changing them breaks binary compatibility with userspace blobs.
```

### 16KB Page Size Kernel Configuration

Android 15+ supports both 4KB and 16KB page sizes. OEMs must build and ship 16KB-capable kernels for devices with ARM64 16KB TLB granule hardware.

**Kernel config options:**

```
# Enable 16KB pages (new)
CONFIG_ARM64_16K_PAGES=y

# Legacy 4KB pages (default)
CONFIG_ARM64_4K_PAGES=y
```

**Kleaf build flag:**

```bash
--page_size=16k
```

**Kernel image header:** The page size is encoded at byte offset 25 of the kernel image:
- `0` = Unspecified, `1` = 4KB, `2` = 16KB, `3` = 64KB

The bootloader reads this to select the correct DTB and kernel configuration.

**GKI 16KB builds:** Available on-demand from `android15-6.6` and `android16-6.12`. OEMs can request 16KB GKI builds alongside the default 4KB builds.

**Dual boot images:** Devices supporting the Developer Option toggle ship two boot images (4K + 16K) to allow page-size switching. This requires:
- `BOARD_KERNEL_PATH_16K` — path to prebuilt 16KB kernel
- `BOARD_KERNEL_MODULES_16K` — 16KB kernel modules
- `BOARD_16K_OTA_USE_INCREMENTAL := true` — reduces OTA size

**Vendor module impact:** All vendor `.ko` modules must be rebuilt against the 16KB GKI kernel. Modules built against a 4KB kernel will fail ABI checks on a 16KB kernel.

**Verification on device:**

```bash
adb shell getconf PAGE_SIZE                    # Expected: 16384
adb shell zcat /proc/config.gz | grep 16K      # CONFIG_ARM64_16K_PAGES=y
```

> **Deep-dive:** See `references/16kb_page_migration_guide.md` for the full audit checklist (ELF alignment, mmap, hardcoded constants, build config, testing strategy).

### Android 15 GKI / Kernel Changes

| Change | Impact |
|--------|--------|
| GKI android15-6.6 (Linux 6.6 LTS) | New kernel baseline; one GKI per release (no android15-6.1) |
| KMI break from A14 | android14-6.1 KMI not compatible with android15-6.6; full module rebuild required |
| 16KB page size GKI builds | Available as on-demand builds alongside 4KB default; see section above |
| android14-6.1 forward-compatible | Can still run on A15 devices, but cannot swap kernel without module rebuild |

### Android 16 GKI / Kernel Changes

| Change | Impact |
|--------|--------|
| GKI android16-6.12 (Linux 6.12 LTS) | New kernel baseline; KMI break from android15-6.6; full vendor module rebuild required |
| EEVDF scheduler replaces CFS | Earliest Eligible Virtual Deadline First scheduler changes scheduling latency; audit RT-priority and SCHED_FIFO code for behavioral changes in audio/media workloads |
| Per-VMA locks | Fine-grained `mmap_lock` replacement reduces contention in multi-threaded workloads (camera/media pipelines); audit drivers using `mmap_lock` directly |
| Proxy Execution | Borrows CPU cycles from high-priority processes to help lower-priority lock holders; mitigates priority inversion without PI mutexes |
| RCU_LAZY | Defers RCU callbacks to reduce power consumption; benefits battery-sensitive use cases |
| CONFIG_ZRAM_MULTI_COMP | Multi-algorithm ZRAM compression; benefits low-RAM devices |
| Memory allocation profiling | `CONFIG_MEM_ALLOC_PROFILING` attributes allocations to source line; enable via `sysctl.vm.mem_profiling` |
| Clang 19.0.1 stricter bounds | `__counted_by` attribute enforces runtime bounds; vendor modules with dynamically-sized arrays must set the size field immediately after allocation or risk kernel panics. `CONFIG_UBSAN_SIGNED_WRAP` disabled to prevent false positives |
| CONFIG_OF_DYNAMIC default on | Exposes driver bugs in device tree node reference counting (use-after-free, memory leaks); audit all `of_node_get()`/`of_node_put()` calls in vendor drivers |
| 16KB page GKI on-demand builds | 16KB GKI builds available for both android15-6.6 and android16-6.12 |

**A16 vendor module migration checklist:**
1. Rebuild all `.ko` modules against android16-6.12 GKI headers (KMI break)
2. Audit scheduler-sensitive code (RT priorities, `SCHED_FIFO`) for EEVDF behavior
3. Audit `mmap_lock` usage in drivers for per-VMA lock compatibility
4. Audit all `__counted_by` annotated arrays — set size field before any access
5. Audit all OF/device-tree API usage for proper `of_node_put()` calls
6. Verify module signatures against new GKI signing keys

---

## Forbidden Actions

1. **Forbidden:** Using non-KMI kernel symbols in a vendor module — any symbol not in `abi_gki_aarch64.xml` is not guaranteed stable and will break on kernel updates.
2. **Forbidden:** Patching `vmlinux` or GKI-signed modules locally — GKI modules are signed by Google; local patches break signature verification.
3. **Forbidden:** Disabling mandatory GKI Kconfig options from `android-base.config` — these are required for CTS/VTS compliance.
4. **Forbidden:** Writing kernel driver code that bypasses the HAL — all hardware access from userspace must go through the HAL interface defined in `hardware/interfaces/`.
5. **Forbidden:** Modifying UAPI headers (`include/uapi/`) without a versioning/compatibility plan — UAPI changes break binary compatibility with existing userspace binaries.
6. **Forbidden:** Loading unsigned kernel modules on a production device with Verified Boot enabled — module signature failures cause silent load rejection or panic.
7. **Forbidden:** Routing kernel driver issues that surface as HAL failures to this skill alone — coordinate with `L2-hal-vendor-interface-expert` for the HAL interface side.

---

## Tool Calls

```bash
# Check if a symbol is in the KMI list
grep "my_symbol" kernel/android/abi_gki_aarch64.xml

# Check module info and signature
modinfo my_driver.ko

# Decode kernel oops call trace address
aarch64-linux-android-addr2line -e vmlinux <hex_address>
python3 kernel/scripts/faddr2line vmlinux my_function+0x1c

# List loaded kernel modules on device
adb shell lsmod

# Check kernel config option
adb shell zcat /proc/config.gz | grep CONFIG_MY_DRIVER

# Verify module loads without error
adb shell insmod /vendor/lib/modules/my_driver.ko
adb logcat -s kernel | grep my_driver

# Check sysfs attributes
adb shell ls /sys/devices/<path>/
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| HAL interface for the kernel driver | `L2-hal-vendor-interface-expert` |
| SELinux denial for driver device node or sysfs | `L2-security-selinux-expert` |
| Kernel module packaging in `Android.bp` | `L2-build-system-expert` |
| `insmod` in `.rc` file at early-init | `L2-init-boot-sequence-expert` |
| Kernel ABI changes in an Android version upgrade | `L2-version-migration-expert` |
| pKVM EL2 issue in `arch/arm64/kvm/hyp/` or `/dev/kvm` behaviour | `L2-virtualization-pkvm-expert` |

Emit `[L2 KERNEL → HANDOFF]` before transferring.

---

## References

- `references/gki_module_development_guide.md` — GKI module authoring, KMI symbol lists, and signing.
- `references/16kb_page_migration_guide.md` — 16KB page size audit checklist (kernel config, Kleaf flags, dual boot images).
- `kernel/android/abi_gki_aarch64.xml` — KMI symbol allowlist (authoritative).
- `kernel/configs/android-base.config` — mandatory GKI Kconfig options.
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

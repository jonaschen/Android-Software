# GKI Kernel Module Development Guide

> Android 14 — GKI 6.1 / 6.6 branches

## GKI Architecture

GKI (Generic Kernel Image) separates the kernel into two layers:

```
┌─────────────────────────────────────────────────────────┐
│  GKI Kernel (vmlinux + GKI modules)                      │
│  Built by Google, signed by Google                       │
│  Same binary runs on all compatible SoCs                 │
│                                                          │
│  KMI (Kernel Module Interface) — stable symbol list      │
│  All exported symbols vendor may use:                    │
│    kernel/android/abi_gki_aarch64.xml                   │
└──────────────────────┬──────────────────────────────────┘
                       │  KMI (stable ABI)
┌──────────────────────▼──────────────────────────────────┐
│  Vendor Modules (.ko files)                              │
│  Built by SoC / OEM, signed by OEM                      │
│  Loaded at boot time by init                             │
│                                                          │
│  Examples: my_sensor.ko, gpu_driver.ko, audio_codec.ko  │
└─────────────────────────────────────────────────────────┘
```

## GKI Branches

| Branch | Kernel | Android | Status |
|--------|--------|---------|--------|
| `android12-5.10` | 5.10 | A12+ | Maintained |
| `android13-5.15` | 5.15 | A13+ | Maintained |
| `android14-6.1` | 6.1 | A14+ | **Current for A14** |
| `android15-6.6` | 6.6 | A15+ | **Current for A15** |
| `android-mainline` | Latest | Development | Upstream |

## Writing a GKI-Compliant Vendor Module

### Module Structure

```c
// my_driver.c
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>

// MANDATORY: License declaration
MODULE_LICENSE("GPL");
MODULE_AUTHOR("OEM Corp");
MODULE_DESCRIPTION("My device driver");
MODULE_VERSION("1.0");

// ONLY use symbols from abi_gki_aarch64.xml
// Check: grep "symbol_name" kernel/android/abi_gki_aarch64.xml

static int my_driver_probe(struct platform_device *pdev)
{
    // Device initialization
    return 0;
}

static int my_driver_remove(struct platform_device *pdev)
{
    return 0;
}

static const struct of_device_id my_driver_match[] = {
    { .compatible = "oem,my-device" },
    {}
};
MODULE_DEVICE_TABLE(of, my_driver_match);

static struct platform_driver my_driver = {
    .probe  = my_driver_probe,
    .remove = my_driver_remove,
    .driver = {
        .name           = "my_driver",
        .of_match_table = my_driver_match,
    },
};

module_platform_driver(my_driver);
```

### Kbuild File

```makefile
# drivers/my_driver/Makefile
obj-$(CONFIG_MY_DRIVER) += my_driver.o
my_driver-y := my_driver_core.o my_driver_hw.o
```

### Kconfig

```kconfig
# drivers/my_driver/Kconfig
config MY_DRIVER
    tristate "My OEM Driver"
    depends on ARCH_ARM64
    depends on OF
    help
      Enable support for OEM My Device.
      To compile as a module, choose M here.
```

### Android.bp Integration

```python
// For packaging the .ko into a system image:
// Note: actual compilation uses Kbuild; Android.bp wraps the result.

prebuilt_etc {
    name: "my_driver.ko",
    src: "my_driver.ko",
    sub_dir: "modules",
    vendor: true,
    filename_from_src: true,
}
```

## KMI Symbol List Management

The KMI is the contract between GKI and vendor modules. Only symbols in `abi_gki_aarch64.xml` may be used.

### Checking Symbols

```bash
# List all symbols your module requires
nm --undefined-only my_driver.ko | awk '{print $NF}'

# Check each against KMI list
for sym in $(nm --undefined-only my_driver.ko | awk '{print $NF}'); do
    grep -q "\"$sym\"" kernel/android/abi_gki_aarch64.xml \
        && echo "OK: $sym" \
        || echo "NOT IN KMI: $sym"
done
```

### Adding a Symbol to KMI

If a symbol your module needs is missing from the KMI list:

1. **Verify it should be stable:** The symbol must be in a subsystem that won't change the function signature.
2. **Submit to android-mainline:** Add to the appropriate fragment in `kernel/android/abi_gki_aarch64_<subsystem>`.
3. **Get Google review:** KMI additions require Google Kernel team sign-off.
4. **Alternative:** Refactor driver to avoid the non-KMI symbol.

## Module Signing

### Production (AVB 2.0)

```bash
# Sign with OEM key
scripts/sign-file sha256 oem_key.pem oem_cert.pem my_driver.ko

# Verify signature
modinfo my_driver.ko | grep "sig_"

# The signing certificate must be enrolled in the device's AVB trust chain
# (configured in the bootloader / secure boot enrollment)
```

### Development (insecure boot)

```bash
# On a device with Verified Boot disabled:
adb push my_driver.ko /data/local/tmp/
adb shell insmod /data/local/tmp/my_driver.ko

# Check load success
adb logcat -s kernel | grep "my_driver"
adb shell lsmod | grep my_driver
```

## init.rc — Loading Modules at Boot

```ini
# vendor/etc/init/my_driver.rc

# Load module at early-init (before /data is mounted)
on early-init
    insmod /vendor/lib/modules/my_driver.ko

# Or load conditionally based on hardware detection:
on early-init && property:ro.hardware=my_board
    insmod /vendor/lib/modules/my_driver.ko
```

## Kernel Panic / Oops Analysis

```bash
# Decode a call trace address to source line
aarch64-linux-android-addr2line -e vmlinux 0xffffffc012345678

# Using faddr2line (more convenient):
python3 scripts/faddr2line vmlinux "my_function+0x1c/0x40 [my_driver]"

# Decode entire oops from logfile:
python3 scripts/decode_stacktrace.py vmlinux < oops.txt
```

### Reading a Kernel Oops

```
[  123.456] Unable to handle kernel NULL pointer dereference
             at virtual address 0000000000000008
             pc : my_function+0x1c/0x40 [my_driver]
             lr : my_caller+0x34/0x80 [my_driver]
Call trace:
 my_function+0x1c/0x40 [my_driver]   ← fault location
 my_caller+0x34/0x80 [my_driver]
 platform_drv_probe+0x24/0xa0
 ...

Interpretation:
  pc = program counter = where fault occurred
  lr = link register = who called the faulting function
  +0x1c/0x40 = offset 0x1c into a 0x40-byte function
```

## Device Tree (DTS/DTBO)

```dts
/* device tree overlay for my_driver */
&my_bus {
    my_device: my-device@100 {
        compatible = "oem,my-device";
        reg = <0x100 0x10>;
        interrupts = <0 123 IRQ_TYPE_LEVEL_HIGH>;
        clocks = <&clk MY_CLK>;
        status = "okay";
    };
};
```

Build as DTBO (Device Tree Blob Overlay):
```python
// Android.bp
dtbo {
    name: "my_device_overlay",
    srcs: ["my_device.dts"],
}
```

## sysfs and ioctl — Userspace Interface Rules

**Golden rule:** Once a sysfs attribute or ioctl command is exposed to userspace, it is part of the stable ABI. Changing or removing it breaks vendor binary compatibility.

```c
// sysfs attribute — read-only
static ssize_t my_status_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    return snprintf(buf, PAGE_SIZE, "%d\n", get_status());
}
DEVICE_ATTR_RO(my_status);

// Register in probe():
device_create_file(dev, &dev_attr_my_status);
// Creates: /sys/devices/<path>/my_status

// ioctl command — define in UAPI header
// include/uapi/linux/my_driver.h  (UAPI = userspace API)
#define MY_DRIVER_IOCTL_BASE  'M'
#define MY_DRIVER_GET_STATUS  _IOR(MY_DRIVER_IOCTL_BASE, 1, struct my_status)
#define MY_DRIVER_SET_CONFIG  _IOW(MY_DRIVER_IOCTL_BASE, 2, struct my_config)
```

Userspace (HAL implementation) accesses via:
```cpp
int fd = open("/dev/my_device", O_RDWR);
struct my_status status;
ioctl(fd, MY_DRIVER_GET_STATUS, &status);
```

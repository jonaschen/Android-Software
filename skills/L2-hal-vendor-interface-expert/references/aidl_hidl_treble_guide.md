# AIDL, HIDL, and Treble Architecture Guide

> Android 14 — `hardware/interfaces/`

## HAL Evolution

| Era | Technology | Status |
|-----|-----------|--------|
| Pre-Treble | Passthrough HAL (`dlopen`) | Deprecated |
| Android 8–13 | HIDL (`.hal` files) | Frozen — no new HALs |
| Android 11+ | AIDL (`.aidl` files) | **Current standard** |

## AIDL Interface Structure

```
hardware/interfaces/<subsystem>/aidl/
├── Android.bp                          ← aidl_interface module
└── android/hardware/<subsystem>/
    ├── I<Name>.aidl                    ← Primary interface
    ├── I<Name>Callback.aidl            ← Async callback interface
    └── <DataType>.aidl                 ← Parcelable data types
```

### Android.bp for AIDL HAL

```python
aidl_interface {
    name: "android.hardware.foo",
    device_specific: true,              # Lives in vendor partition
    srcs: ["android/hardware/foo/*.aidl"],
    stability: "vintf",                 # Required for HAL interfaces
    backend: {
        cpp: { enabled: true },
        java: { enabled: false },       # HALs rarely need Java backend
        ndk: { enabled: true },         # NDK backend for vendor code
    },
    versions_with_info: [
        { version: "1", imports: [] },
        {
            version: "2",
            imports: ["android.hardware.common-V1"],
        },
    ],
    frozen: true,                       # Lock current version
}
```

### AIDL Interface Annotation

```java
// I<Name>.aidl
package android.hardware.foo;

// @VintfStability: interface is part of the stable VINTF ABI
@VintfStability
interface IFoo {
    // Methods annotated with @nullable, @utf8InCpp, etc. as needed
    String doSomething(in byte[] data);
    void registerCallback(IFooCallback callback);
}
```

## Versioning Workflow

```
1. Unfreeze current version:
   In Android.bp: remove 'frozen: true' or set 'frozen: false'

2. Make changes to .aidl files

3. Regenerate API snapshot:
   m android.hardware.foo-update-api
   This updates: aidl/aidl_api/android.hardware.foo/<version>/

4. Review diff in aidl_api/ — these files are the ABI contract

5. Re-freeze:
   Set 'frozen: true' in Android.bp
   Increment version in versions_with_info

6. Update VINTF manifest to declare new version:
   vendor/etc/vintf/manifest.xml
```

## VINTF Manifest

The VINTF manifest declares which HALs the vendor partition provides.

```xml
<!-- vendor/etc/vintf/manifest.xml -->
<manifest version="2.0" type="device">
    <hal format="aidl">
        <name>android.hardware.foo</name>
        <transport>hwbinder</transport>
        <fqname>IFoo/default</fqname>
        <version>2</version>
    </hal>
</manifest>
```

The system's compatibility matrix (`compatibility-matrix.xml`) specifies the minimum HAL versions it requires. **Mismatch = VTS failure + boot rejection.**

## HAL Implementation Pattern

```cpp
// FooImpl.h
#include <aidl/android/hardware/foo/BnFoo.h>

class FooImpl : public ::aidl::android::hardware::foo::BnFoo {
public:
    ::ndk::ScopedAStatus doSomething(
        const std::vector<uint8_t>& data,
        std::string* _aidl_return) override;
};

// main.cpp — service entry point
#include <android/binder_manager.h>
#include <android/binder_process.h>

int main() {
    ABinderProcess_setThreadPoolMaxThreadCount(0);
    auto service = ndk::SharedRefBase::make<FooImpl>();
    auto instance = std::string(FooImpl::descriptor) + "/default";
    binder_status_t status =
        AServiceManager_addService(service->asBinder().get(), instance.c_str());
    ABinderProcess_joinThreadPool();
    return EXIT_FAILURE;
}
```

## VNDK Deep Dive

### Library Categories

```
LL-NDK:   libc, libm, libdl, liblog, libEGL, libGLESv1_CM, libGLESv2
          → Always available to vendor; lowest-level stable ABI

VNDK:     libutils, libcutils, libhidlbase, libnativewindow, ...
          → Vendor may link against these; list in build/make/target/product/vndk/

VNDK-SP:  Subset of VNDK for Same-Process HALs (SP-HALs like Vulkan)
          → Must not call any non-VNDK-SP library

Framework-only: libandroid_runtime, libart, ...
          → NOT available to vendor; causes VNDK violation if linked
```

### Checking VNDK Status

```bash
# Is libfoo in VNDK?
grep "libfoo" build/make/target/product/vndk/current.txt

# Check VNDK violation in build
# Error: "VNDK-core violation: libfoo depends on non-vndk libbar"
# Fix: either move libbar to VNDK or replace with a VNDK-safe alternative
```

## Binder Domains (Treble Enforcement)

| Domain | Device Node | Used By |
|--------|------------|---------|
| Framework Binder | `/dev/binder` | System ↔ System |
| Vendor Binder | `/dev/vndbinder` | Vendor ↔ Vendor |
| HW Binder | `/dev/hwbinder` | HIDL (legacy) |

**The kernel enforces these domain boundaries.** A vendor process attempting to open `/dev/binder` will fail. This is by design — it enforces the Treble ABI boundary at the OS level.

## HAL Testing

```bash
# Run VTS HAL test for a specific HAL
atest VtsHalFooV2_0TargetTest

# Check HAL registration on device
adb shell service list | grep android.hardware.foo
adb shell dumpsys -l | grep android.hardware.foo

# Verify VINTF compatibility
adb shell vintf --check-compat
```

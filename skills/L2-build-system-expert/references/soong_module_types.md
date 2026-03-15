# Soong Module Types Reference

> Android 14 — `build/soong/`

## Core C/C++ Module Types

| Module Type | Output | Key Fields |
|-------------|--------|-----------|
| `cc_library_shared` | `.so` shared library | `srcs`, `shared_libs`, `export_include_dirs` |
| `cc_library_static` | `.a` static library | `srcs`, `static_libs`, `export_include_dirs` |
| `cc_library` | Both `.so` and `.a` | Same as above |
| `cc_library_headers` | Header-only (no compiled output) | `export_include_dirs` |
| `cc_binary` | Native executable | `srcs`, `shared_libs` |
| `cc_binary_host` | Host-side binary (runs on build machine) | `srcs` |
| `cc_test` | Native test binary | `srcs`, `test_suites` |
| `cc_prebuilt_library_shared` | Prebuilt `.so` | `srcs: ["lib.so"]`, `strip: {none: true}` |
| `cc_prebuilt_library_static` | Prebuilt `.a` | `srcs: ["lib.a"]` |
| `cc_prebuilt_binary` | Prebuilt executable | `srcs: ["bin"]` |
| `cc_defaults` | Shared property set | Inherited via `defaults:` |

## Java Module Types

| Module Type | Output | Key Fields |
|-------------|--------|-----------|
| `java_library` | `.jar` | `srcs`, `libs`, `static_libs` |
| `java_library_host` | Host `.jar` | `srcs` |
| `android_app` | `.apk` | `srcs`, `manifest`, `resource_dirs` |
| `android_app_certificate` | Signing key | `certificate: "platform"` |
| `android_library` | `.aar` equivalent | `srcs`, `resource_dirs` |
| `java_defaults` | Shared property set | Inherited via `defaults:` |

## System / Packaging Module Types

| Module Type | Output | Key Fields |
|-------------|--------|-----------|
| `filegroup` | Group of files (no build output) | `srcs`, `path` |
| `prebuilt_etc` | Install file to `/etc/` | `src`, `sub_dir` |
| `prebuilt_etc_host` | Install to host etc | `src` |
| `sh_binary` | Shell script installed as binary | `src`, `filename` |
| `phony` | Build alias with no output | `required:` |

## AIDL and Protobuf

| Module Type | Output | Key Fields |
|-------------|--------|-----------|
| `aidl_interface` | AIDL-generated stubs (.java, .cpp) | `srcs`, `stability`, `versions_with_info` |
| `java_aidl_library` | Java AIDL library | `aidl.interfaces` |
| `cc_aidl_library` | C++ AIDL library | `aidl.interfaces` |
| `java_protobuf_library` | Java proto stubs | `proto.type: "lite"` |
| `cc_protobuf_library` | C++ proto stubs | `proto.include_dirs` |

## Key Module Fields Reference

```python
cc_library_shared {
    name: "libfoo",              # Unique module name (required)
    srcs: ["foo.cpp"],           # Source files

    # Dependencies
    shared_libs: ["libbar"],     # Linked at runtime (.so)
    static_libs: ["libbaz"],     # Linked at compile time (.a)
    header_libs: ["libheader"],  # Headers only

    # Visibility
    visibility: ["//my/path:__subpackages__"],

    # Partition placement
    vendor: true,                # Place in /vendor/
    product_specific: true,      # Place in /product/
    # (no flag = /system/)

    # VNDK
    vndk: {
        enabled: true,           # This lib is part of VNDK
    },

    # APEX inclusion
    apex_available: ["com.android.foo"],

    # Compile flags
    cflags: ["-DFOO_ENABLED"],
    cppflags: ["-std=c++17"],

    # Exported headers (visible to dependents)
    export_include_dirs: ["include/"],
}
```

## Conditional Compilation with soong_config_module_type

```python
soong_config_module_type {
    name: "my_cc_library",
    module_type: "cc_library_shared",
    config_namespace: "my_oem",
    variables: ["feature_x"],
    properties: ["srcs", "cflags"],
}

soong_config_string_variable {
    name: "feature_x",
    values: ["enabled", "disabled"],
}

my_cc_library {
    name: "libmyfeature",
    soong_config_variables: {
        feature_x: {
            enabled: { srcs: ["feature_x.cpp"] },
            disabled: { srcs: ["feature_x_stub.cpp"] },
        },
    },
}
```

## Common Build Flags for Platform Libraries

```python
// Disable rtti and exceptions for most platform C++ libs
cppflags: ["-fno-rtti", "-fno-exceptions"]

// 16KB page alignment (Android 15 requirement)
ldflags: ["-Wl,-z,max-page-size=16384"]

// Sanitizers (for debug builds)
sanitize: {
    address: true,   // ASan
    undefined: true, // UBSan
}
```

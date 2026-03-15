# HS-015: crosvm Is Pure Rust — Never Apply C++ Build Patterns

**Category:** Virtualization / Build
**Skills involved:** L2-virtualization-pkvm-expert, L2-build-system-expert
**Android versions:** Android 13+ (AVF)

## Insight

crosvm (`external/crosvm/`) is written entirely in Rust. Applying C++ patterns to it causes build failures and incorrect architectural suggestions.

**Wrong patterns to avoid:**
- Using `cc_binary` instead of `rust_binary` in `Android.bp`
- Suggesting `CFLAGS` or `LOCAL_CPPFLAGS` for crosvm components
- Adding `.cpp` files to crosvm's device backends
- Linking crosvm against a `cc_library_shared` using `shared_libs` directly (Rust FFI requires explicit bindings)

**Correct patterns:**
```json
rust_binary {
    name: "crosvm",
    crate_name: "crosvm",
    srcs: ["src/main.rs"],
    rustlibs: ["libbase_rust", "liblibc"],
}
```

For Rust→C interop, crosvm uses `bindgen` to auto-generate bindings from C headers.

## Why This Matters

An agent that suggests adding a C++ file to crosvm will break the build and confuse the developer. The "crosvm is Rust" invariant is a fundamental architectural fact, not a preference.

## Trigger

Any task involving `external/crosvm/` must activate `L2-virtualization-pkvm-expert`, not `L2-build-system-expert` as the primary skill.

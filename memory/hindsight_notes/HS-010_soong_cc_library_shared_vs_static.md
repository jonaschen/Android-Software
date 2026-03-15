# HS-010: cc_library_shared vs cc_library_static — VNDK Implications

**Category:** Build System
**Skills involved:** L2-build-system-expert, L2-hal-vendor-interface-expert
**Android versions:** Android 8+

## Insight

In AOSP Soong, there is an important difference between `cc_library_shared` and `cc_library_static` that has VNDK implications:

- `cc_library_shared` — produces a `.so`; if `vndk: {enabled: true}`, it is included in the VNDK snapshot and can cross the system/vendor boundary.
- `cc_library_static` — produces a `.a`; **static libraries cannot be in VNDK**. They are always linked into their consumer and cannot cross partitions.

**Common mistake:** Marking a `cc_library_static` with `vendor_available: true` and expecting it to be usable from both system and vendor. This produces a *copy* in each partition — it does not create a shared ABI boundary.

**When to use which:**
- Use `cc_library_shared` + VNDK when the library is a shared dependency across the partition boundary.
- Use `cc_library_static` only for libraries internal to a single partition or a single binary.

## Why This Matters

Incorrect use of static libraries in vendor code causes ODM/OEM divergence: each vendor gets a slightly different copy of the library, making it impossible to update the system independently (breaking Treble).

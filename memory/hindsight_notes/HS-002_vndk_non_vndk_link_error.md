# HS-002: VNDK vs Non-VNDK Linking Produces Cryptic Build Errors

**Category:** Build System + HAL
**Skills involved:** L2-build-system-expert, L2-hal-vendor-interface-expert
**Android versions:** Android 8+

## Insight

When a vendor library (tagged `vendor: true`) attempts to link against a non-VNDK system library, the build error is:

```
error: "libfoo" is not a VNDK library
```

The fix is **never** to add `vendor: true` to the system library — that crosses the Treble partition boundary. Instead:
1. Check if the library is already in `vndk-core` or `vndk-sp` (`system/vndk/VNDK.libraries.txt`).
2. If not, find a VNDK-equivalent or refactor the vendor code to not depend on it.
3. If the dependency is legitimate, file a VNDK addition proposal.

## Why This Matters

Blindly adding `vendor: true` to a framework library breaks the Treble ABI contract and causes CTS/VTS failures at the partition boundary. The Soong error is correct — the library should not cross the boundary.

## Trigger

Always route VNDK linking errors to `L2-hal-vendor-interface-expert` first, then `L2-build-system-expert` for the build rule fix.

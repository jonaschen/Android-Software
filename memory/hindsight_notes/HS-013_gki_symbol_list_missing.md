# HS-013: GKI Symbol Not in Symbol List Causes Vendor Module Load Failure

**Category:** Kernel / GKI
**Skills involved:** L2-kernel-gki-expert
**Android versions:** Android 11+ (GKI)

## Insight

GKI (Generic Kernel Image) restricts which kernel symbols vendor modules can use via the **GKI symbol list** (`android/abi_gki_aarch64`). If a vendor module calls a kernel function not in the list:

```
insmod: ERROR: could not insert module foo.ko: Unknown symbol in module
```

**Fix workflow:**
1. Run `check_gki_symbol_list.sh` to identify missing symbols.
2. If the symbol should be exported: add it to `android/abi_gki_aarch64` and submit to the kernel team for review.
3. If the symbol is internal: refactor the driver to not use it (use an exported alternative or a new exported helper).

**Critical rule:** Never use `EXPORT_SYMBOL_GPL` to export a new symbol from a vendor module to expose a back-channel to the GKI kernel. This violates GKI's stability contract.

## Why This Matters

Symbol list violations cause the module to fail at `insmod` time — the device will boot without the driver. In production, this can brick devices that depend on the driver (e.g., a modem or storage driver).

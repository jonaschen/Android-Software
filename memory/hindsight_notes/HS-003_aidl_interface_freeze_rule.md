# HS-003: AIDL Interface Must Be Frozen Before HAL Server Ships

**Category:** HAL Interface Management
**Skills involved:** L2-hal-vendor-interface-expert
**Android versions:** Android 11+

## Insight

AIDL interfaces defined under `hardware/interfaces/` must be **frozen** (version locked) before a HAL server ships to production. An unfrozen interface (`@VintfStability` without a version number) cannot be used in a vendor partition that ships separately from the system.

The freezing process:
```bash
# From AOSP root, freeze interface at version N:
m aidl-freeze-api
# This generates api/N/... files alongside the .aidl sources
```

Post-freeze rules:
- You may **add** new methods/types in a new version (N+1)
- You may **never** change or remove existing methods — this breaks binary compatibility
- `@nullable` can be added to existing fields in some cases (check compatibility tool)

## Why This Matters

Shipping an unfrozen interface causes `vintf` validation to fail at boot — the HAL is rejected as non-compliant. This is a launch-blocking bug that is easy to avoid by freezing early.

## Trigger

Every time a new HAL AIDL interface is added, immediately verify it is frozen. Use `check_aidl_version.py` from `L2-hal-vendor-interface-expert/scripts/`.

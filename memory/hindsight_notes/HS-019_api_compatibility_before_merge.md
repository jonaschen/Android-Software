# HS-019: Always Run API Compatibility Check Before Merging Framework Changes

**Category:** Version Migration / Framework
**Skills involved:** L2-version-migration-expert, L2-framework-services-expert
**Android versions:** All

## Insight

Any change to `frameworks/base/` that touches `@SystemApi`, `@PublicApi`, or any method in an `api/` snapshot file must pass API compatibility verification before merging:

```bash
# Check for API surface changes:
m api-stubs-docs-non-updatable-update-current-api

# If this fails with "error: Added <method>", the API was changed without updating current.txt
# Fix: run the update target:
m update-api
```

**Hidden failure mode:** A developer removes a method thinking it's unused, but the method is part of a `@SystemApi` contract. This breaks OEM apps that call it. The compatibility check catches this at build time.

**For mainline modules:** Use `m <module>-check-api` — mainline modules have stricter compatibility requirements since they can be updated independently of the OS.

## Why This Matters

API compatibility breaks are CTS failures and require an emergency patch. The `check_api_compatibility.py` script in `L2-version-migration-expert/scripts/` can compare API dumps from before and after a change.

## Trigger

Add to pre-merge checklist for any PR touching `frameworks/base/api/`, `frameworks/base/core/java/android/`, or any `@SystemApi` annotation.

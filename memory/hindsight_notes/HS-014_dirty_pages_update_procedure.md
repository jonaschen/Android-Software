# HS-014: Dirty Pages Update Procedure After OS Version Bump

**Category:** Version Migration / Memory Model
**Skills involved:** L2-version-migration-expert
**Android versions:** All (model procedure)

## Insight

After an Android OS version bump, update `memory/dirty_pages.json` in this order:

1. **Run impact detection:** `python3 scripts/detect_dirty_pages.py <git-diff-output>` (Phase 4 tool; until then, manual review).
2. **Identify affected paths:** Cross-reference changed AOSP paths against each skill's `path_scope` field.
3. **Mark affected skills `dirty`:** Set `status: "dirty"`, `dirty_reason: "android_version_bump"`, list `affected_paths`.
4. **After refreshing a skill:** Set `status: "clean"`, update `android_version_tested` and `last_validated`.

**Template for a dirty entry:**
```json
"L2-<skill>": {
  "status": "dirty",
  "android_version_tested": "Android 14",
  "last_validated": "2026-03-15",
  "dirty_reason": "android_version_bump",
  "affected_paths": ["path/that/changed/"]
}
```

## Why This Matters

Without dirty page tracking, skill content drifts silently. An AI agent using a stale skill will confidently cite outdated API names, paths, or patterns — the most dangerous failure mode of the system.

## Trigger

Run this procedure at the start of every major Android version migration engagement.

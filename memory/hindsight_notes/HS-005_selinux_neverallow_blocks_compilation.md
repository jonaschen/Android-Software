# HS-005: SELinux neverallow Rules Block Build, Not Just Runtime

**Category:** SELinux
**Skills involved:** L2-security-selinux-expert, L2-build-system-expert
**Android versions:** All

## Insight

SELinux `neverallow` violations are **compile-time errors** in Android — the `checkpolicy` tool (run during the build) rejects the policy if any `allow` rule would violate a `neverallow`. This means:

1. A policy change that seems valid at runtime can still break the build.
2. `neverallow` errors appear in the build log as `libselinux` or `sepolicy` target failures, not as runtime AVC denials.
3. AOSP adds new `neverallow` rules with each major Android release — a policy that compiled on A14 may fail on A15.

**Diagnosis:** If `m sepolicy` fails with `neverallow` in the error output, the allow rule being added violates a platform policy constraint. The solution is **never** to remove the `neverallow` — instead, restructure the allow rule or use a more specific type.

## Why This Matters

Teams sometimes suppress the error by commenting out `neverallow` rules. This silently weakens the platform security model and will be caught by CTS/VTS `sepolicy_tests`.

## Trigger

Any SELinux compile failure should route to `L2-security-selinux-expert`. Do not treat as a build system error.

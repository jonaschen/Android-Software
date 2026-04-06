---
id: HS-028
title: "16KB page-size compliance mandatory by May 31, 2026 for Play Store"
skill: L2-version-migration-expert
date: 2026-04-07
source: research-session
---

## Insight

Google Play enforces 16KB page-size compliance with a hard deadline:

- **Nov 1, 2025**: All new apps/updates targeting Android 15+ (API 35) must
  support 16KB page sizes on 64-bit ARM devices.
- **May 31, 2026**: Final deadline. Non-compliant apps may be blocked from
  publishing updates. One-time extension was available but only extends to
  this date.

This affects apps with native code (NDK/JNI). Pure Java/Kotlin apps are
unaffected. The 16KB requirement applies at the ELF alignment level (see
HS-006 for technical details).

## Lesson

BSP engineers shipping vendor apps (Settings, SystemUI, Camera) via Play
must ensure all native libraries are 16KB-aligned by May 2026. This is not
just an app developer concern — vendor partitions carrying prebuilt APKs with
JNI libs need rebuild.

GKI android16-6.12 builds now offer 16KB page-size kernel images, so the
entire stack (kernel + userspace) can run 16KB consistently.

## Cross-Skill Impact

- **L2-build-system-expert**: `cc_library_shared` targets need linker flag
  audit (see HS-006).
- **L2-kernel-gki-expert**: 16KB GKI kernel builds available for android16-6.12.
- **L2-hal-vendor-interface-expert**: Vendor HAL .so files need alignment check.

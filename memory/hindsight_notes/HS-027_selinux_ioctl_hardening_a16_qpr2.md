---
id: HS-027
title: "Android 16 QPR2 adds SELinux macro to harden kernel driver IOCTLs"
skill: L2-security-selinux-expert
date: 2026-04-07
source: research-session
---

## Insight

Android 16 QPR2 introduces an SELinux macro specifically designed to harden
kernel drivers by blocking restricted IOCTLs in production builds. The macro:

1. **Blocks deprecated IOCTLs** and development-only IOCTLs in production.
2. **Limits driver profiling IOCTLs** to shell or debuggable apps only.
3. Enforces a zero-trust model at the hardware driver interface level.

This is part of Android 16's broader push to validate every request — device,
app, or user — before granting access, even at the driver IOCTL boundary.

## Lesson

When writing or reviewing SELinux policy for vendor kernel drivers, check
whether the driver exposes IOCTLs that should be restricted in production.
The new macro provides a standard way to gate these — no need for ad-hoc
neverallow rules. Vendor `.te` files should adopt this macro for any custom
kernel drivers.

## Cross-Skill Impact

- **L2-kernel-gki-expert**: Out-of-tree driver modules need IOCTL audit.
- **L2-hal-vendor-interface-expert**: HAL implementations using ioctl() to
  talk to kernel drivers should verify their IOCTLs aren't blocked.
- **L2-version-migration-expert**: A15→A16 migration checklist needs IOCTL
  hardening audit step.

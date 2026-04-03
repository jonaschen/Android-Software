---
id: HS-023
title: "GKI android16-6.12 branch introduces new KMI baseline"
skill: L2-kernel-gki-expert
date: 2026-04-04
source: research-session
---

## Insight

Android 16 ships with the `android16-6.12` GKI kernel branch (Linux 6.12 LTS).
KMI stability is scoped per LTS+Android version pair — symbols stable within
`android16-6.12` are NOT interchangeable with `android14-6.1` or `android15-6.6`.

Key changes:
- 16 KB page-size GKI builds are now available on-demand for android16-6.12.
- Vendor modules must be rebuilt against the new KMI symbol list.
- The `vmlinux.symvers` from android16-6.12 is the new baseline.

## Lesson

When upgrading a BSP from A14/A15 to A16, **all out-of-tree vendor .ko modules
must be recompiled** against the android16-6.12 KMI. Do not assume symbol
compatibility across GKI generations. Check `abi_gki_aarch64` symbol list diff
early in the migration.

## Cross-Skill Impact

- **L2-version-migration-expert**: Add android16-6.12 to kernel ABI delta checklist.
- **L2-hal-vendor-interface-expert**: Vendor HAL modules shipped as .ko need rebuild.
- **L2-build-system-expert**: Kernel prebuilt paths may change for 6.12 branch.

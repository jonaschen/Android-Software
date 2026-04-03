---
id: HS-025
title: "HIDL deprecated since A11; AIDL mandatory for new HALs; audio CAP gap"
skill: L2-hal-vendor-interface-expert
date: 2026-04-04
source: research-session
---

## Insight

HIDL was deprecated in Android 11 and no new HIDL HALs are accepted. As of
Android 16, HIDL is still supported on the vendor partition for backward
compatibility, but all new HAL work must use Stable AIDL.

Notable gap: Audio HAL's Configurable Audio Policy (CAP) — widely used by OEMs —
was not ported to AIDL in A14 or A15. OEMs still on HIDL audio HAL because of
CAP dependency should track whether Android 16 QPR releases address this.

SELinux `genfscon` labels: Starting with vendor API level 202504, newer genfscon
labels are optional for older vendor partitions — eases mixed-version upgrades.

## Lesson

When advising on HAL migration, always check whether the OEM uses CAP for audio
routing. If yes, a straight HIDL→AIDL migration for audio HAL may break their
audio routing policy configuration. This is a known Google resource gap, not an
OEM oversight.

## Cross-Skill Impact

- **L2-multimedia-audio-expert**: Audio HAL AIDL migration blocked by CAP gap.
- **L2-security-selinux-expert**: genfscon label optionality for older vendors.
- **L2-version-migration-expert**: HAL migration checklist needs CAP caveat.

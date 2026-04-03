---
id: HS-026
title: "AOSP source drops change to biannual (Q2/Q4) starting 2026"
skill: L2-version-migration-expert
date: 2026-04-04
source: research-session
---

## Insight

Effective 2026, Google publishes source code to AOSP only in Q2 and Q4 (was
quarterly with QPR drops). The `android-latest-release` manifest branch replaces
`aosp-main` as the recommended baseline for building and contributing.

This means:
- QPR1 and QPR3 source no longer dropped to AOSP (only initial + QPR2).
- BSP teams must plan migration windows around Q2/Q4 drops.
- `aosp-main` is no longer the recommended branch for BSP work.

## Lesson

Update all migration checklists and diff analysis scripts to reference
`android-latest-release` instead of `aosp-main`. BSP engineers planning A16
migration should target the Q2 2026 AOSP drop as their baseline.

## Cross-Skill Impact

- **L1-aosp-root-router**: Path references should note `android-latest-release`.
- **L2-build-system-expert**: Build manifest branch defaults may need updating.

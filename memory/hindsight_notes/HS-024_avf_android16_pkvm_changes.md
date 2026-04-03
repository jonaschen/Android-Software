---
id: HS-024
title: "Android 16 AVF/pKVM: vendor VMs, early-boot VMs, 16K pVM support"
skill: L2-virtualization-pkvm-expert
date: 2026-04-04
source: research-session
---

## Insight

Android 16 introduces significant AVF/pKVM expansions:

1. **AVF LL-NDK**: Vendors can now launch VMs from the vendor partition using
   Google-managed AVF. This is a new integration surface for SoC vendors.
2. **Early-boot VM support**: VMs can run earlier in boot — critical for payloads
   like KeyMint HAL running inside a protected VM.
3. **Microdroid enhancements**: Resizable encrypted storage and 16K protected VM
   support (aligned with the platform 16KB page-size push).
4. **Linux Terminal (Ferrochrome)**: Debian-based Linux terminal in a VM — new
   user-facing feature.
5. **Guest firmware (FF-A)**: pKVM supports FF-A standardized communication with
   TrustZone for protected VMs, replacing ad-hoc SMC patterns.

## Lesson

The pKVM skill (currently tested against A15) needs a refresh to cover:
- LL-NDK vendor VM launch path
- Early-boot VM lifecycle (pre-SystemServer)
- FF-A guest firmware integration (cross-cuts with ATF skill)
- 16KB page alignment for Microdroid kernel and guest images

## Cross-Skill Impact

- **L2-trusted-firmware-atf-expert**: FF-A guest firmware uses TrustZone; ATF
  skill must document the FF-A path for protected VMs.
- **L2-init-boot-sequence-expert**: Early-boot VMs run before init's late stages;
  boot sequence skill should document the new VM-launch timing.
- **L2-kernel-gki-expert**: pKVM EL2 code lives in kernel — 6.12 branch changes.

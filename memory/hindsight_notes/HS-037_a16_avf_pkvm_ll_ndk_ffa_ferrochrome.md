---
id: HS-037
title: "Android 16 AVF/pKVM: LL-NDK, early boot VMs, FF-A, Ferrochrome, device assignment"
skill: L2-virtualization-pkvm-expert
date: 2026-04-09
source: research-session
---

## Insight

Android 16 brings a major expansion to the Android Virtualization Framework
(AVF) and pKVM hypervisor, well beyond the A15 baseline (updatable VMs, remote
attestation, experimental device assignment):

1. **AVF LL-NDK support**: Vendors can now launch VMs from the vendor partition
   using Google-managed AVF. This is a new Low-Level NDK surface that exposes
   AVF capabilities to native vendor code.
   - Path: `packages/modules/Virtualization/`, vendor partition integration

2. **Early boot VM support**: VMs can now run earlier in the boot process,
   benefiting critical payloads like **KeyMint HALs**. This means security-
   critical functionality can be isolated in a pVM before the full Android
   framework starts.
   - Path: `packages/modules/Virtualization/`, `system/core/init/`

3. **FF-A support (Firmware Framework for Arm A-profile)**: pKVM now supports
   FF-A standardized secure communication with TrustZone for protected VMs.
   This replaces ad-hoc SMC-based communication with a standardized protocol.
   - Path: `packages/modules/Virtualization/`, kernel pKVM code

4. **Ferrochrome Linux terminal**: A Debian-based Linux terminal running inside
   a virtual machine. This is a developer-facing feature using AVF/crosvm.
   - Path: `external/crosvm/`, `packages/modules/Virtualization/`

5. **Microdroid updates**: Resizable encrypted storage and 16K protected VM
   support for improved performance.

6. **Trusty OS in protected VMs**: Standard trusted applications (TAs) can now
   run TrustZone-style trusted applets inside protected VMs, not just in
   traditional TrustZone.

7. **Device assignment to pVMs (promoted)**: Was experimental in A15, now
   supports assigning platform devices to pVMs for direct hardware access.

8. **Hypervisor tracing**: Structured logging events and improved function
   tracing for pKVM debugging.

## Lesson

The AVF/pKVM skill needs significant content expansion for A16:
- LL-NDK is a new API surface not previously documented.
- Early boot VMs create a cross-skill interaction with init/boot sequence.
- FF-A changes the TrustZone communication model documented in ATF skill.
- Ferrochrome is a new use case for the crosvm/AVF stack.
- Device assignment graduating from experimental changes the pVM capability model.

## Cross-Skill Impact

- **L2-trusted-firmware-atf-expert**: FF-A support changes the pKVM↔TrustZone
  communication interface; Trusty in pVMs blurs the ATF/pKVM boundary.
- **L2-init-boot-sequence-expert**: Early boot VMs run before full init;
  KeyMint-in-pVM changes boot dependency order.
- **L2-hal-vendor-interface-expert**: LL-NDK means vendor HALs can interact
  with AVF; KeyMint HAL in early boot VM is a new pattern.
- **L2-kernel-gki-expert**: pKVM runs in kernel 6.12 context; FF-A requires
  kernel-level support; hypervisor tracing hooks into kernel tracing infra.
- **L2-security-selinux-expert**: pVM-based KeyMint and Trusty change the
  security domain model.

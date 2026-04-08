---
id: HS-038
title: "Android 16 QPR2 SELinux IOCTL hardening macro and KeyMint 4.0 attestation"
skill: L2-security-selinux-expert
date: 2026-04-09
source: research-session
---

## Insight

Android 16 QPR2 introduces two significant security changes:

### 1. SELinux IOCTL Hardening Macro

A new SELinux macro hardens kernel drivers by:
- Blocking **restricted IOCTLs** in production builds (deprecated IOCTLs,
  development-only IOCTLs)
- Limiting **profiling IOCTLs** to shell or debuggable apps only
- This specifically targets GPU syscall filtering (QPR2 release note category:
  "GPU Syscall Filtering")

Impact for BSP developers:
- Vendor kernel drivers that use custom IOCTLs must be audited against the
  new restricted list
- GPU drivers (Adreno, Mali, PowerVR) are primary targets
- Any IOCTL that was only used during development/profiling will be blocked
  in user builds
- Policy files in `system/sepolicy/` will contain the new macro definitions

This builds on HS-027 (IOCTL hardening in QPR2 context) with concrete
implementation details now available.

### 2. KeyMint 4.0 with APEX Module Integrity

Android 16 introduces KeyMint version 4.0 with:
- New **moduleHash** field in the KeyDescription attestation structure
- Enables verification of **APEX module integrity** through attestation certs
- This ties the hardware-backed attestation chain to the software module state

Path scope:
- `hardware/interfaces/security/keymint/` — KeyMint HAL interface
- `system/security/` — framework-side attestation handling
- `system/sepolicy/` — SELinux policies for KeyMint domains

## Lesson

The SELinux skill's Architecture Intelligence section should document:
1. The new IOCTL hardening macro and its effect on vendor drivers
2. How to audit vendor IOCTLs for the restricted list
3. The pattern: development IOCTLs allowed in userdebug, blocked in user builds

The security skill should also cross-reference KeyMint 4.0 with the pKVM
early-boot-VM pattern (HS-037) where KeyMint can run in a protected VM.

## Cross-Skill Impact

- **L2-kernel-gki-expert**: IOCTL restrictions affect kernel driver development;
  CONFIG_SECURITY_SELINUX interactions with driver IOCTLs.
- **L2-hal-vendor-interface-expert**: KeyMint 4.0 HAL interface update; vendor
  GPU HAL drivers affected by IOCTL filtering.
- **L2-virtualization-pkvm-expert**: KeyMint in early boot VMs (HS-037) +
  KeyMint 4.0 attestation = new attestation flow through pVM.

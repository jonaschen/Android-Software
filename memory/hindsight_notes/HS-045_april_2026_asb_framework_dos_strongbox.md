---
id: HS-045
title: "April 2026 ASB — CVE-2026-0049 Framework zero-interaction DoS + CVE-2025-48651 StrongBox high-severity"
skill: L2-framework-services-expert
date: 2026-04-17
source: research-session
---

## Insight

The April 2026 Android Security Bulletin (2026-04-01 / 2026-04-05 patch levels)
introduces two notable findings that affect the skill set's framework and
security domains.

### CVE-2026-0049 — Framework zero-interaction DoS (Critical)

- **Component**: `frameworks/base/` — Android Framework
- **Severity**: Critical
- **Patch level**: 2026-04-01
- **Affected versions**: Android 14, 15, 16, and 16-QPR2
- **Exploit profile**: Zero-interaction (no user action) — a malicious
  application can trigger local DoS, "bricking" software responsiveness until
  hard reset. Remote triggering paths are not disclosed but the "zero-click"
  framing in multiple advisories suggests an IPC-reachable entry point
  (likely Binder or intent handler).
- **Exploitation status**: Not known to be exploited in the wild at disclosure.

### CVE-2025-48651 — StrongBox (High)

- **Component**: StrongBox keystore implementations (Google, NXP,
  STMicroelectronics, Thales Secure Elements)
- **Severity**: High
- **Patch level**: 2026-04-05
- **AOSP bug IDs**: A-434039170, A-467765081, A-467765894, A-467762899
- **Impact profile**: StrongBox flaws typically risk key extraction,
  privilege escalation, or DoS. Specific impact not publicly detailed.
- **Relevance**: StrongBox is the hardware-backed secure element keystore
  (distinct from TEE-based KeyMint). Vendor-specific SE firmware patches
  required — this is not fixed by a platform-only update.

## Lesson

1. **Framework-reaching zero-interaction DoS is back on the threat model.**
   Past AOSP framework DoS classes typically required user interaction
   (launching a malicious app). CVE-2026-0049 removes that barrier. When
   reviewing `frameworks/base/` PRs touching public intent filters, service
   manager registration, or Binder entry points, apply extra scrutiny to
   input validation and rate limiting. An actively exploited variant of this
   class would be a P0 platform event.

2. **StrongBox patch path is vendor-side.** A platform-only ASB update does
   NOT fix SE firmware. BSP engineers must verify that the secure element
   vendor (NXP, ST, Thales, or Google Titan equivalent) has shipped their
   own patch and that the device's SE firmware has been flashed. GKI kernel
   or framework updates alone will not close this gap.

3. **Cross-version backport scope is wide.** CVE-2026-0049 affecting
   Android 14, 15, 16, and 16-QPR2 simultaneously means downstream LTS
   branches maintained by OEMs all need the patch. For L2-version-migration-expert,
   treat framework-layer critical CVEs as cross-branch work items.

## Cross-Skill Impact

- **L2-framework-services-expert**: CVE-2026-0049 entry point will land in
  `frameworks/base/` — once the patch is published to AOSP (within 48 hours
  of bulletin), use `git log --grep=CVE-2026-0049` to identify the exact
  file(s). Update Architecture Intelligence if the fix reveals a subsystem
  attack surface not currently documented.

- **L2-security-selinux-expert**: StrongBox and KeyMint sit adjacent. The
  April 2026 patch does not modify AIDL interfaces but BSP engineers should
  verify `android.hardware.security.keymint` HAL integrity after any SE
  firmware update (the SE change must not break KeyMint attestation chains).

- **L2-hal-vendor-interface-expert**: SE firmware updates may reset
  provisioning state — verify `IKeyMintDevice.getHardwareInfo()` still
  reports the expected `securityLevel = STRONGBOX` after SE firmware
  rotation.

- **L2-version-migration-expert**: Add CVE-2026-0049 and CVE-2025-48651 to
  the April 2026 patch intake checklist. Critical Framework CVEs with
  backports to A14 are a standing maintenance burden.

## Research References

- Android Security Bulletin April 2026 (source.android.com)
- NVD: CVE-2025-48651
- OpenText Cybersecurity: "Severe StrongBox Vulnerability Patched in Android"
- securityonline.info: "Android Security Bulletin April 2026"

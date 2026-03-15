# HS-022: pKVM Lives at EL2 (Non-Secure) — Completely Separate from ATF EL3

**Category:** Virtualization / Trusted Firmware
**Skills involved:** L2-virtualization-pkvm-expert, L2-trusted-firmware-atf-expert
**Android versions:** Android 13+ (pKVM)

## Insight

pKVM and ATF are often conflated because both operate below the Linux kernel. They are categorically different:

| | pKVM | ATF BL31 |
|-|------|---------|
| Exception Level | EL2 (Non-Secure) | EL3 (Secure Monitor) |
| World | Non-Secure | Secure |
| Source path | `arch/arm64/kvm/hyp/` | `atf/`, `arm-trusted-firmware/` |
| Purpose | VM isolation, stage-2 page tables | SMC dispatch, PSCI, TrustZone |
| Communicates via | HVC (hypervisor call from EL1) | SMC (secure monitor call from EL1/EL2) |

pKVM interacts with ATF only at the EL2→EL3 boundary via SMC for PSCI power management. This interaction is narrow and well-defined.

**Routing rule:**
- pKVM stage-2 page fault, VMID management, `/dev/kvm` behavior → `L2-virtualization-pkvm-expert`
- ATF boot chain, BL31 SMC handler, PSCI, TrustZone → `L2-trusted-firmware-atf-expert`
- pKVM ↔ ATF SMC interaction → both skills, pKVM first

## Why This Matters

Sending a pKVM bug to the ATF expert loses days — they have completely different source trees, toolchains, and debugging methods.

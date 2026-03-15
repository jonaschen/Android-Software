# HS-009: ATF Runs at EL3 — Never Conflate with Linux Kernel (EL1)

**Category:** Trusted Firmware / Kernel
**Skills involved:** L2-trusted-firmware-atf-expert, L2-kernel-gki-expert
**Android versions:** All

## Insight

ATF (Arm Trusted Firmware) and the Linux kernel are completely separate software running at different ARM exception levels:

```
EL3 — ATF BL31 (Secure Monitor)   ← atf/, arm-trusted-firmware/
EL2 — pKVM hypervisor              ← arch/arm64/kvm/hyp/
EL1 — Linux kernel                 ← kernel/
```

They do not share source trees, build systems, or debugging tools. Communication from EL1 to EL3 goes through **SMC calls** (Secure Monitor Call). The kernel has no direct access to ATF memory.

**Routing rule:**
- Issue is in `atf/` source, BL31, SMC handlers, PSCI → `L2-trusted-firmware-atf-expert`
- Issue is in `kernel/` or `drivers/` → `L2-kernel-gki-expert`
- Issue involves SMC calling convention at the boundary → both skills, ATF first

**Debugging tools differ:**
- ATF: JTAG, BL31 uart output, ATF trace logs (if enabled)
- Kernel: `dmesg`, `adb shell`, `ftrace`, `perf`

## Why This Matters

Sending an ATF bug to a kernel engineer (or vice versa) loses days. The skills have zero code overlap.

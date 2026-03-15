# HS-008: LK/ABL and init Are Completely Separate Boot Stages

**Category:** Bootloader / Init
**Skills involved:** L2-bootloader-lk-expert, L2-init-boot-sequence-expert
**Android versions:** All

## Insight

A common routing mistake is sending LK/ABL issues to `L2-init-boot-sequence-expert` or vice versa. The boundary is strict:

| Stage | Responsible Component | Skill |
|-------|----------------------|-------|
| Power-on → kernel handoff | LK/ABL (EL1/EL2 pre-kernel) | `L2-bootloader-lk-expert` |
| Kernel start → PID 1 | Kernel decompression, early init | `L2-kernel-gki-expert` |
| PID 1 onward | `init` process, `.rc` files | `L2-init-boot-sequence-expert` |

**Symptoms by stage:**
- Device stuck before `android logo`: LK/ABL issue → `L2-bootloader-lk-expert`
- `Kernel panic` messages: kernel issue → `L2-kernel-gki-expert`
- `init: Service ... died`: init issue → `L2-init-boot-sequence-expert`

**Key tell:** If `adb` is not available and there are no kernel messages on the serial console, the failure is in LK/ABL. If kernel messages appear but `init` never runs, it's a kernel issue.

## Why This Matters

Routing LK failures to init wastes investigation time. The tools are completely different: LK uses JTAG/serial console; init uses `adb logcat`.

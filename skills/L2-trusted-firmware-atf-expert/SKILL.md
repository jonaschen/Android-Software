---
name: trusted-firmware-atf-expert
layer: L2
path_scope: atf/, arm-trusted-firmware/, trusty/, vendor/*/trustzone/
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

## Path Scope

> **Important:** ARM Trusted Firmware (TF-A) and Trusty are **not part of the standard AOSP
> tree**. ATF is typically provided by the SoC vendor or sourced from the upstream TF-A project
> (https://git.trustedfirmware.org/TF-A/trusted-firmware-a.git). The paths below are
> conventions — confirm actual layout with the BSP.

| Path | Description | Present in |
|------|-------------|-----------|
| `atf/` | ARM Trusted Firmware source tree (TF-A) | Vendor BSP / upstream TF-A |
| `arm-trusted-firmware/` | Alternative root name for TF-A | Some vendor BSPs |
| `trusty/` | Trusty TEE OS — runs as ATF BL32 | AOSP (partial), Vendor BSP |
| `vendor/<OEM>/trustzone/` | OEM TrustZone / TEE extensions | OEM BSP |
| `device/<OEM>/<product>/` | Board-level ATF config, BL image paths | AOSP device tree |
| `external/trusty/` | Trusty client library for Android | AOSP |

---

## Trigger Conditions

Load this skill when the task involves:
- ARM Trusted Firmware (ATF / TF-A) — BL1, BL2, BL31, BL32 questions
- SMC (Secure Monitor Call) — adding, modifying, or debugging SMC handlers
- TrustZone — EL3 Secure Monitor, secure world / non-secure world interaction
- Trusty TEE OS — trusted applications (TAs), Trusty IPC, `tipc` driver
- OP-TEE — alternative TEE running as BL32
- Secure boot chain — RoT (Root of Trust), chain of trust, image signing
- PSCI (Power State Coordination Interface) — CPU hotplug, system suspend via SMC
- Secure firmware update (FWU) — BL2U, firmware image package (FIP)
- Hardware-backed Keystore / StrongBox — relies on TEE for key operations
- `android.hardware.security.keymint` HAL backed by Trusty TA
- `tlkd` (Trusty LK Dispatcher) — ATF dispatcher for Trusty as BL32

---

## Architecture Intelligence

### ARM Exception Levels and ATF Position

```
EL0  Application (user space)            Non-Secure World  │  Secure World (TrustZone)
EL1  OS Kernel (Linux / GKI)            │                  │  TEE OS (Trusty / OP-TEE)
EL2  Hypervisor (optional)              │                  │
EL3  Secure Monitor (ATF BL31)  ────────┴──────────────────┘
                                         SMC instructions cross this boundary
```

**ATF (BL31) owns EL3 exclusively.** It is the single secure monitor for the entire system.

### ATF Boot Stages (Chain of Trust)

```
Power On
  │
  ▼
BL1  (ROM / BootROM)
  │  Source: atf/bl1/
  │  Loaded from: SoC ROM (immutable)
  │  Job: Minimal HW init, load & verify BL2 from flash
  │  Exception level: EL3 (Secure)
  ▼
BL2  (Trusted Boot Firmware)
  │  Source: atf/bl2/
  │  Job: Initialize DRAM, load & verify BL31, BL32, BL33
  │       Builds FIP (Firmware Image Package) manifest
  │  Exception level: S-EL1 (Secure)
  ▼
BL31 (EL3 Runtime Firmware / Secure Monitor)  ←── STAYS RESIDENT IN EL3 FOREVER
  │  Source: atf/bl31/
  │  Job: Handle all SMC calls from EL1/EL2 (PSCI, vendor SMCs)
  │       Arbitrate Secure ↔ Non-Secure world switches
  │  Exception level: EL3 (Secure)
  │
  ├──► BL32 (Trusted OS — optional, runs in Secure EL1)
  │    │  Trusty: trusty/ or vendor/*/trusty/
  │    │  OP-TEE: external/optee_os/
  │    │  Job: Execute Trusted Applications (TAs) for Keymaster, DRM, etc.
  │    └──► Trusted Applications (TAs): key operations, DRM, biometric
  │
  └──► BL33 (Non-Trusted Firmware) = UEFI Firmware
       │  Provides UEFI services (Android 16+: required for GBL)
       │  Or: little-kernel (LK) / ABL / U-Boot (legacy)
       │  Job: Load Android bootloader (GBL or LK) → loads kernel
       └──► BL33 hands off to GBL/LK → Linux kernel
```

### SMC (Secure Monitor Call) Interface

SMC is the hardware instruction that transitions from non-secure EL1/EL2 to EL3 (BL31).

```
Non-Secure World (Linux kernel or LK)      EL3 (BL31 Secure Monitor)
                                                    │
  smc #0   ────────────────────────────────────►   SMC handler dispatch
  x0 = Function ID (SMC calling convention)        │
  x1..x7 = arguments                               ├── PSCI calls (CPU on/off/suspend)
                                                    ├── Vendor-specific SMC services
                                  ◄────────────────  ├── SiP (Silicon Provider) services
  x0 = return code                                  └── Trusted OS dispatcher (to BL32)
```

**SMC Function ID format (ARM SMCCC):**

```
Bit[31]    : 0 = SMC32, 1 = SMC64
Bits[30:24]: Calling convention version
Bits[23:16]: Service type:
               0x00 = ARM Architecture calls
               0x01 = CPU Service calls
               0x02 = SiP (SoC vendor) calls     ← OEM extensions go here
               0x03 = OEM calls
               0x04 = Standard Secure Service calls (PSCI, SDEI, ...)
               0x30-0x31 = Trusted OS calls (Trusty, OP-TEE)
Bits[15:0] : Function number within service
```

### Adding a New SMC Handler in BL31

```c
// atf/plat/<vendor>/<soc>/sip_svc_setup.c

// 1. Define the function ID
#define PLAT_SIP_MY_SERVICE     0x8200FF01  // SiP (0x02), SMC64, function 1

// 2. Register handler in the SiP dispatcher
uintptr_t plat_sip_handler(uint32_t smc_fid,
                            u_register_t x1, u_register_t x2,
                            u_register_t x3, u_register_t x4,
                            void *cookie, void *handle, u_register_t flags)
{
    switch (smc_fid) {
    case PLAT_SIP_MY_SERVICE:
        // Do secure-world work here
        // Access secure memory, configure hardware in secure mode
        SMC_RET1(handle, result);
        break;
    default:
        SMC_RET1(handle, SMC_UNK);
    }
}

// 3. Register dispatcher in bl31_main.c or plat_bl31_setup.c
static sip_svc_calls_t plat_sip_calls = {
    .svc_handler = plat_sip_handler,
    ...
};
```

### PSCI (Power State Coordination Interface)

PSCI is the standard ARM interface for power management, implemented in BL31.

```
Linux kernel calls (via SMC):
  PSCI_CPU_ON          → wake a secondary CPU core
  PSCI_CPU_OFF         → shut down current CPU core
  PSCI_SYSTEM_SUSPEND  → deep suspend (all cores off)
  PSCI_SYSTEM_RESET    → reboot

BL31 implementation:
  atf/lib/psci/psci_main.c     ← PSCI state machine
  atf/plat/<vendor>/psci.c     ← Platform-specific power sequences
```

### Trusty TEE Architecture

```
Android (Non-Secure EL1)          Trusty OS (Secure EL1 — BL32)
                                        │
android.hardware.security.keymint ─SMC─► Trusty IPC (tipc)
  KeyMint HAL                            │
  (/dev/trusty-ipc-dev0)                 ├── KeyMint TA
                                          ├── DRM/Widevine TA
  biometric HAL ─────────────────────►  ├── Fingerprint TA
                                          └── Secure storage TA

tipc kernel driver: drivers/trusty/   ← in GKI kernel
Trusty client lib: external/trusty/   ← in AOSP
```

### Firmware Image Package (FIP)

BL2 assembles a FIP — a container image that bundles BL31, BL32, BL33, and certificates:

```
fiptool create \
  --tb-fw   bl31.bin  \     # EL3 Runtime Firmware
  --tos-fw  bl32.bin  \     # Trusty / OP-TEE (optional)
  --nt-fw   lk.bin    \     # Non-Trusted Firmware (LK/ABL)
  --tb-fw-cert   bl31.crt \
  --nt-fw-cert   lk.crt  \
  fip.bin

fip.bin is then flashed to the 'fip' or 'abl' partition.
```

### Android 15 ATF-Relevant Changes

| Change | Impact |
|--------|--------|
| AVF device assignment (experimental) | Peripheral devices can be fully assigned to protected VMs at firmware level; ATF may need new SMC handlers for device passthrough |
| No direct ATF AOSP API changes | ATF changes for A15 are vendor-driven, not in AOSP mainline |

---

## Forbidden Actions

1. **Forbidden:** Routing ATF/TF-A tasks to `L2-kernel-gki-expert` — ATF runs in EL3 (Secure Monitor), which is a completely separate execution context from the Linux kernel (EL1). They share no source and no runtime.
2. **Forbidden:** Conflating Trusty OS with the Linux kernel — Trusty is a secure-world operating system running as ATF BL32 in Secure EL1; it lives in `trusty/`, not `kernel/`.
3. **Forbidden:** Writing SMC handlers without following the ARM SMCCC (SMC Calling Convention) specification — function ID collisions with PSCI or existing SiP services will silently corrupt power management.
4. **Forbidden:** Treating EL3 memory as accessible from Linux — EL3 memory (BL31 SRAM region) is protected by the Memory Management Unit at the secure world; Linux access causes a secure fault.
5. **Forbidden:** Routing Trusty TA (Trusted Application) logic to this skill alone — the non-secure side of a TA (the HAL, the `tipc` client) belongs to `L2-hal-vendor-interface-expert` (for the HAL AIDL) and `L2-kernel-gki-expert` (for the `drivers/trusty/` tipc driver).
6. **Forbidden:** Asserting that ATF source paths (`atf/`, `trusty/`) exist in standard AOSP — these are SoC/vendor-supplied trees; always verify BSP layout before citing a path.
7. **Forbidden:** Modifying PSCI CPU on/off sequences without verifying the platform's CPU power domain topology — incorrect PSCI implementation causes silent data corruption on secondary core startup.

---

## Tool Calls

```bash
# Check if device supports PSCI (from Linux kernel)
adb shell cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
adb shell cat /proc/device-tree/psci/compatible 2>/dev/null

# List Trusty IPC services on device
adb shell ls /dev/trusty*
adb shell ls /dev/tee*

# Check KeyMint TEE backing (should show "strongbox" or "tee")
adb shell dumpsys keystore2 | grep -i "strongbox\|software\|tee"

# Check secure boot state from bootloader
fastboot getvar secure
fastboot getvar unlocked

# Verify AVB root of trust (chains back to ATF-established RoT)
adb shell getprop ro.boot.verifiedbootstate
adb shell getprop ro.boot.vbmeta.digest

# Inspect FIP image (requires fiptool from ATF tree)
fiptool info fip.bin

# Check PSCI version exposed by BL31
adb shell cat /sys/devices/system/cpu/cpu*/online
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| Bootloader (GBL/LK/ABL) hands off to kernel — boot failure | `L2-bootloader-lk-expert` |
| UEFI firmware providing EFI protocols for GBL | `L2-bootloader-lk-expert` |
| Trusty tipc kernel driver (`drivers/trusty/`) issue | `L2-kernel-gki-expert` |
| KeyMint HAL AIDL interface (non-secure side) | `L2-hal-vendor-interface-expert` |
| SELinux denial for Trusty device node (`/dev/trusty-ipc-dev0`) | `L2-security-selinux-expert` |
| Build system packaging of BL31/BL32/FIP images | `L2-build-system-expert` |
| pKVM EL2 interaction with ATF BL31 via HVC/SMC | `L2-virtualization-pkvm-expert` |

Emit `[L2 ATF → HANDOFF]` before transferring.

---

## References

- `references/atf_boot_stages.md` — ATF boot stage deep-dive: BL1→BL2→BL31→BL32→BL33 flow, SMC calling convention, PSCI.
- `external/trusty/` — Trusty TEE client library (AOSP side).
- `external/avb/` — Android Verified Boot library (trust chain starts here from RoT established by ATF).
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

# ARM Trusted Firmware (TF-A) Boot Stages Reference

> Applies to: TF-A v2.x, Android 14, ARMv8-A / ARMv9-A platforms
> Note: ATF source (`atf/`) is not in standard AOSP. Source from:
>   https://git.trustedfirmware.org/TF-A/trusted-firmware-a.git

## ARM Exception Level Architecture

```
EL3  ─── Secure Monitor (BL31, runs here permanently after boot)
          Highest privilege. Controls Secure ↔ Non-Secure world switching.
          Only code in EL3 can access Secure EL1 and EL3 registers.

EL2  ─── Hypervisor (optional; KVM or pKVM in Android)
          Non-Secure only on most Android platforms.

EL1  ─── OS Kernel:
          Non-Secure EL1: Linux / GKI kernel
          Secure EL1: TEE OS (Trusty, OP-TEE)  ← BL32

EL0  ─── User Space:
          Non-Secure EL0: Android apps / HAL processes
          Secure EL0: Trusted Applications (TAs) running inside TEE
```

## Boot Stage Responsibilities

### BL1 — Primary Boot Loader
```
Location: atf/bl1/
Loaded from: SoC BootROM (masked ROM — immutable)
Exception level: EL3 (Secure)

Responsibilities:
  - Minimal CPU/cache/MMU initialization
  - Locate BL2 in flash (NOR/eMMC/UFS)
  - Authenticate BL2 image using RoT public key (embedded in SoC)
  - Hand off to BL2

Key files:
  atf/bl1/bl1_main.c        ← BL1 entry and auth flow
  atf/bl1/aarch64/bl1_arch.S ← Exception vector setup
```

### BL2 — Trusted Boot Firmware
```
Location: atf/bl2/
Exception level: Secure EL1 (drops from EL3 after BL1 hands off)

Responsibilities:
  - Full DRAM initialization (calls platform SPDs)
  - Load and authenticate: BL31, BL32 (TEE OS), BL33 (LK/U-Boot)
  - Build the Firmware Image Package (FIP) manifest
  - Set up memory regions (secure / non-secure carveouts)
  - Pass control to BL31

Key files:
  atf/bl2/bl2_main.c
  atf/plat/<vendor>/bl2_plat_setup.c  ← Platform DDR init, image loading
```

### BL31 — EL3 Runtime Firmware (Secure Monitor) ← MOST RELEVANT FOR DEVELOPERS
```
Location: atf/bl31/
Exception level: EL3 (Secure)
STAYS RESIDENT: Yes — BL31 is never unloaded. It lives in a reserved
                secure SRAM region for the lifetime of the device.

Responsibilities:
  - Handle ALL SMC calls from EL1 and EL2
  - Implement PSCI (CPU on/off/suspend)
  - Dispatch to SiP (SoC vendor) services
  - Switch between Secure EL1 (TEE) and Non-Secure EL1 (Linux)
  - SDEI (Software Delegated Exception Interface) for RAS

Key files:
  atf/bl31/bl31_main.c            ← Runtime entry, SMC dispatch
  atf/lib/psci/psci_main.c        ← PSCI implementation
  atf/plat/<vendor>/sip_svc.c     ← Vendor SiP SMC handlers  ← edit here for new SMCs
  atf/include/bl31/services/      ← Service headers (PSCI, SDEI, SPD)
```

### BL32 — Trusted OS (TEE)
```
Two common implementations:

Trusty (Google):
  Location: trusty/ (separate repo, may be in vendor BSP)
  Exception level: Secure EL1
  Used for: KeyMint, Widevine, Fingerprint TAs
  Entry: via ATF's "Trusty LK Dispatcher" (TLKD) in BL31

OP-TEE (Linaro):
  Location: external/optee_os/ (not standard AOSP) or standalone
  Exception level: Secure EL1
  Used in some Qualcomm and Mediatek devices
```

### BL33 — Non-Trusted Firmware
```
= little-kernel (LK) / ABL / U-Boot
Exception level: Non-Secure EL1 or EL2

This is the Android bootloader. See L2-bootloader-lk-expert for details.
ATF BL31 jumps to BL33 after completing EL3 setup.
```

## SMC Calling Convention (ARM SMCCC v1.2)

### Function ID Layout

```
Bit 31:     0 = SMC32 (32-bit register width)
            1 = SMC64 (64-bit register width)
Bits 30-24: Calling convention version (must be 0)
Bits 23-16: Service type (owner):
              0x00  ARM Architecture calls
              0x01  CPU service calls
              0x02  SiP (Silicon Provider / SoC vendor) calls  ← OEM extensions
              0x03  OEM calls (deprecated, use SiP)
              0x04  Standard Secure Service (PSCI, SDEI, …)
              0x05  Standard Hypervisor Service
              0x06  Vendor Hypervisor Service
              0x30  Trusted OS Call (Trusty)
              0x31  Trusted OS Call (OP-TEE)
Bits 15-0:  Function number within the service type
```

### PSCI Function IDs (Standard — do not redefine)

| Function | SMC ID | Description |
|----------|--------|-------------|
| `PSCI_VERSION` | `0x84000000` | Get PSCI version |
| `CPU_SUSPEND` | `0x84000001` | Suspend current CPU |
| `CPU_OFF` | `0x84000002` | Power off current CPU |
| `CPU_ON` | `0x84000003` | Power on a secondary CPU |
| `SYSTEM_SUSPEND` | `0x8400000E` | Full system suspend |
| `SYSTEM_RESET` | `0x84000009` | Warm reset |
| `SYSTEM_POWEROFF` | `0x84000008` | Power off |

### Implementing a New SiP SMC Handler

```c
// atf/plat/<vendor>/<soc>/plat_sip_svc.c

#include <common/runtime_svc.h>
#include <smccc_helpers.h>

// 1. Define function IDs (SiP range: 0x82000000-0x8200FFFF for SMC64)
#define MY_PLAT_SIP_FUNC_GET_CHIP_ID    U(0x82000001)
#define MY_PLAT_SIP_FUNC_SET_SECURE_REG U(0x82000002)

// 2. Implement handler
static uintptr_t plat_sip_handler(uint32_t smc_fid,
    u_register_t x1, u_register_t x2, u_register_t x3, u_register_t x4,
    void *cookie, void *handle, u_register_t flags)
{
    // Verify caller is from non-secure world
    if (!is_caller_non_secure(flags)) {
        SMC_RET1(handle, SMC_UNK);
    }

    switch (smc_fid) {
    case MY_PLAT_SIP_FUNC_GET_CHIP_ID:
        SMC_RET2(handle, SMC_OK, plat_get_chip_id());

    case MY_PLAT_SIP_FUNC_SET_SECURE_REG:
        // x1 = register offset, x2 = value
        // Only allow writes to approved register list
        if (!is_approved_secure_reg(x1)) {
            SMC_RET1(handle, SMC_UNK);
        }
        mmio_write_32(SECURE_REG_BASE + x1, (uint32_t)x2);
        SMC_RET1(handle, SMC_OK);

    default:
        WARN("Unimplemented SiP SMC: 0x%x\n", smc_fid);
        SMC_RET1(handle, SMC_UNK);
    }
}

// 3. Register service
DECLARE_RT_SVC(
    plat_sip_svc,
    OEN_SIP_START,
    OEN_SIP_END,
    SMC_TYPE_FAST,
    NULL,
    plat_sip_handler
);
```

### Calling an SMC from Linux Kernel

```c
// In a GKI vendor module or platform driver:
#include <linux/arm-smccc.h>

struct arm_smccc_res res;
arm_smccc_smc(MY_PLAT_SIP_FUNC_GET_CHIP_ID,
              0, 0, 0, 0, 0, 0, 0, &res);
if (res.a0 == 0) {  // SMC_OK = 0
    chip_id = res.a1;
}
```

## Trusty TEE Integration with ATF

```
Trusty is loaded by BL2 as BL32. At runtime:

Linux kernel (EL1, non-secure)
  │  smc() via tipc driver
  ▼
BL31 Secure Monitor (EL3)
  │  TLKD (Trusty LK Dispatcher) in BL31 dispatches to Trusty
  ▼
Trusty OS (Secure EL1)
  │  Trusty IPC → Trusted Application
  ▼
Trusted Application (Secure EL0)
  e.g., KeyMint TA, Widevine TA

Key source files:
  atf/services/spd/tlkd/        ← Trusty dispatcher in BL31
  external/trusty/              ← Trusty client library (Android side)
  drivers/trusty/               ← tipc kernel driver (in GKI)
```

## Firmware Image Package (FIP) Format

```
FIP = single binary container for all BL images + certificates.
Magic: 0xAAAAAAAA (4 bytes at offset 0)

Structure:
  FIP Header
  ├── Entry[0]: UUID=BL31, offset=X, size=Y
  ├── Entry[1]: UUID=BL32 (Trusty), offset=A, size=B
  ├── Entry[2]: UUID=BL33 (LK), offset=C, size=D
  ├── Entry[3]: UUID=BL31-cert
  ├── Entry[4]: UUID=BL33-cert
  └── ...
  [BL31 binary]
  [Trusty binary]
  [LK binary]
  [Certificates (X.509 DER)]

Create:
  fiptool create --tb-fw bl31.bin --tos-fw trusty.bin --nt-fw lk.bin \
    --tb-fw-cert bl31.crt --nt-fw-cert lk.crt fip.bin

Inspect:
  fiptool info fip.bin

Extract a component:
  fiptool unpack --tb-fw extracted_bl31.bin fip.bin
```

## Memory Layout (Typical ARMv8-A Android Device)

```
Physical Address Space:

0x0000_0000  ─── SoC peripherals (UART, timers, GIC, ...)
0x4000_0000  ─── DRAM start (device-specific)
             │
             ├── BL31 reserved region (16–64 MB, at top of DRAM or in SRAM)
             │   Secure, not accessible from Linux
             │
             ├── Trusty reserved region (8–32 MB, at top of DRAM)
             │   Secure EL1 accessible only
             │
             ├── Linux kernel load address
             │   Mapped as Non-Secure by BL31 before handoff to BL33
             │
             └── Linux usable DRAM (reported via DT /memory node)
```

BL31 configures the Memory Controller (via TrustZone Address Space Controller — TZASC) to enforce these boundaries before jumping to BL33.

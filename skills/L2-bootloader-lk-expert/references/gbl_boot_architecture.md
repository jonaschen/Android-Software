# Generic Bootloader (GBL) Architecture Reference

> Applies to: Android 16+ (GBL strongly recommended for new ARM-64 devices)
> Source: `bootable/libbootloader/` (AOSP, branch `uefi-gbl-mainline`)
> Official docs: https://source.android.com/docs/core/architecture/bootloader/generic-bootloader

---

## What is GBL?

The **Generic Bootloader (GBL)** is a standardized, updatable bootloader introduced in
Android 16. It replaces the fragmented landscape of vendor-specific bootloaders (LK,
U-Boot, proprietary) with a single, consistently maintained component distributed as a
UEFI application.

Key properties:
- **Standardized**: One bootloader binary across OEMs (Google-certified)
- **Updatable**: Bootloader OTA updates via dedicated ESP partitions
- **UEFI-based**: Runs as an EFI application on top of vendor UEFI firmware
- **Written in Rust**: Memory-safe implementation with Bazel build system
- **Multi-arch**: Builds for aarch64, x86_64, x86_32, riscv64

---

## Boot Chain Position

```
Power On
  │
  ▼
PBL (Primary Boot Loader)         ← SoC ROM code, immutable
  │
  ▼
UEFI Firmware                      ← SoC-specific (EDK2, U-Boot+UEFI, LK+UEFI shim)
  │  Initializes DRAM, storage, basic HW
  │  Provides UEFI Boot Services + Runtime Services
  │  Implements required EFI protocols
  │  Loads GBL from android_esp partition
  ▼
GBL (Generic Bootloader)          ← /EFI/BOOT/BOOTAA64.EFI in android_esp_{a,b}
  │  bootable/libbootloader/gbl/efi/
  │  Runs as EFI application (not a standalone OS like LK)
  │  Uses UEFI protocols to access storage, RNG, slot info
  │  Implements:
  │    - Boot mode detection (normal / fastboot / recovery)
  │    - A/B slot selection (GBL_EFI_BOOT_CONTROL_PROTOCOL)
  │    - boot.img loading (EFI_BLOCK_IO_PROTOCOL)
  │    - AVB verification (GBL_EFI_AVB_PROTOCOL)
  │    - pvmfw loading (GBL_EFI_AVF_PROTOCOL)
  │    - Kernel cmdline + bootconfig assembly
  │    - Fastboot protocol (built-in)
  ▼
Kernel (Image / Image.gz-dtb)
  │
  ▼
init (PID 1)
```

### Comparison with LK Boot Chain

```
LK chain:  PBL → SBL/XBL → LK (standalone OS, EL1) → Kernel → init
GBL chain: PBL → UEFI FW  → GBL (EFI app)          → Kernel → init
```

Key difference: LK is a standalone embedded OS that directly drives hardware. GBL is a
UEFI application that delegates hardware access to the UEFI firmware through standardized
protocols. This is what enables standardization — GBL doesn't need to know about specific
SoC hardware.

---

## Partition Layout

GBL requires two EFI System Partitions (ESP) for A/B slot support:

```
GPT Partition Table:
  ...
  android_esp_a    ← GBL binary for slot A
  android_esp_b    ← GBL binary for slot B
  boot_a / boot_b  ← Kernel + generic ramdisk (same as LK devices)
  ...
```

### ESP Partition Specification

| Property | Value |
|----------|-------|
| Partition label | `android_esp_a`, `android_esp_b` |
| Partition type GUID | `C12A7328-F81F-11D2-BA4B-00A0C93EC93B` (EFI System Partition) |
| Filesystem | FAT12, FAT16, or FAT32 |
| Minimum size | 8 MB |
| GBL binary path | `/EFI/BOOT/BOOTAA64.EFI` (ARM-64) |
| Update granularity | Entire partition (no partial updates) |

### Sizing Rationale

GBL is approximately 2 MB uncompressed. The 8 MB minimum provides headroom for
growth over approximately seven years of feature additions.

### OTA Update Flow

```
OTA payload includes android_esp image
  → update_engine writes to inactive ESP slot (e.g., android_esp_b)
  → Slot switch via GBL_EFI_BOOT_CONTROL_PROTOCOL
  → Next boot: UEFI firmware loads GBL from new slot
  → If boot fails: rollback to previous slot's GBL
```

---

## Required UEFI Protocols

Firmware (EDK2, U-Boot, etc.) must implement these protocols for GBL:

### Standard UEFI Protocols

| Protocol | Purpose | Notes |
|----------|---------|-------|
| `EFI_BLOCK_IO_PROTOCOL` | Read boot.img, vendor_boot.img, pvmfw from storage | Or `EFI_BLOCK_IO2_PROTOCOL` for async I/O |
| `EFI_RNG_PROTOCOL` | Generate stack canaries, KASLR seeds, RNG seeds | Security-critical — weak RNG undermines KASLR |
| `EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL` | Console logging during boot | Default debug output |
| `EFI_DEVICE_PATH_PROTOCOL` | Device identification | Standard UEFI device paths |
| `EFI_LOADED_IMAGE_PROTOCOL` | GBL image metadata | Standard for loaded EFI apps |
| UEFI Memory Allocation Services | Scratch space for AVB, DICE, image buffers | `AllocatePages`, `AllocatePool`, etc. |

### GBL-Specific Protocols

| Protocol | Purpose | Implementation |
|----------|---------|----------------|
| `GBL_EFI_AVB_PROTOCOL` | AVB public key access and rollback index verification | Vendor firmware must provide OEM public key and rollback storage |
| `GBL_EFI_BOOT_CONTROL_PROTOCOL` | A/B slot metadata and boot reason acquisition | Replaces vendor-specific slot metadata (e.g., LK's `bootctrl` partition) |
| `GBL_EFI_AVF_PROTOCOL` | AVF config data generation from DICE chain | For pvmfw (protected VM firmware) loading — links to pKVM early boot |

Reference implementations exist for:
- **EDK2** (Tianocore) — primary reference
- **U-Boot** with UEFI support
- **LK** with UEFI shim layer

Protocol definitions are in: `bootable/libbootloader/gbl/libefi/`

---

## Firmware API Level

GBL enforces API level compatibility between the firmware and the Android platform:

```
UEFI Variable:
  Vendor GUID: 5a6d92f3-a2d0-4083-91a1-a50f6c3d9830
  Variable name: gbl_fw_api_level
  Value: integer matching ro.board.api_level

Verification:
  GBL reads gbl_fw_api_level from UEFI runtime variables
  Compares against expected API level for this Android release
  Mismatch → may refuse to boot or disable features
```

This ensures firmware and OS stay in sync, preventing issues from firmware/OS version skew.

---

## GBL Source Layout

```
bootable/libbootloader/
├── gbl/
│   ├── efi/              ← Main EFI application entry point (BOOTAA64.EFI)
│   ├── libgbl/           ← Core orchestration: boot mode, slot selection, kernel load
│   ├── libboot/          ← Boot image loading and verification pipeline
│   ├── libbootimg/       ← boot.img header parsing (v3/v4 format)
│   ├── libbootparams/    ← Kernel cmdline + bootconfig parameter assembly
│   ├── libfastboot/      ← Built-in fastboot protocol (USB + TCP)
│   ├── libefi/           ← UEFI protocol definitions (EFI_* + GBL_EFI_*)
│   ├── libefi_types/     ← UEFI type definitions and constants
│   ├── libavb/           ← Android Verified Boot — signature and hash verification
│   ├── libabr/           ← A/B partition recovery (slot state machine)
│   ├── liblp/            ← Logical partition (super) metadata parsing
│   ├── libstorage/       ← Block device abstraction over EFI_BLOCK_IO
│   ├── libboringssl/     ← Cryptographic primitives (via BoringSSL)
│   ├── libc/             ← Minimal C library for Rust FFI bridges
│   ├── smoltcp/          ← Network stack for fastboot over TCP
│   ├── libasync/         ← Asynchronous operation support
│   ├── libutils/         ← Common utility functions
│   ├── libmisc/          ← Miscellaneous helpers
│   ├── tests/            ← Host-side unit tests
│   ├── docs/             ← EFI protocol documentation
│   ├── tools/            ← Build and analysis utilities
│   └── qemu_gdb_example/ ← QEMU debugging setup
├── BUILD                  ← Top-level Bazel build file
├── MODULE.bazel           ← Bazel module definition
└── build.config.constants ← Build configuration constants
```

### Building GBL

```bash
# 1. Install dependencies
sudo apt install repo bazel-bootstrap

# 2. Checkout source
repo init -u https://android.googlesource.com/kernel/manifest -b uefi-gbl-mainline
repo sync -j16

# 3. Build EFI application (all architectures)
tools/bazel run //bootable/libbootloader:gbl_efi_dist \
  --extra_toolchains=@gbl//toolchain:all

# 4. Run unit tests
tools/bazel test @gbl//tests --extra_toolchains=@gbl//toolchain:all

# Output: EFI binaries for aarch64, x86_64, x86_32, riscv64
```

### Testing with Cuttlefish

```bash
cvd start --android_efi_loader=<path-to-gbl-efi-binary>
```

---

## Security Model

### Chain of Trust

```
SoC Root of Trust
  → verifies UEFI Firmware (vendor signing)
    → firmware verifies GBL EFI binary (OEM signing)
      → GBL verifies boot.img (AVB, via GBL_EFI_AVB_PROTOCOL)
        → GBL verifies pvmfw (AVF, via GBL_EFI_AVF_PROTOCOL)
          → Kernel + init continue the chain (dm-verity)
```

### OEM Signing Flow

1. Obtain Google-certified production GBL build
2. Sign with OEM signing solution
3. Store signed binary + signature metadata in `android_esp_{slot}` partition
4. Preserve GBL certificate intact (no additional headers wrapping)

### Attack Surfaces

| Surface | Risk | Mitigation |
|---------|------|-----------|
| FAT partition parsing | Buffer overflow in FAT driver | UEFI firmware must harden FAT parser; GBL itself doesn't parse FAT |
| EFI binary replacement | Unsigned GBL loaded by firmware | Firmware must verify GBL signature before execution |
| Rollback attack | Old GBL with known vulnerabilities | `GBL_EFI_AVB_PROTOCOL` provides rollback index enforcement |
| Standardization risk | Single vuln affects all OEMs | Trade-off for faster patching via OTA; March 2026 Qualcomm exploit demonstrated this |
| ESP integrity | Physical attacker modifies FAT partition | Locked bootloader + AVB verification prevents unsigned boot |

### March 2026 Qualcomm GBL Exploit

A three-vulnerability chain targeting Qualcomm's GBL implementation demonstrated that:
- GBL's standardized nature means vulnerability classes can affect multiple OEMs simultaneously
- The UEFI-based architecture introduces new attack surfaces (EFI protocol bugs, FAT parsing)
- Vendor GBL patches must be tracked separately from AOSP GBL updates
- See `memory/hindsight_notes/HS-040_gbl_qualcomm_exploit_march_2026.md` for details

---

## GBL vs LK Decision Matrix

| Factor | GBL | LK/ABL |
|--------|-----|--------|
| **New ARM-64 device (A16+)** | Strongly recommended | Acceptable but not preferred |
| **Existing device upgrade** | Optional (requires UEFI firmware) | Continue using |
| **Non-ARM architecture** | Supported (x86, RISC-V) | Limited (primarily ARM) |
| **Bootloader OTA updates** | First-class (ESP partition) | Vendor-specific, often difficult |
| **Security patching** | Centralized (Google-certified) | Per-vendor responsibility |
| **Custom fastboot commands** | Via GBL extension protocols | Direct C code modification |
| **Hardware abstraction** | Via UEFI protocols (standardized) | Direct HW access (SoC-specific) |
| **Build system** | Bazel + Rust | Make/CMake + C |
| **Debugging** | QEMU + GDB, Cuttlefish | JTAG, SoC-specific tools |

---

## Migration: LK to GBL

For devices transitioning from LK to GBL:

1. **Firmware prerequisite**: SoC vendor must provide UEFI firmware implementing required
   protocols. This is the primary blocker — LK devices without UEFI firmware cannot adopt GBL.
2. **Partition changes**: Add `android_esp_a` / `android_esp_b` partitions (8 MB each, FAT, ESP GUID).
3. **A/B slot logic**: Migrate from vendor-specific `bootctrl` partition to `GBL_EFI_BOOT_CONTROL_PROTOCOL`.
4. **AVB integration**: Migrate from LK's `libavb` calls to `GBL_EFI_AVB_PROTOCOL`.
5. **Custom fastboot**: Reimplement OEM fastboot commands as GBL extension protocols.
6. **Testing**: Validate with Cuttlefish emulator before hardware bring-up.

Cross-reference: `L2-version-migration-expert` for full migration impact analysis.

---

*GBL Architecture Reference v1.0 — 2026-04-11. Sources: source.android.com, AOSP bootable/libbootloader, HS-034, HS-040.*

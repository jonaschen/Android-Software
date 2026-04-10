---
name: bootloader-lk-expert
layer: L2
path_scope: bootloader/lk/, bootable/bootloader/, bootable/libbootloader/, device/<OEM>/<product>/bootloader/
version: 2.0.0
android_version_tested: Android 16
parent_skill: aosp-root-router
---

## Path Scope

> **Important:** This skill covers two bootloader ecosystems:
> 1. **Generic Bootloader (GBL)** — standardized, updatable UEFI-based bootloader introduced in Android 16. Source is in AOSP at `bootable/libbootloader/`.
> 2. **little-kernel (LK)** and vendor-specific successors (Qualcomm ABL, etc.) — **not part of standard AOSP**. Paths are SoC/OEM-supplied and vary by vendor.
>
> Always verify the actual BSP layout before asserting a vendor path.

| Path | Description | Present in |
|------|-------------|-----------|
| `bootable/libbootloader/` | **GBL source tree** — Generic Bootloader Library (Rust + Bazel) | AOSP (`uefi-gbl-mainline` branch) |
| `bootable/libbootloader/gbl/` | GBL core: EFI app, libgbl, libfastboot, libavb, libboot | AOSP |
| `bootable/libbootloader/gbl/efi/` | GBL EFI application entry point (`BOOTAA64.EFI`) | AOSP |
| `bootable/libbootloader/gbl/libefi/` | UEFI protocol definitions (standard + GBL-specific) | AOSP |
| `bootloader/lk/` | LK source tree — canonical location for Qualcomm devices | Qualcomm BSP ¹ |
| `bootable/bootloader/` | Legacy AOSP bootloader hook directory | AOSP (mostly empty stubs) |
| `device/<OEM>/<product>/` | Board-level bootloader config, partition layout XML | AOSP device tree |
| `vendor/<OEM>/proprietary/bootable/bootloader/` | MTK and other vendor LK trees | MTK BSP ¹ |
| `hardware/qcom/bootctrl/` | A/B slot control HAL (interfaces with bootloader) | Qualcomm BSP ¹ |

> ¹ Vendor-supplied paths — not in standard AOSP. Routing is by subsystem, not path presence.

---

## Trigger Conditions

Load this skill when the task involves:

### GBL (Generic Bootloader) — Android 16+
- GBL deployment, build, or configuration (`bootable/libbootloader/`)
- UEFI boot chain integration — EFI protocols, ESP partitions, `BOOTAA64.EFI`
- `GBL_EFI_AVB_PROTOCOL`, `GBL_EFI_BOOT_CONTROL_PROTOCOL`, `GBL_EFI_AVF_PROTOCOL`
- `android_esp_a` / `android_esp_b` FAT partition layout
- `gbl_fw_api_level` UEFI variable or `ro.board.api_level` alignment
- GBL OTA updates — bootloader updatability via ESP partitions
- GBL security — FAT partition integrity, EFI binary signing, exploit surfaces
- GBL + firmware integration (EDK2, U-Boot with UEFI, LK with UEFI shim)

### LK / Vendor Bootloaders (Legacy + Current)
- Fastboot protocol — commands, variables, `fastboot flash`, `fastboot oem`
- Device stuck in fastboot or download mode
- Partition table layout — GPT, partition XML (`partitions.xml`, `partition.xml`)
- Boot image loading, verification (AVB), and handoff to kernel
- A/B slot switching — `current_slot`, `slot_successful`, `slot_unbootable`
- `aboot` or ABL (Android Boot Loader) source code
- Splash screen or bootloader UI
- Bootloader unlock/lock state
- `bootloader/lk/` source questions: fastboot commands, partition parsing, device tree selection
- Download mode (Qualcomm EDL / DLOAD) questions
- Signed image requirements for bootloader stages

---

## Architecture Intelligence

### GBL (Generic Bootloader) — Android 16+

Android 16 introduces the **Generic Bootloader (GBL)**, a standardized, updatable UEFI-based
bootloader that replaces the fragmented vendor-specific bootloader landscape. GBL is
**strongly recommended** for all new ARM-64 devices shipping with Android 16.

#### GBL Boot Chain Position

```
Power On
  │
  ▼
PBL (Primary Boot Loader)       ← ROM code, immutable
  │
  ▼
SBL / XBL / UEFI Firmware       ← SoC-specific; initializes DRAM, provides UEFI services
  │  Must implement required EFI protocols (see below)
  ▼
GBL (Generic Bootloader)        ← This skill's domain (Android 16+)
  │  bootable/libbootloader/gbl/efi/
  │  Distributed as single UEFI app: /EFI/BOOT/BOOTAA64.EFI
  │  Written in Rust, built with Bazel
  │  Runs as EFI application on top of UEFI firmware
  │  Responsibilities:
  │    - Boot mode detection (normal / fastboot / recovery)
  │    - A/B slot selection via GBL_EFI_BOOT_CONTROL_PROTOCOL
  │    - Load boot.img / vendor_boot.img via EFI_BLOCK_IO_PROTOCOL
  │    - AVB verification via GBL_EFI_AVB_PROTOCOL
  │    - Load pvmfw (protected VM firmware) via GBL_EFI_AVF_PROTOCOL
  │    - Fastboot protocol (built-in, not separate binary)
  │    - Build kernel cmdline, bootconfig, DTB
  │    - Jump to kernel entry point
  ▼
Kernel (Image / Image.gz-dtb)   ← Handed off by GBL
  │
  ▼
init (PID 1)
```

#### GBL Partition Layout

GBL requires two EFI System Partitions for A/B slot support:

```
android_esp_a / android_esp_b
  ├── Partition type GUID: C12A7328-F81F-11D2-BA4B-00A0C93EC93B (ESP)
  ├── File system: FAT12/16/32
  ├── Minimum size: 8 MB (~2 MB for GBL binary + growth headroom)
  ├── Contents: /EFI/BOOT/BOOTAA64.EFI (signed GBL binary)
  └── Update granularity: entire partition (no partial GBL-only updates)
```

#### Required UEFI Protocols

Firmware must implement these protocols for GBL to function:

| Protocol | Purpose |
|----------|---------|
| `EFI_BLOCK_IO_PROTOCOL` (or `EFI_BLOCK_IO2_PROTOCOL`) | Boot image and pvmfw retrieval from storage |
| `EFI_RNG_PROTOCOL` | Stack canaries, KASLR seeds, RNG seeds |
| UEFI Memory Allocation Services | Scratch space for AVB and DICE computation |
| `EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL` | Default logging interface |
| `GBL_EFI_AVB_PROTOCOL` | Public key access and rollback index verification |
| `GBL_EFI_BOOT_CONTROL_PROTOCOL` | Slot metadata and boot reason acquisition from firmware |
| `GBL_EFI_AVF_PROTOCOL` | AVF config data generation from DICE chain (for pvmfw) |

Reference implementations for GBL-specific protocols exist for EDK2, U-Boot, and LK with UEFI.

#### Firmware API Level

```
UEFI variable (vendor GUID: 5a6d92f3-a2d0-4083-91a1-a50f6c3d9830):
  gbl_fw_api_level = <integer>

Must match: ro.board.api_level (Android system property)
Mismatch → GBL may refuse to boot or degrade functionality.
```

#### GBL Source Layout

```
bootable/libbootloader/
└── gbl/
    ├── efi/              ← Main EFI application entry point
    ├── libgbl/           ← Core GBL library (boot logic orchestration)
    ├── libboot/          ← Boot image loading logic
    ├── libbootimg/       ← boot.img format parsing
    ├── libbootparams/    ← Kernel cmdline / bootconfig parameter assembly
    ├── libfastboot/      ← Built-in fastboot protocol implementation
    ├── libefi/           ← UEFI protocol definitions (standard + GBL_EFI_*)
    ├── libefi_types/     ← UEFI type definitions
    ├── libavb/           ← Android Verified Boot library
    ├── libabr/           ← A/B partition recovery logic
    ├── liblp/            ← Logical partition (super) support
    ├── libstorage/       ← Storage abstraction layer
    ├── libboringssl/     ← Cryptographic primitives
    ├── libc/             ← Minimal C library for Rust FFI
    ├── smoltcp/          ← Network stack (for fastboot over TCP)
    ├── tests/            ← Host-side unit tests
    ├── docs/             ← EFI protocol documentation
    └── tools/            ← Build and analysis utilities
```

Build: `tools/bazel run //bootable/libbootloader:gbl_efi_dist`
Test: `tools/bazel test @gbl//tests`
Supported architectures: aarch64, x86_64, x86_32, riscv64.

#### GBL Security Considerations

1. **FAT partition attack surface**: The `android_esp_a/b` partitions use FAT, which
   introduces parsing vulnerabilities. A March 2026 Qualcomm exploit chain
   (CVE-2026-xxxx) demonstrated bootloader unlock via GBL implementation bugs.
2. **EFI binary signing**: OEMs must sign the Google-certified GBL binary; the GBL
   certificate must be preserved intact (no additional headers).
3. **Rollback protection**: `GBL_EFI_AVB_PROTOCOL` provides rollback index verification
   to prevent downgrade attacks.
4. **Standardization trade-off**: GBL's standardization means a single vulnerability
   class can affect multiple OEMs simultaneously (unlike fragmented LK/U-Boot).

---

### LK / Vendor Bootloader Architecture (Legacy + Current)

### Boot Chain Position (LK)

```
Power On
  │
  ▼
PBL (Primary Boot Loader)     ← ROM code, immutable, loads SBL/XBL
  │  SoC-internal; not in any repo
  ▼
SBL / XBL (Secondary/eXtensible Boot Loader)
  │  Qualcomm-specific; initializes DRAM, loads LK/ABL
  ▼
little-kernel (LK) / ABL      ← This skill's domain
  │  bootloader/lk/ or vendor ABL source
  │  Runs in EL1 non-secure world
  │  Responsibilities:
  │    - Read partition table (GPT)
  │    - Load boot.img from selected slot
  │    - Verify boot image (AVB2 / dm-verity)
  │    - Pass DTB / DTBO to kernel
  │    - Implement fastboot protocol
  │    - Handle A/B slot selection
  │    - Expose `androidboot.*` kernel cmdline params
  ▼
Kernel (Image / Image.gz-dtb)  ← Handed off by LK
  │
  ▼
init (PID 1)
```

### LK Source Layout (Qualcomm ABL convention)

```
bootloader/lk/
├── app/
│   ├── aboot/            ← aboot.c — Android boot app (main fastboot + boot logic)
│   └── fastboot/         ← fastboot.c — USB fastboot protocol implementation
├── dev/
│   ├── flash/            ← Storage drivers (eMMC, UFS, NAND)
│   └── pmic/             ← Power management IC drivers
├── lib/
│   └── avb/              ← Android Verified Boot library (libavb)
├── platform/
│   └── <soc>/            ← SoC-specific board init, clocks, UART
└── target/
    └── <board>/          ← Board-specific: partition.xml, panel init, keys
        ├── init.c
        └── rules.mk
```

### Fastboot Protocol

```
Host (fastboot tool)                 Device (LK fastboot handler)
                                       │
fastboot getvar product         ────►  handle_getvar()
                                ◄────  "OKAY<product_name>"

fastboot flash boot boot.img    ────►  handle_flash()
  (DATA phase: image bytes)           → writes to boot partition
                                ◄────  "OKAY"

fastboot oem <custom_cmd>       ────►  handle_oem_cmd()
                                ◄────  OEM-defined response

fastboot continue               ────►  handle_boot()
                                       → loads boot.img, jumps to kernel
```

**Custom fastboot variables** are registered in `aboot.c`:
```c
fastboot_publish("version-baseband", info.baseband_version);
fastboot_publish("product", TARGET(BOARD));
```

### Partition Table

Most Android devices use GPT. LK reads the partition table at startup.

```
Partition XML (target/<board>/partition.xml) — compile-time source:
  <partition label="boot"        size_in_kb="65536" type="..."/>
  <partition label="vendor_boot" size_in_kb="65536" type="..."/>
  <partition label="super"       size_in_kb="4194304" type="..."/>

GPT on device (runtime):
  /dev/block/by-name/boot        ← symlinked by ueventd from GPT label
  /dev/block/by-name/vendor_boot
  /dev/block/by-name/super
```

### A/B Slot Selection

```
LK reads slot metadata from the bootctrl partition (or BCB):
  slot_a: { priority, tries_remaining, successful_boot }
  slot_b: { priority, tries_remaining, successful_boot }

Selection logic:
  1. Pick highest priority slot with tries_remaining > 0
  2. If boot succeeds: mark slot_successful=1 (done by init + update_engine)
  3. If boot fails: decrement tries_remaining; if 0 → mark unbootable → try other slot

Android kernel cmdline set by LK:
  androidboot.slot_suffix=_a
  androidboot.verifiedbootstate=green   ← AVB result
```

### Android Verified Boot (AVB)

```
LK calls libavb to verify boot.img:
  avb_slot_verify()
    → reads vbmeta partition
    → checks signature against embedded public key (or device-enrolled key)
    → verifies hash tree descriptor for boot partition
  Result:
    GREEN  → full verified boot; key matches OEM key
    YELLOW → key is device-enrolled (user-installed); warning shown
    ORANGE → verification disabled (unlocked bootloader)
    RED    → verification failed; boot aborted (locked device)
```

### Android 15 Bootloader-Relevant Changes

| Change | Impact |
|--------|--------|
| 16KB page size boot | Bootloader must read page size from kernel image header to select correct DTB/kernel config |
| `ro.boot.hardware.cpu.pagesize` | OEM-specific property for signaling page size to userspace |
| Virtual A/B v3 | New OTA update mechanism; boot slot selection logic updated |
| Dual kernel OTA | Two boot images (4K + 16K) for page size toggle support |

### Android 16 Bootloader-Relevant Changes

| Change | Impact |
|--------|--------|
| **GBL introduction** | Standardized UEFI-based bootloader replaces vendor-specific LK/U-Boot; strongly recommended for new ARM-64 devices |
| **Bootloader OTA** | GBL is updatable via `android_esp_a/b` partitions — bootloader updates become first-class OTA payloads |
| **UEFI protocol interface** | Firmware must implement `GBL_EFI_AVB_PROTOCOL`, `GBL_EFI_BOOT_CONTROL_PROTOCOL`, `GBL_EFI_AVF_PROTOCOL` |
| **pvmfw integration** | GBL loads protected VM firmware (pvmfw) before kernel via `GBL_EFI_AVF_PROTOCOL` — links to pKVM early boot |
| **Firmware API level** | `gbl_fw_api_level` UEFI variable must match `ro.board.api_level`; mismatch blocks boot |
| **Rust implementation** | GBL is written in Rust (memory-safe) with Bazel build — different toolchain from LK (C/Makefile) |
| **Multi-arch support** | GBL builds for aarch64, x86_64, x86_32, riscv64 — broader than LK's ARM focus |

---

## Forbidden Actions

1. **Forbidden:** Routing LK/fastboot issues to `L2-init-boot-sequence-expert` — LK and GBL run before the kernel and `init`; their source is in `bootloader/lk/` or `bootable/libbootloader/`, not `system/core/init/`.
2. **Forbidden:** Routing partition table layout questions to `L2-build-system-expert` — GPT partition layout is defined in `target/<board>/partition.xml` (LK) or firmware provisioning (GBL), not in `Android.bp` or build makefiles.
3. **Forbidden:** Treating LK paths as standard AOSP paths — `bootloader/lk/` is SoC/OEM-supplied and absent from vanilla AOSP. Always confirm the BSP layout before asserting a path. (GBL at `bootable/libbootloader/` **is** in AOSP.)
4. **Forbidden:** Modifying `androidboot.*` kernel cmdline parameters without understanding their consumers — these are read by `init`, `vold`, `ueventd`, and the Android property service; changes affect the entire system.
5. **Forbidden:** Advising direct edits to partition size without a full partition layout audit — resizing one partition requires adjusting all subsequent partitions in the GPT; an error bricks the device.
6. **Forbidden:** Conflating Download Mode (EDL / DLOAD — SoC ROM) with Fastboot Mode (LK/GBL) — EDL is a SoC-level rescue mode that bypasses the bootloader entirely; it is not addressable from LK or GBL source.
7. **Forbidden:** Routing A/B bootctrl HAL questions to this skill alone — the `bootctrl` HAL implementation (`hardware/qcom/bootctrl/`) bridges the bootloader and Android; coordinate with `L2-hal-vendor-interface-expert`.
8. **Forbidden:** Conflating GBL with LK — GBL is a UEFI application (Rust, Bazel, `bootable/libbootloader/`) while LK is a standalone embedded OS (C, Make, `bootloader/lk/`). They have different build systems, languages, boot interfaces, and deployment models.
9. **Forbidden:** Assuming all Android 16 devices use GBL — GBL is "strongly recommended" but not mandatory; existing devices may continue using LK/U-Boot/proprietary bootloaders. Always ask which bootloader the device uses.
10. **Forbidden:** Treating `android_esp_a/b` FAT partitions like regular Android partitions — these are EFI System Partitions with specific GUID, FAT filesystem, and `/EFI/BOOT/BOOTAA64.EFI` layout requirements; they follow UEFI conventions, not Android's dynamic partition model.

---

## Tool Calls

```bash
# === GBL-Specific (Android 16+) ===

# Build GBL from source (requires uefi-gbl-mainline checkout)
tools/bazel run //bootable/libbootloader:gbl_efi_dist

# Run GBL unit tests
tools/bazel test @gbl//tests

# Check GBL firmware API level on device
adb shell getprop ro.board.api_level

# List android_esp partitions
adb shell ls -la /dev/block/by-name/android_esp*

# Test GBL with Cuttlefish emulator
cvd start --android_efi_loader=<path-to-gbl-efi>

# === Common (LK and GBL) ===

# List partition table on device
adb shell cat /proc/partitions
adb shell ls -la /dev/block/by-name/

# Check current A/B slot
adb shell getprop ro.boot.slot_suffix
fastboot getvar current-slot
fastboot getvar slot-count

# Check AVB status
adb shell getprop ro.boot.verifiedbootstate
fastboot getvar verified-boot-state

# List all fastboot variables
fastboot getvar all 2>&1 | head -30

# Read partition (for analysis — requires root / unlocked bootloader)
adb shell dd if=/dev/block/by-name/boot of=/data/local/tmp/boot.img bs=4096

# Unpack boot image
python3 external/avb/avbtool.py info_image --image boot.img

# Check AVB metadata
python3 external/avb/avbtool.py info_image --image vbmeta.img
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| Kernel fails to boot after LK/GBL hands off | `L2-init-boot-sequence-expert` |
| A/B bootctrl HAL implementation | `L2-hal-vendor-interface-expert` |
| AVB key enrollment or signing pipeline | `L2-trusted-firmware-atf-expert` (if in secure world) |
| `ueventd` not creating `/dev/block/by-name/` symlinks | `L2-init-boot-sequence-expert` |
| SELinux denial for bootloader-related device nodes | `L2-security-selinux-expert` |
| Build system packaging of bootloader images | `L2-build-system-expert` |
| GBL pvmfw loading or `GBL_EFI_AVF_PROTOCOL` issues | `L2-virtualization-pkvm-expert` |
| UEFI firmware (BL2/BL31) providing EFI protocols to GBL | `L2-trusted-firmware-atf-expert` |
| GBL migration planning (LK→GBL transition) | `L2-version-migration-expert` |

Emit `[L2 BOOTLOADER → HANDOFF]` before transferring.

---

## References

- `references/gbl_boot_architecture.md` — GBL architecture, UEFI protocols, deployment guide, and security model.
- `references/lk_boot_flow.md` — LK boot sequence, fastboot protocol, and A/B slot logic.
- `bootable/libbootloader/` — GBL source tree (AOSP, `uefi-gbl-mainline` branch).
- `bootable/libbootloader/gbl/docs/` — GBL EFI protocol specifications.
- `external/avb/` — Android Verified Boot library (`avbtool.py` for image inspection).
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.
- [GBL Overview (source.android.com)](https://source.android.com/docs/core/architecture/bootloader/generic-bootloader)
- [Deploy GBL (source.android.com)](https://source.android.com/docs/core/architecture/bootloader/generic-bootloader/gbl-dev)

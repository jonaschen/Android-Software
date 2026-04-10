# Android Bootloader Reference — LK and GBL

> Applies to: Qualcomm ABL / little-kernel (Android 14–15+), Generic Bootloader / GBL (Android 16+)
> Note: LK source is not in standard AOSP. GBL source is in AOSP at `bootable/libbootloader/`.

## Bootloader Landscape

As of Android 16, two bootloader ecosystems coexist:

| Bootloader | Era | Language | Build System | AOSP Source | Key Trait |
|-----------|-----|----------|-------------|-------------|-----------|
| **GBL** (Generic Bootloader) | Android 16+ | Rust | Bazel | `bootable/libbootloader/` | Standardized, updatable UEFI app |
| **LK** (little-kernel) / ABL | Android 4–16 | C | Make/CMake | Vendor BSP (`bootloader/lk/`) | SoC/OEM-specific, mature |

GBL is **strongly recommended** for new ARM-64 devices. Existing devices shipping with LK/U-Boot may continue using them. Both share the same fundamental responsibilities: load + verify + boot the kernel.

---

## GBL Boot Flow (Android 16+)

See `references/gbl_boot_architecture.md` for full GBL architecture details.

```
UEFI Firmware provides EFI services
              │
              ▼
        GBL entry (EFI application)       ← /EFI/BOOT/BOOTAA64.EFI
              │
        Boot mode detection               ← key press / BCB flag / reboot reason
              │
        ┌─────────────────────────────────────┐
        │  GBL decision tree:                  │
        │  KEY held?   → fastboot mode         │
        │  BCB flag?   → recovery mode         │
        │  default     → normal boot           │
        └─────────────────────────────────────┘
              │
        ┌─────▼──────────────────────────────┐
        │        GBL Normal Boot Path         │
        │  1. Query slot via BOOT_CONTROL     │
        │  2. Read boot.img via BLOCK_IO      │
        │  3. AVB verification via AVB proto  │
        │  4. Load pvmfw via AVF protocol     │
        │  5. Load kernel + initrd + DTB      │
        │  6. Build kernel cmdline + bootcfg  │
        │  7. Jump to kernel entry point      │
        └─────────────────────────────────────┘
```

---

## LK Boot Flow (Legacy + Current)

## What is little-kernel?

little-kernel (LK) is a small embedded operating system used as the Android bootloader on many ARM SoC platforms, most prominently Qualcomm devices (where it is called ABL — Android Boot Loader). It runs in EL1 non-secure world and is responsible for everything between the SoC's secondary boot loader and the Linux kernel.

## LK Boot Sequence

```
SBL/XBL hands control to LK entry point
              │
              ▼
        lk_main()                         ← bootloader/lk/kernel/main.c
              │
        platform_early_init()             ← board-level HW init (clocks, UART)
              │
        heap_init()                       ← initialize malloc heap
              │
        thread_init() / timer_init()      ← LK threading + timer subsystem
              │
        platform_init()                   ← driver init: MMC/UFS, display, USB
              │
        apps_init()                       ← register app modules
              │
        aboot_init()                      ← Android boot app  ← main logic here
              │
        ┌─────────────────────────────────────┐
        │  aboot_init() decision tree:         │
        │                                      │
        │  KEY held?  → fastboot mode          │
        │  BCB flag?  → recovery mode          │
        │  REASON?    → download/recovery      │
        │  default    → normal boot            │
        └─────────────────────────────────────┘
              │
        ┌─────▼──────────────────────────────┐
        │        Normal Boot Path             │
        │                                     │
        │  1. Read GPT / partition table      │
        │  2. Select A/B slot                 │
        │  3. Read boot.img from slot         │
        │  4. AVB verification (libavb)       │
        │  5. Load kernel + initrd + DTB      │
        │  6. Build kernel cmdline            │
        │     (androidboot.* params)          │
        │  7. Jump to kernel entry point      │
        └─────────────────────────────────────┘
```

## boot.img Format

```
┌─────────────────────────┐  ← boot.img header (magic: ANDROID!)
│   Header v3/v4          │    page_size, kernel_size, ramdisk_size
├─────────────────────────┤
│   Kernel (Image.gz-dtb) │  ← compressed kernel + appended DTB
├─────────────────────────┤
│   Generic Ramdisk       │  ← CPIO: /init, busybox tools
├─────────────────────────┤
│   Boot Signature        │  ← AVB hash footer / vbmeta signature
└─────────────────────────┘

vendor_boot.img (A/B enabled devices):
├── Vendor Ramdisk        ← device-specific drivers, firmware
└── DTB (DTBO merged)     ← device tree blob

LK loads both boot.img + vendor_boot.img and merges ramdisks.
```

## Fastboot Protocol Deep Dive

```
USB CDC ACM or ADB-over-TCP transport layer
              │
              ▼
Fastboot packet format:
  Command: ASCII string, e.g. "getvar:product\0"
  Data:    "DATA<hex_size>" then raw bytes
  Status:  "OKAY<info>" | "FAIL<reason>" | "INFO<message>"

Key command handlers in bootloader/lk/app/aboot/aboot.c:

  "getvar:<name>"     → fastboot_getvar()    ← publish/query variables
  "download:<size>"   → fastboot_download()  ← receive image into RAM
  "flash:<partition>" → fastboot_flash()     ← write RAM buffer to partition
  "erase:<partition>" → fastboot_erase()     ← wipe partition
  "boot"              → fastboot_boot()      ← boot image in RAM without flashing
  "continue"          → fastboot_continue()  ← exit fastboot, resume normal boot
  "reboot"            → fastboot_reboot()
  "oem <cmd>"         → oem_command_handler() ← OEM-defined commands
```

### Adding a Custom Fastboot Variable

```c
// In platform/target init or aboot_init():
fastboot_publish("my-oem-version", get_my_version_string());

// Host reads it with:
// fastboot getvar my-oem-version
```

### Adding a Custom `fastboot oem` Command

```c
// bootloader/lk/app/aboot/aboot.c
static void cmd_oem_my_command(const char *arg, void *data, unsigned sz)
{
    if (!strcmp(arg, "unlock-my-feature")) {
        // implement
        fastboot_okay("feature unlocked");
    } else {
        fastboot_fail("unknown oem command");
    }
}

// Register in fastboot_register():
fastboot_register("oem my-command", cmd_oem_my_command);
```

## A/B Slot Selection Logic

```c
// Simplified from bootloader/lk/app/aboot/aboot.c

typedef struct {
    uint8_t  priority;          // 0-15, higher = preferred
    uint8_t  tries_remaining;   // 0-7, decremented each failed boot
    uint8_t  successful_boot;   // 1 = this slot successfully booted
    uint8_t  unbootable;        // 1 = do not try this slot
} slot_metadata_t;

// Selection:
//   if slot_a.unbootable → try slot_b
//   else if slot_b.unbootable → try slot_a
//   else pick slot with higher priority (and tries_remaining > 0)

// On successful boot, Android's update_verifier calls:
//   bootctrl HAL: markBootSuccessful()
// Which sets successful_boot=1 and resets tries_remaining.
```

## Kernel Command Line Parameters Set by LK

| Parameter | Example Value | Consumer |
|-----------|--------------|---------|
| `androidboot.slot_suffix` | `_a` | init, update_engine |
| `androidboot.verifiedbootstate` | `green` | keystore, init |
| `androidboot.vbmeta.hash_alg` | `sha256` | init |
| `androidboot.hardware` | `qcom` | init, ueventd |
| `androidboot.baseband` | `msm` | telephony HAL |
| `androidboot.bootdevice` | `soc/1d84000.ufshc` | ueventd symlinks |
| `androidboot.serialno` | `ABC123` | adb, fastboot |
| `androidboot.mode` | `normal` / `charger` / `recovery` | init trigger |

## Partition Table Reference

```
GPT (GUID Partition Table) on UFS/eMMC:
  Defined at compile time in: target/<board>/partition.xml
  Flashed to device by: fastboot flash partition partition.xml
                    or: provisioning tool

Critical partitions:
  xbl / xbl_a / xbl_b     ← SBL/XBL (secondary boot loader)
  abl / abl_a / abl_b     ← Android Boot Loader (LK/ABL binary)
  boot_a / boot_b          ← Kernel + generic ramdisk
  vendor_boot_a / _b       ← Vendor ramdisk + DTBs
  init_boot_a / _b         ← Generic ramdisk (A14+ GKI2.0 split)
  vbmeta_a / vbmeta_b      ← AVB metadata
  super                    ← Dynamic partitions (system, vendor, product)
  userdata                 ← /data (user data, always single slot)
  misc                     ← BCB (Bootloader Control Block) — recovery flag
```

## BCB (Bootloader Control Block)

The `misc` partition stores the BCB — a small struct that lets Android signal the bootloader to enter recovery or apply an OTA:

```c
struct bootloader_message {
    char command[32];    // "boot-recovery", "boot-fastboot", ""
    char status[32];     // Result written back by recovery
    char recovery[1024]; // Arguments to recovery
    ...
};

// Common commands written by Android RecoverySystem:
//   "boot-recovery"  → LK boots into recovery.img
//   "boot-fastboot"  → LK enters fastboot mode
//   ""               → Normal boot
```

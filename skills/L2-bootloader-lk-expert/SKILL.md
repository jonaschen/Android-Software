---
name: bootloader-lk-expert
layer: L2
path_scope: bootloader/lk/, bootable/bootloader/, device/<OEM>/<product>/bootloader/
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

## Path Scope

> **Important:** little-kernel (LK) and its successors (Qualcomm ABL, etc.) are **not part of
> the standard AOSP tree**. These paths are SoC/OEM-supplied and vary by vendor. The paths
> below reflect common conventions; always verify with the actual BSP layout.

| Path | Description | Present in |
|------|-------------|-----------|
| `bootloader/lk/` | LK source tree — the canonical location for Qualcomm devices | Qualcomm BSP |
| `bootable/bootloader/` | Legacy AOSP bootloader hook directory | AOSP (mostly empty stubs) |
| `bootable/libbootloader/` | libbootloader helpers (present in AOSP) | AOSP |
| `device/<OEM>/<product>/` | Board-level bootloader config, partition layout XML | AOSP device tree |
| `vendor/<OEM>/proprietary/bootable/bootloader/` | MTK and other vendor LK trees | MTK BSP |
| `hardware/qcom/bootctrl/` | A/B slot control HAL (interfaces with bootloader) | Qualcomm BSP |

---

## Trigger Conditions

Load this skill when the task involves:
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

### Boot Chain Position

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

---

## Forbidden Actions

1. **Forbidden:** Routing LK/fastboot issues to `L2-init-boot-sequence-expert` — LK runs before the kernel and `init`; its source is in `bootloader/lk/`, not `system/core/init/`.
2. **Forbidden:** Routing partition table layout questions to `L2-build-system-expert` — GPT partition layout is defined in `target/<board>/partition.xml` inside the LK tree, not in `Android.bp` or build makefiles.
3. **Forbidden:** Treating LK paths as standard AOSP paths — `bootloader/lk/` is SoC/OEM-supplied and absent from vanilla AOSP. Always confirm the BSP layout before asserting a path.
4. **Forbidden:** Modifying `androidboot.*` kernel cmdline parameters without understanding their consumers — these are read by `init`, `vold`, `ueventd`, and the Android property service; changes affect the entire system.
5. **Forbidden:** Advising direct edits to partition size without a full partition layout audit — resizing one partition requires adjusting all subsequent partitions in the GPT; an error bricks the device.
6. **Forbidden:** Conflating Download Mode (EDL / DLOAD — SoC ROM) with Fastboot Mode (LK) — EDL is a SoC-level rescue mode that bypasses LK entirely; it is not addressable from LK source.
7. **Forbidden:** Routing A/B bootctrl HAL questions to this skill alone — the `bootctrl` HAL implementation (`hardware/qcom/bootctrl/`) bridges LK and Android; coordinate with `L2-hal-vendor-interface-expert`.

---

## Tool Calls

```bash
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
| Kernel fails to boot after LK hands off | `L2-init-boot-sequence-expert` |
| A/B bootctrl HAL implementation | `L2-hal-vendor-interface-expert` |
| AVB key enrollment or signing pipeline | `L2-trusted-firmware-atf-expert` (if in secure world) |
| `ueventd` not creating `/dev/block/by-name/` symlinks | `L2-init-boot-sequence-expert` |
| SELinux denial for bootloader-related device nodes | `L2-security-selinux-expert` |
| Build system packaging of bootloader images | `L2-build-system-expert` |

Emit `[L2 BOOTLOADER → HANDOFF]` before transferring.

---

## References

- `references/lk_boot_flow.md` — LK boot sequence, fastboot protocol, and A/B slot logic.
- `bootable/libbootloader/` — AOSP-side bootloader interface helpers.
- `external/avb/` — Android Verified Boot library (`avbtool.py` for image inspection).
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

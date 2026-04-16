# MediaTek Kernel Architecture Reference

> **Skill:** L3-mediatek-kernel-expert
> **Version:** 1.0.0
> **Last updated:** 2026-04-17
> **Applicable SoCs:** MT6983 (Dimensity 9000) through MT6991 (Dimensity 9400), GKI 5.15 – 6.12

---

## 1. SoC Part Number Glossary

MediaTek identifies platforms by **MT-prefixed part numbers** rather than external codenames. These numbers appear in AOSP `device/mediatek/<part>/` directory names, `TARGET_BOARD_PLATFORM` variables, and kernel `Kconfig` guards.

| Commercial Name | MTK Part # | SoC Tier | GKI Branch | Android Version |
|-----------------|-----------|----------|-----------|----------------|
| Dimensity 9000 | MT6983 | Flagship | android13-5.15 | A13 (pre-GKI migration in some OEMs) |
| Dimensity 9000+ | MT6983T | Flagship | android13-5.15 | A13 |
| Dimensity 9200 | MT6985 | Flagship | android14-5.15 | A14 |
| Dimensity 9300 | MT6989 | Flagship | android14-6.1 | A15 |
| Dimensity 9400 | MT6991 | Flagship | android15-6.6 | A16 |
| Dimensity 8300 | MT6897 | High-mid | android14-6.1 | A15 |
| Dimensity 8200 | MT6895 | High-mid | android13-5.15 | A13–A14 |
| Dimensity 7200 | MT6886 | Mid | android13-5.15 | A13–A14 |
| Dimensity 7050 | MT6877V | Mid | android13-5.15 | A13 |

> **Check device part number at runtime:** `adb shell getprop ro.vendor.mtk_platform`
> **Check hardware string:** `adb shell getprop ro.hardware` (e.g., `mt6989`)
> **Check DT model:** `adb shell cat /proc/device-tree/model`

---

## 2. Out-of-Tree Module Tree Structure

MediaTek consolidates most out-of-tree drivers under a single parent:

```
vendor/mediatek/kernel_modules/
├── connectivity/       ← CONNSYS + WMT (Wi-Fi + BT + GPS + FM)
├── mtk_cam/            ← Camera ISP (Pass-1 sensor, Pass-2 post-processing)
├── mtk_audio/          ← Audio platform + smart amp drivers
├── mtk_disp/           ← Display + MML/MDP 2D composition
├── mtk_emi/            ← EMI (External Memory Interface) MPU driver
├── mtk_irq/            ← IRQ controller integration
├── scp/                ← System Companion Processor loader
├── sspm/               ← System-Side Processor Module loader
├── gpu/                ← Mali GPU + MTK GED (GPU Energy Dispatcher)
└── trustonic/          ← Trustonic Kinibi TEE kernel driver (if used)
```

### 2.1 Connectivity Subsystem (`vendor/mediatek/kernel_modules/connectivity/`)

All radio stacks on MediaTek platforms share a **combo chip** — MT66xx family (MT6639, MT6653, etc.) — accessed via a unified WMT (Wireless Management Task) transport.

```
connectivity/
├── common/             — WMT state machine, IPC with combo chip firmware
│   └── linux/          — Linux-side char device drivers (/dev/stpwmt, /dev/stpbt)
├── wlan/               — Wi-Fi driver (gen4m chip family supports Wi-Fi 6/7)
│   └── adaptor/        — MAC layer (mt7922, mt7921, mt6635)
│   └── cfg80211/       — cfg80211 integration (GKI-compliant Wi-Fi API)
├── bt/                 — Bluetooth HCI driver (HCI H4 over UART-equivalent SPI)
├── gps/                — GNSS driver (multi-band multi-constellation)
├── fm/                 — FM radio driver (rare on newer flagships)
└── power_throttling/   — Per-radio thermal throttling
```

**Combo chip crash signature:**
```
wmt_lib_notify_wholechip_reset: chip reset triggered
```
Recovery: All CONNSYS users (Wi-Fi, BT, GPS) are torn down and re-initialized.

### 2.2 Camera (`vendor/mediatek/kernel_modules/mtk_cam/`)

MediaTek's camera pipeline is multi-pass:

```
Pass-1 (sensor input)
  ↓ SENINF (MIPI CSI-2 receiver) → CAMSYS (ISP Pass-1)
  ↓ Raw Bayer frames → DRAM buffer
Pass-2 (post-processing)
  ↓ IMGSYS (DIP, MDP, WPE) reads raw → applies 3A, denoise, tone mapping
  ↓ YUV/RGB output → DRAM buffer
Camera HAL v3 AIDL → userspace
```

Key subdrivers:
```
mtk_cam/
├── seninf/             — Sensor interface (MIPI CSI-2 PHY + controller)
├── camsys/             — Camera System top (Pass-1, frame scheduler)
├── imgsys/             — Image System (DIP + MDP + WPE — Pass-2)
├── mtk-isp/            — ISP hardware register abstraction
└── sensor/             — Sensor module drivers (per-sensor files)
```

**IOMMU faults** show as:
```
mtk_iommu: fault iova=0x<addr>, master=<master_id>, port=<port>
```
The `master_id` maps to a camera HW block (SENINF, DIP, MDP, etc.) via `iommu-port-id` in the device tree.

### 2.3 Audio (`vendor/mediatek/kernel_modules/mtk_audio/`)

```
mtk_audio/
├── audio_scp/          — SCP-hosted audio DSP RPC (low-power voice, codec offload)
├── audio_smart_pa/     — Smart amplifier integration
│     ├── goodix/       — Goodix smart PA
│     ├── nxp_tfa98xx/  — NXP TFA98xx smart PA
│     └── aw88xxx/      — Awinic AW88xxx smart PA
├── asoc/
│   ├── platform/       — ALSA SoC platform drivers
│   └── machine/        — Machine driver binding DAIs
└── codec/              — MTK on-chip codec (MT6357, MT6377, etc.)
```

**ADSP/SCP boot path for audio:**
```
Boot → scp driver loads /vendor/firmware/scp.img
     → SCP firmware runs on Cortex-M4
     → SCP exposes Audio RPC channel
     → mtk_audio/audio_scp/ registers IPI listener
     → AudioFlinger tinyalsa → ALSA platform driver → SCP IPI → DSP
```

### 2.4 Display (`vendor/mediatek/kernel_modules/mtk_disp/`)

```
mtk_disp/
├── mml/                — Media ML (image signal processing pipeline, AI-assisted)
├── mdp/                — Media Data Path (2D composition, color conversion, resize)
├── disp_aal/           — Adaptive Ambient Light (per-frame backlight modulation)
├── disp_ccorr/         — Color correction engine
├── disp_gamma/         — Gamma correction engine
├── dsi/                — MIPI DSI controller (command mode + video mode)
└── dpi/                — DPI/parallel output (legacy)
```

MDP vs. MML distinction:
- **MDP** — 2D pixel ops (scale, rotate, format convert). Used by graphics compositor, ISP.
- **MML** — Full image processing pipeline (MDP + ML-accelerated denoising, HDR tone mapping).

---

## 3. TINYSYS: SCP, SSPM, and ADSP

MediaTek's **TINYSYS** is the collective name for small auxiliary processors inside the SoC. Each one has a dedicated kernel driver that acts as a firmware loader and IPI (Inter-Processor Interrupt) endpoint.

### 3.1 SCP — System Companion Processor

- **Hardware:** Cortex-M4 / M33, 128–512 KB SRAM
- **Responsibilities:** low-power sensor aggregation, always-on audio keyword, display AAL precomputation
- **Firmware:** `/vendor/firmware/scp.img` (signed by MTK TEE)
- **Kernel driver:** `vendor/mediatek/kernel_modules/scp/`
- **Userspace node:** `/dev/scp` (ioctl-based), `/sys/kernel/debug/scp/`

### 3.2 SSPM — System-Side Processor Module

- **Hardware:** Cortex-M4, <128 KB SRAM
- **Responsibilities:** CPU DVFS governance, thermal policy, power arbitration (replaces some duties of PSCI BL31 for fast decisions)
- **Firmware:** `/vendor/firmware/sspm.img`
- **Kernel driver:** `vendor/mediatek/kernel_modules/sspm/`

### 3.3 ADSP — Audio DSP (HiFi3 / HiFi4)

- **Hardware:** Cadence Tensilica HiFi3 (legacy) or HiFi4 (Dimensity 9300+)
- **Responsibilities:** audio codec offload (AAC, Opus), voice wake word, active noise cancellation
- **Firmware:** `/vendor/firmware/audio_dsp.img`
- **Kernel driver:** in `vendor/mediatek/kernel_modules/mtk_audio/audio_scp/` (ADSP shares the SCP IPI transport)

### 3.4 TINYSYS Boot Sequence

```
Linux kernel boots on AP (Application Processor)
  → platform driver for scp / sspm / adsp probes
  → request_firmware_nowait("<dsp>.img")
  → Kernel calls into ATF BL31 via SMC: SIP_SVC_LOAD_<DSP>
  → ATF BL31 authenticates image signature (via GenieZone or trustonic)
  → ATF maps image into TINYSYS SRAM (protected by EMI MPU)
  → ATF returns; kernel triggers DSP reset
  → DSP firmware runs; sets up mailbox
  → IPI (Inter-Processor Interrupt) channel opens
  → Userspace ioctls begin flowing
```

### 3.5 TINYSYS Crash Recovery

TINYSYS processors crash from watchdog, exception, or firmware bug:

```
SCP watchdog fires
  → kernel: scp_l1c_reset()
  → AEE (Android Exception Engine) dumps state to /sdcard/data/aee_exp/
  → scp driver re-requests firmware
  → ATF re-authenticates and reloads
  → IPI channel re-establishes
  → Consumer drivers (audio, sensors) reconnect
```

Diagnostic commands:
```bash
adb shell cat /sys/class/mtk_scp/*/state           # SCP runtime state
adb shell cat /sys/kernel/debug/scp/scp_A_log      # SCP trace buffer
adb shell ls /data/aee_exp/                        # AEE crash dumps
adb shell dmesg | grep -iE "scp|sspm|adsp|tinysys" # Kernel-side logs
```

---

## 4. Board Configuration and Defconfig

### 4.1 BoardConfig.mk Structure

```makefile
# device/mediatek/mt6989/BoardConfig.mk (excerpt)
TARGET_BOARD_PLATFORM := mt6989
TARGET_BOOTLOADER_BOARD_NAME := mt6989

# GKI kernel
TARGET_KERNEL_SOURCE := kernel/common
TARGET_KERNEL_CONFIG := gki_defconfig              # Base GKI config
BOARD_KERNEL_CMDLINE  := console=tty0,921600

BOARD_VENDOR_KERNEL_MODULES := \
    $(KERNEL_MODULES_OUT)/wlan_drv_gen4m.ko \
    $(KERNEL_MODULES_OUT)/mtk_cam.ko \
    $(KERNEL_MODULES_OUT)/mtk_audio.ko \
    $(KERNEL_MODULES_OUT)/scp.ko \
    $(KERNEL_MODULES_OUT)/sspm.ko
```

### 4.2 Config Fragment Stack

```
gki_defconfig                         ← Google baseline (must not be modified)
  + device/mediatek/mt6989/k6989_GKI.config    ← SoC-level features
  + device/mediatek/mt6989/k6989_debug.config  ← Debug / eng build options
  + device/mediatek/mt6989/k6989_vendor.config ← Vendor-only tweaks
```

**Rule:** Never add SoC-specific `CONFIG_*` options to `gki_defconfig`. Add them to the SoC vendor fragment.

### 4.3 Pre-GKI kernel defconfig (Legacy)

Pre-GKI targets use `k<mtkpart>_defconfig` with the entire kernel compiled as a single monolithic image, plus in-tree `drivers/misc/mediatek/*` drivers:

```
kernel/mediatek/<branch>/
├── arch/arm64/configs/k6983_defconfig
├── arch/arm64/configs/k6989_defconfig
└── drivers/misc/mediatek/        ← In-tree drivers (pre-GKI only)
```

---

## 5. GKI ABI Compliance for MTK Modules

### 5.1 Prohibited Legacy APIs

MediaTek historically used internal kernel APIs that are not on the GKI allowlist. Migration table:

| Legacy API | GKI Replacement | Module |
|-----------|----------------|--------|
| `mtk_devinfo_get()` | `of_property_read_u32()` (device tree) | mtk_cam, mtk_disp |
| `emi_mpu_set_protection()` | SMC call `SIP_SVC_EMI_MPU_SET` to ATF BL31 | mtk_emi |
| `mtk_ion_alloc()` | `dma_heap_buffer_alloc()` (DMA-BUF heaps) | mtk_cam, mtk_audio |
| `scp_ipi_send()` | Use mailbox framework or remoteproc IPI wrappers | audio_scp, sensors |
| `mtk_ccci_*` (modem) | None — CCCI is modem-internal; not cross-domain | telephony |
| `mtk_clkmgr_*` | Common Clock Framework (CCF) `clk_get()` | various |

### 5.2 DMA-BUF Heap Migration

Android 13+ GKI requires vendor modules to use DMA-BUF heaps instead of ION:

```c
/* Old (MTK ION — not GKI) */
mtk_ion_alloc(client, size, align, ION_HEAP_MULTIMEDIA_MASK, 0);

/* New (DMA-BUF heap — GKI compliant) */
#include <linux/dma-heap.h>
heap = dma_heap_find("mtk_mm-uncached");   /* MTK-reserved secure mm heap */
buf  = dma_heap_buffer_alloc(heap, size, 0, 0);
```

MTK multimedia modules completed the transition for Dimensity 9200 (MT6985) and newer.

---

## 6. 16KB Page Size Impact on MTK Modules

Android 16 mandates 16KB page size support. MTK-specific impact:

| Module | Issue | Fix |
|--------|-------|-----|
| `wlan_drv_gen4m.ko` | Rx descriptor ring `__aligned(4096)` | Change to `PAGE_SIZE` or `__aligned(16384)` |
| `mtk_cam.ko` | IOMMU mapping assumes 4KB granule (SENINF Pass-1) | Use `iommu_map()` with `PAGE_SIZE`-aligned sizes |
| `scp.ko` | SCP firmware SRAM mapping | Already PAGE_SIZE-aligned — no change needed |
| `mtk_disp.ko` | MDP/MML shared buffer alignment | Update DMA-BUF heap alignment flag |
| `mtk_audio.ko` | ADSP ringbuffer page alignment | Verify `vb2_plane` size rounding |

Reference: `references/16kb_page_migration_guide.md` for the full audit checklist.

---

## 7. MediaTek TEE: GenieZone vs. Trustonic Kinibi

MediaTek platforms support two TEE options (vendor choice):

| TEE | Origin | BL31 Integration | Typical OEMs |
|-----|--------|-----------------|--------------|
| **GenieZone** | MediaTek-owned | BL31 + BL32 combined; EL2 hypervisor assist on some Dimensity 9x00 | Xiaomi, OPPO, Vivo |
| **Trustonic Kinibi** | Trustonic | BL32 dispatched by BL31; Linux `trustonic.ko` driver | Samsung (Exynos-MTK combo), some Tecno/Infinix |

Cross-checking: `adb shell getprop ro.boot.tee.version` or look for `/dev/mobicore` (Trustonic) vs. `/dev/gz_cli` (GenieZone).

---

## 8. MediaTek-Specific Debug Commands

```bash
# Identify SoC part number and GKI version
adb shell getprop ro.vendor.mtk_platform
adb shell uname -r

# Check loaded MTK modules
adb shell lsmod | grep -E "wlan|mtk_|scp|sspm|wmt"

# Check SCP / SSPM / ADSP status
adb shell cat /sys/class/mtk_scp/*/state
adb shell cat /sys/class/remoteproc/*/state

# CONNSYS / WMT combo chip state
adb shell cat /proc/driver/wmt_dev/state
adb shell cat /proc/driver/wmt_aee

# Camera IOMMU fault analysis
adb shell dmesg | grep -iE "mtk_iommu|iova|camsys|imgsys"

# Display composition trace
adb shell cat /sys/kernel/debug/mtk_drm/clients

# WLAN driver version
adb shell cat /sys/kernel/debug/wlan0/*

# AEE crash dumps
adb shell ls /data/aee_exp/

# Audit KMI compliance for a module
bash skills/L3-mediatek-kernel-expert/scripts/check_mtk_kmi_symbols.sh \
    out/target/product/mt6989/vendor/lib/modules/wlan_drv_gen4m.ko
```

---

## 9. Notable Differences from Qualcomm

Cross-reference to `skills/L3-qualcomm-kernel-expert/` — this table highlights where MTK diverges from QC patterns:

| Area | Qualcomm | MediaTek |
|------|----------|----------|
| Out-of-tree module root | `vendor/qcom/opensource/` (multiple repos) | `vendor/mediatek/kernel_modules/` (single tree) |
| DSP loader | PIL / remoteproc with `.mbn` signed images | Custom SCP/SSPM drivers with `.img` signed images |
| Secure boot chain | XBL → ABL → kernel | BROM → Preloader → LK → kernel |
| Fastboot owner | ABL (`bootloader/lk/app/aboot/`) | LK (`bootloader/lk/` — MTK-customized) |
| Combo chip | qcacld-3.0 (Wi-Fi only in single repo; BT/GPS separate) | CONNSYS/WMT unified transport for Wi-Fi + BT + GPS + FM |
| DSP framework | FastRPC (`/dev/fastrpc-*`) | IPI (`/dev/scp`, `/dev/sspm`) |
| TEE | QSEECOM / Trusty | GenieZone or Trustonic Kinibi |
| Memory protection | Hypervisor stage-2 + HLOS-side iommu | EMI MPU (hardware) + SMC BL31 |
| SoC codename format | Human-readable (lahaina, kalama, sun) | MT-part number (mt6983, mt6989, mt6991) |

---

*MediaTek Kernel Architecture Reference v1.0.0 — Part of the L3-mediatek-kernel-expert skill. Covers GKI 5.15 through 6.12, MT6983 (Dimensity 9000) through MT6991 (Dimensity 9400).*

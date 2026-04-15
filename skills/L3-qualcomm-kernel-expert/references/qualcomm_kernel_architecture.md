# Qualcomm Kernel Architecture Reference

> **Skill:** L3-qualcomm-kernel-expert
> **Version:** 1.0.0
> **Last updated:** 2026-04-16
> **Applicable SoCs:** SM8350 (lahaina) through SM8750 (sun), GKI 5.10 – 6.12

---

## 1. SoC Codename Glossary

Qualcomm uses internal codenames for SoC platforms. These codenames appear in AOSP `device/qcom/<codename>/` directory names, `TARGET_BOARD_PLATFORM` variables, and kernel `Kconfig` guards.

| Commercial Name | Qualcomm Codename | SoC Part # | GKI Branch | Android Version |
|-----------------|------------------|-----------|-----------|----------------|
| Snapdragon 888 | lahaina | SM8350 | android12-5.4 | A12 (MSM kernel) |
| Snapdragon 8 Gen 1 | taro | SM8450 | android13-5.10 | A13 |
| Snapdragon 8 Gen 2 | kalama | SM8550 | android14-5.15 | A14 |
| Snapdragon 8 Gen 3 | crow | SM8650 (8 Gen 3) | android14-6.1 | A14–A15 |
| Snapdragon 8 Elite | sun | SM8750 | android15-6.6 | A16 |
| Snapdragon 7s Gen 3 | niobe | SM7635 | android14-6.1 | A15 |
| Snapdragon X Elite | hamoa | SC8380XP | android15-6.6 | A16 (PC/Automotive) |

> **Check device codename at runtime:** `adb shell getprop ro.board.platform`
> **Check SoC ID:** `adb shell cat /sys/devices/soc0/soc_id`

---

## 2. Out-of-Tree Module Repository Structure

Qualcomm's key kernel modules live in separate Git repositories under `vendor/qcom/opensource/`. This is different from in-tree drivers in `kernel/drivers/`.

### 2.1 Camera Kernel (`vendor/qcom/opensource/camera-kernel/`)

```
camera-kernel/
├── drivers/
│   ├── cam_core/           — Core camera request manager, session, sync
│   ├── cam_isp/            — ISP subsystem (IFE, SFE, CSID, TFE)
│   │   ├── isp_hw_mgr/     — IFE hardware manager
│   │   └── isp_hw_top/     — IFE register definitions
│   ├── cam_icp/            — Image Compute Processor (IPE, BPS, OFE)
│   ├── cam_sensor_module/  — Sensor, actuator, OIS, flash, eeprom drivers
│   ├── cam_smmu/           — Camera IOMMU/SMMU wrapper
│   ├── cam_utils/          — Shared utilities, debug infrastructure
│   └── cam_lrme/           — Low-Res Motion Estimation engine
└── Kbuild
```

**Key build variable:** `CONFIG_SPECTRA_CAMERA=m` enables the camera kernel module build.

### 2.2 Audio Kernel (`vendor/qcom/opensource/audio-kernel/`)

```
audio-kernel/
├── asoc/
│   ├── codecs/             — Codec drivers (WCD938x, WCD937x, etc.)
│   └── msm/                — Platform-level ALSA SoC drivers
│       ├── qdsp6v2/        — Q6ASM (Audio Stream Manager) interface
│       └── msm-audio-effects-q6-v2.c
├── dsp/
│   ├── q6asm.c             — ADSP Audio Stream Manager protocol
│   ├── q6afe.c             — ADSP Audio Front End protocol
│   └── q6adm.c             — ADSP Audio Device Manager protocol
├── ipc/
│   └── apr.c               — APR (Asynchronous Packet Router) transport
└── soc/
    └── pinctrl-lpi.c       — Low-Power Island (LPI) pin control
```

**FastRPC path:** `/dev/fastrpc-adsp` (for ADSP) — used by `libadsprpc.so` to RPC into DSP.

### 2.3 WLAN (`vendor/qcom/opensource/wlan/qcacld-3.0/`)

The `qcacld-3.0` driver supports all recent Qualcomm Wi-Fi chipsets (WCN685x, WCN7850). It is the largest single QC out-of-tree module (~400K lines).

```
qcacld-3.0/
├── core/
│   ├── hdd/        — Host Driver Daemon — netdev interface, cfg80211
│   ├── mac/        — 802.11 MAC layer, SME, PE, LIM
│   ├── wma/        — Firmware/WMI abstraction layer
│   └── dp/         — Datapath — Rx/Tx ring management
├── components/
│   ├── mlme/       — Multi-Link Operation (MLO) for Wi-Fi 7
│   └── pmo/        — Power Management Offloads
└── fw-api/         — Firmware WMI/HTT API headers (DO NOT MODIFY)
```

**Key compatibility guard in Kconfig:**
```
config QCA_CLD_WLAN
    depends on WCN_CHIP_VERSION  # Must match installed firmware version
```

### 2.4 Data IPA (`vendor/qcom/opensource/dataipa/`)

The Inline Packet Accelerator (IPA) handles LTE/5G data offload in hardware, bypassing the CPU for modem ↔ network packet routing.

```
dataipa/
└── drivers/platform/msm/ipa/
    ├── ipa_v3/         — IPA v3.x core driver
    ├── ipa_clients/    — Client drivers (WLAN, USB, MHI/PCIe modem)
    └── ipa_test/       — Kernel-space test framework
```

---

## 3. Peripheral Image Loader (PIL) and DSP Lifecycle

Qualcomm's ADSP, CDSP, SLPI, and modem are loaded by the **Peripheral Image Loader (PIL)**, which is part of the kernel's `remoteproc` framework.

### 3.1 Boot Sequence for ADSP

```
Kernel boot
  → PIL driver registers with remoteproc
  → userspace: rproc_recovery_disable / rproc_state = "running"
  → PIL reads /vendor/firmware/adsp.mbn
  → PIL authenticates firmware via Secure Boot (TZ QSEE)
  → PIL loads firmware into ADSP IOVA
  → ADSP runs Q6DSP code
  → APR transport (apr.ko) establishes IPC channel
  → Audio HAL opens /dev/snd/* → ALSA → Q6ASM/AFE → ADSP
```

### 3.2 ADSP Crash Recovery

When the ADSP crashes, it triggers an SSR (Subsystem Restart):

```
ADSP watchdog fires
  → kernel: remoteproc_recovery_work
  → userspace: uevent "SUBSYSTEM=adsprpc-smd"
  → AudioFlinger receives APR error → tears down sessions
  → PIL reloads adsp.mbn
  → APR transport re-establishes
  → AudioFlinger reconnects
```

Diagnostic commands:
```bash
adb shell cat /sys/bus/platform/devices/*/remoteproc*/state
adb shell dmesg | grep -E "adsp|pil|rproc|ssr"
adb shell cat /sys/kernel/debug/rproc/*/trace0   # ADSP crash log
```

---

## 4. Board Configuration and Defconfig

### 4.1 BoardConfig.mk Structure

```makefile
# device/qcom/kalama/BoardConfig.mk (excerpt)
TARGET_BOARD_PLATFORM := kalama
TARGET_BOOTLOADER_BOARD_NAME := kalama

# GKI kernel
TARGET_KERNEL_SOURCE := kernel/common
TARGET_KERNEL_CONFIG := gki_defconfig          # Base GKI config
BOARD_KERNEL_CMDLINE  := console=ttyMSM0,115200
BOARD_VENDOR_KERNEL_MODULES := \
    $(KERNEL_MODULES_OUT)/qca_cld3_wlan.ko \
    $(KERNEL_MODULES_OUT)/camera.ko \
    $(KERNEL_MODULES_OUT)/audio_apr.ko
```

### 4.2 Config Fragment Stack

GKI builds use a layered config fragment approach:

```
gki_defconfig                     ← Google baseline (must not be modified)
  + vendor/kalama_GKI.config      ← SoC-level features (CPU, GPU, memory)
  + vendor/debugfs.config         ← Debug options
  + device/qcom/kalama/kalama.config  ← Device-specific tweaks
```

**Rule:** Never add SoC-specific `CONFIG_*` options to `gki_defconfig`. Add them to the SoC vendor fragment.

---

## 5. GKI ABI Compliance for QC Modules

### 5.1 Prohibited Legacy APIs

Qualcomm historically used internal kernel APIs that are not on the GKI allowlist. Migration table:

| Legacy API | GKI Replacement | Module |
|-----------|----------------|--------|
| `msm_bus_scale_register_client()` | `icc_get()` (interconnect framework) | audio-kernel |
| `subsystem_get()` / `subsystem_put()` | `rproc_get()` / `rproc_put()` | camera-kernel |
| `qpnp_get_prop_charger_present()` | `power_supply_get_property()` | various |
| `msm_iomap()` | `ioremap()` | various |
| `kgsl_*` (GPU memory) | DMA-BUF heaps | camera/video |

### 5.2 DMA-BUF Heap Migration

Android 13+ GKI requires vendor modules to use DMA-BUF heaps instead of ION:

```c
/* Old (ION — not GKI) */
ion_alloc(client, size, align, ION_HEAP_SYSTEM_MASK, 0);

/* New (DMA-BUF heap — GKI compliant) */
#include <linux/dma-heap.h>
heap = dma_heap_find("system");
buf = dma_heap_buffer_alloc(heap, size, 0, 0);
```

QC camera-kernel completed this migration in A14. Audio-kernel completed it in A15.

---

## 6. 16KB Page Size Impact on QC Modules

Android 16 mandates 16KB page size support. QC-specific impact:

| Module | Issue | Fix |
|--------|-------|-----|
| `qca_cld3_wlan.ko` | `__aligned(4096)` in Rx ring descriptors | Change to `PAGE_SIZE` or `__aligned(16384)` |
| `camera.ko` | IOMMU mapping assumes 4KB granule | Use `iommu_map()` with `PAGE_SIZE`-aligned sizes |
| `audio_apr.ko` | SMEM buffer alignment | Already PAGE_SIZE-aligned — no change needed |
| `video_codec_v4l2.ko` | V4L2 buffer queue page alignment | Update `vb2_plane` alignment checks |

Reference: `references/16kb_page_migration_guide.md` for the full audit checklist.

---

## 7. Qualcomm-Specific Debug Commands

```bash
# Identify SoC codename and GKI version
adb shell getprop ro.board.platform
adb shell uname -r

# Check loaded QC modules
adb shell lsmod | grep -E "qca|cam|audio|ipa|video"

# Check ADSP / CDSP status
adb shell cat /sys/bus/platform/drivers/qcom-pil/*/status
adb shell cat /sys/kernel/debug/rproc/*/state

# Dump IPA statistics
adb shell cat /sys/kernel/debug/ipa/ipa_stats

# Camera IOMMU fault analysis
adb shell dmesg | grep -E "cam_smmu|iommu_map|page fault"

# WLAN driver version
adb shell cat /sys/module/qca_cld3_wlan/version

# Audit KMI compliance for a module
bash skills/L3-qualcomm-kernel-expert/scripts/check_qcom_kmi_symbols.sh \
    out/target/product/kalama/vendor/lib/modules/qca_cld3_wlan.ko
```

---

*Qualcomm Kernel Architecture Reference v1.0.0 — Part of the L3-qualcomm-kernel-expert skill. Covers GKI 5.10 through 6.12, SM8350 (lahaina) through SM8750 (sun).*

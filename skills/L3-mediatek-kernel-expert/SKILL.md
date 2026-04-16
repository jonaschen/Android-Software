---
name: mediatek-kernel-expert
layer: L3
path_scope: vendor/mediatek/kernel_modules/, vendor/mediatek/proprietary/, device/mediatek/, kernel/mediatek/
version: 1.0.0
android_version_tested: Android 16 (GKI 6.12)
parent_skill: kernel-gki-expert
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `vendor/mediatek/kernel_modules/` | MediaTek out-of-tree kernel modules (connectivity, GPU, display, camera, audio) |
| `vendor/mediatek/kernel_modules/connectivity/` | CONNSYS / WMT driver (unified Wi-Fi + Bluetooth + GPS + FM combo chip) |
| `vendor/mediatek/kernel_modules/gpu/` | Mali GPU driver integration layer (MTK-specific DVFS, power) |
| `vendor/mediatek/kernel_modules/mtk_cam/` | MTK Camera ISP drivers (Pass-1 sensor, Pass-2 post-processing) |
| `vendor/mediatek/kernel_modules/mtk_audio/` | MTK audio platform, SCP-based audio DSP interface |
| `vendor/mediatek/kernel_modules/mtk_disp/` | MDP/MML (Media Data Path / Media ML) display modules |
| `vendor/mediatek/kernel_modules/sspm/` | SSPM (System-Side Processor Module) firmware loader |
| `vendor/mediatek/kernel_modules/scp/` | SCP (System Companion Processor) — audio + sensor DSP |
| `vendor/mediatek/kernel_modules/mtk_emi/` | EMI (External Memory Interface) protection and MPU configuration |
| `vendor/mediatek/kernel_modules/mtk_irq/` | MediaTek platform IRQ controller (IRQ/GIC integration) |
| `vendor/mediatek/proprietary/` | Binary-only blobs (TEE, modem firmware) — read-only, never modify |
| `vendor/mediatek/proprietary/tinysys/` | TINYSYS firmware artifacts (SCP/SSPM/ADSP binaries) |
| `device/mediatek/<target>/` | Device-specific BoardConfig, defconfig, DT overlays (e.g., mt6989, mt6991) |
| `device/mediatek/<target>/kernel-headers/` | SoC-specific kernel headers for vendor modules |
| `kernel/mediatek/<branch>/` | MediaTek kernel tree (pre-GKI legacy targets; A11-A13 devices) |

### Inherited Paths (from parent L2 skill: kernel-gki-expert)

This L3 skill **extends** `kernel-gki-expert`. The parent skill handles standard AOSP/GKI paths.
MediaTek deviations from the standard AOSP kernel model are documented here.

| Parent L2 Path | L3 Override / Extension |
|----------------|------------------------|
| `kernel/` | MTK also uses `kernel/mediatek/<branch>/` for non-GKI targets and `vendor/mediatek/kernel_modules/` for GKI out-of-tree modules |
| `drivers/` | MTK out-of-tree drivers live in `vendor/mediatek/kernel_modules/` — not inside `kernel/drivers/` |
| `common/` | Dimensity devices on GKI 6.12 use the `android15-6.6` branch; older D9000 uses `android13-5.15` |
| `device/<OEM>/` | MTK target names follow `<MT-part-number>` convention (e.g., `mt6983`, `mt6985`, `mt6989`, `mt6991`) |

---

## Trigger Conditions

Load this skill (after `kernel-gki-expert`) when the task involves:
- MediaTek-specific kernel module build failure in `vendor/mediatek/kernel_modules/`
- CONNSYS / WMT combo-chip driver errors (Wi-Fi/BT/GPS unified stack)
- SCP or SSPM firmware loading failures (`/vendor/firmware/scp.img`, `/vendor/firmware/sspm*.img`)
- TINYSYS audio DSP (MTK adsp / hifi3) communication errors
- MTK Camera ISP (Pass-1/Pass-2) pipeline faults
- MDP/MML display composition errors in `vendor/mediatek/kernel_modules/mtk_disp/`
- MTK EMI/MPU memory protection violations (secure memory region errors)
- MTK Preloader (`preloader_<target>.bin`) boot failures
- Defconfig issues in `device/mediatek/<target>/` (e.g., `k6989_defconfig`)
- GKI ABI breakage caused by an MTK-specific symbol not on the allowlist
- Any path referencing `mediatek/`, `mtk_`, `mt6983`, `mt6985`, `mt6989`, `mt6991`, `Dimensity`, `Helio`

### Escalation from Parent L2

`kernel-gki-expert` should escalate to this skill when:
- The task references `vendor/mediatek/` or `device/mediatek/` paths explicitly
- The error log contains `mtk_`, `mediatek_`, `connsys_`, `wmt_`, `sspm_`, `scp_`, `mtk_cam_` module names
- The user mentions a Dimensity SoC part number (MT6983, MT6985, MT6989, MT6991) or codename
- The board uses MediaTek's Preloader boot chain (see `L2-bootloader-lk-expert` for preloader→LK handoff)

---

## Architecture Intelligence

### MediaTek GKI Module Organization

MediaTek ships kernel drivers as **out-of-tree modules** consolidated under `vendor/mediatek/kernel_modules/`. Unlike Qualcomm's split across multiple open-source repos, MTK keeps most modules inside a single vendor subtree.

```
GKI Kernel (vmlinux — Google signed)
│
├── vendor/mediatek/kernel_modules/connectivity/    ← CONNSYS / WMT
│     wlan/               — Wi-Fi driver (MT66xx chip family)
│     bt/                 — Bluetooth HCI driver
│     gps/                — GNSS driver
│     fm/                 — FM radio driver
│     common/             — WMT (Wireless Management Task) transport layer
│
├── vendor/mediatek/kernel_modules/mtk_cam/         ← Camera ISP
│     mtk-isp/            — Pass-1 (sensor input) and Pass-2 (post-processing)
│     seninf/             — Sensor interface (MIPI CSI-2)
│     imgsys/             — Image System top-level (DIP, MDP, WPE)
│     camsys/             — Camera System framework (v4l2-async integration)
│
├── vendor/mediatek/kernel_modules/mtk_audio/       ← Audio platform
│     audio_scp/          — SCP-hosted audio DSP interface
│     audio_smart_pa/     — Smart amplifier driver (Goodix, NXP TFA98xx)
│     asoc/               — ALSA SoC machine drivers
│
├── vendor/mediatek/kernel_modules/mtk_disp/        ← Display / composition
│     mml/                — Media ML (image signal processing pipeline)
│     mdp/                — Media Data Path (2D compositing)
│     disp_aal/           — Adaptive ambient light (display backlight modulation)
│     dsi/                — MIPI DSI controller
│
├── vendor/mediatek/kernel_modules/sspm/            ← SSPM firmware loader
│     sspm_v1/            — SSPM (System-Side Processor Module) driver
│
├── vendor/mediatek/kernel_modules/scp/             ← SCP firmware loader
│     scp/                — SCP (System Companion Processor) driver
│
└── vendor/mediatek/kernel_modules/gpu/             ← Mali GPU integration
      gpu_mali/           — ARM Mali driver + MTK DVFS / GED (GPU Energy Dispatcher)
      ged/                — GPU Energy Dispatcher (MTK-specific frequency governor)
```

### MediaTek Kernel vs GKI Kernel

| Aspect | MediaTek Kernel (`kernel/mediatek/<branch>/`) | GKI Kernel (`common/`) |
|--------|------------------------------------------------|------------------------|
| Scope | MTK-internal, SoC-specific | AOSP standard, Google-managed |
| Drivers | In-tree under `drivers/misc/mediatek/` | Out-of-tree in `vendor/mediatek/kernel_modules/` |
| ABI | No KMI guarantee | KMI enforced (GKI ABI stability) |
| Android target | A10–A13 legacy devices | A13+ GKI-compliant devices |
| Signing | OEM-signed vmlinux | Google-signed vmlinux |
| Defconfig | `k<mtkpart>_defconfig` (e.g., `k6983_defconfig`) | `gki_defconfig` + SoC fragments |

**Rule of thumb**: If the device ships with Android 13+ and Dimensity 9000 (MT6983) or newer, it uses GKI. Older Helio G-series and early Dimensity devices may still use the MediaTek kernel.

### MediaTek SoC Part Number → GKI Kernel Mapping

| Commercial Name | MTK Part # | Codename | GKI Branch | Android Target |
|-----------------|-----------|----------|-----------|---------------|
| Dimensity 9000 | MT6983 | - | android13-5.15 | A13 |
| Dimensity 9200 | MT6985 | - | android14-5.15 | A14 |
| Dimensity 9300 | MT6989 | - | android14-6.1 | A15 |
| Dimensity 9400 | MT6991 | - | android15-6.6 | A16 |
| Dimensity 8300 | MT6897 | - | android14-6.1 | A15 |
| Dimensity 8200 | MT6895 | - | android13-5.15 | A13–A14 |
| Dimensity 7200 | MT6886 | - | android13-5.15 | A13–A14 |

> **Check device codename at runtime:** `adb shell getprop ro.vendor.mtk_platform` (e.g., `MT6989`)
> **Check SoC ID:** `adb shell cat /proc/device-tree/chosen/atag,mtk_serial`

### TINYSYS Architecture (SCP / SSPM / ADSP)

MediaTek's **TINYSYS** is the umbrella name for small auxiliary processors embedded in the SoC. Each is loaded at boot by a dedicated kernel driver:

```
Linux Kernel (GKI)
│
├── vendor/mediatek/kernel_modules/sspm/
│   └── SSPM (System-Side Processor Module, Cortex-M4)
│       └── Loads: /vendor/firmware/sspm.img
│       └── Responsibilities: DVFS governance, thermal management, power arbitration
│
├── vendor/mediatek/kernel_modules/scp/
│   └── SCP (System Companion Processor, Cortex-M4 / M33)
│       └── Loads: /vendor/firmware/scp.img
│       └── Responsibilities: sensor hub, low-power audio, always-on sensing
│
└── vendor/mediatek/kernel_modules/adsp/ (HiFi3/HiFi4 DSP)
    └── Loads: /vendor/firmware/audio_dsp.img
    └── Responsibilities: audio codec offload, voice wake word
```

**Firmware load path:**
```
Boot → kernel platform driver probes SSPM / SCP / ADSP
     → request_firmware_nowait("sspm.img")
     → MTK TEE (GenieZone or trustonic) authenticates image via ATF BL31
     → Firmware mapped into TINYSYS SRAM via SMC call
     → IPI (Inter-Processor Interrupt) channel established
     → Userspace /dev/scp, /dev/sspm interfaces become available
```

When TINYSYS crashes: check `/sys/class/mtk_scp/*/state`, `/sys/class/remoteproc/*/state`, and `dmesg | grep -iE "scp|sspm|tinysys|ipi"`.

### MediaTek Preloader → LK → Kernel Boot Chain

Unlike Qualcomm's XBL→ABL two-stage model, MediaTek uses a three-stage chain:

```
BROM (ROM Code)
  ↓ loads
Preloader (preloader_<target>.bin)
  — MTK-proprietary, lives in `boot0` hardware partition
  — Initializes DRAM, loads LK
  ↓
LK (bootloader/lk/) — MTK-customized little-kernel
  — Handles fastboot, verified boot (AVB)
  — Loads boot.img / init_boot.img + kernel
  ↓
Linux Kernel (GKI vmlinux)
  — Loads vendor modules from vendor_boot.img
```

**Key difference from Qualcomm**: Fastboot commands hit **LK** (not ABL). The preloader is NOT user-visible — it executes before USB enumeration.

### MTK EMI / MPU (Memory Protection Unit)

MediaTek SoCs use a proprietary **EMI MPU** to carve the physical DRAM into secure regions for:
- TEE (Trusted Execution Environment)
- Modem firmware
- TINYSYS (SCP/SSPM/ADSP)
- Protected content (Widevine L1)

Violating EMI MPU triggers a hardware fault visible as:
```
[  123.456] emi_mpu: Permission violation at address 0x<addr>
[  123.457] emi_mpu: master_id=<id>, domain=<sec|nwd>
```

Driver: `vendor/mediatek/kernel_modules/mtk_emi/`

### KMI Symbol Compliance for MTK Modules

MediaTek vendor modules must use only symbols on the GKI ABI allowlist (`android/abi_gki_aarch64.xml`). Common MTK-specific violations:

| Symbol | Module | Issue |
|--------|--------|-------|
| `mtk_devinfo_get` | mtk_cam | Custom device info API — replaced by DT-based queries |
| `emi_mpu_set_protection` | mtk_emi | Must use SMC call to ATF BL31 instead of direct register |
| `scp_ipi_send` | scp | Use allowlisted IPI framework APIs only |
| `mtk_ccci_*` | CCCI (cellular comms) | Modem-only; not suitable for cross-domain |
| `mtk_ion_*` | Legacy ION | Must migrate to DMA-BUF heaps for GKI |

Use `scripts/check_mtk_kmi_symbols.sh <module.ko>` to audit a module's symbol dependencies.

---

## Forbidden Actions

> **Inherited from `kernel-gki-expert`**: Do not modify `android/abi_gki_aarch64.xml` without ABI review, do not link modules against non-KMI symbols, do not bypass `modpost` checks.

In addition, for MediaTek-specific work:

1. **Do NOT modify `vendor/mediatek/proprietary/`** — these are pre-built binaries signed by MediaTek / the OEM. Modification voids signing, causes boot failures.
2. **Do NOT modify the Preloader (`preloader_<target>.bin`)** — the preloader executes before USB and is signed by MTK BROM. Tampering bricks the device and usually requires SP Flash Tool DA (Download Agent) recovery.
3. **Do NOT assume `drivers/misc/mediatek/` paths in GKI kernels** — in-tree `drivers/misc/mediatek/*` exists only inside `kernel/mediatek/<branch>/`. GKI targets use `vendor/mediatek/kernel_modules/` instead.
4. **Do NOT use MTK-internal defconfig targets on GKI builds** — always use `gki_defconfig` plus SoC-specific config fragments (e.g., `k6989_GKI.config`). Do not use `k6989_defconfig` on a GKI device.
5. **Do NOT link MTK camera/audio/display modules against non-KMI symbols** — modules built for GKI must not call `mtk_devinfo_get`, `emi_mpu_set_protection`, or any non-allowlisted MTK internal APIs.
6. **Do NOT modify TINYSYS firmware images** (`scp.img`, `sspm.img`, `audio_dsp.img`) — they are signed and verified by MTK TEE. Tampering breaks secure boot of the DSP subsystems.
7. **Do NOT conflate MTK kernel paths with GKI paths** — if the device uses GKI, camera drivers are in `vendor/mediatek/kernel_modules/mtk_cam/`, NOT in `kernel/mediatek/<branch>/drivers/misc/mediatek/cam/`.
8. **Do NOT route MTK Preloader boot issues to this skill** — preloader-stage problems belong in `L2-bootloader-lk-expert`. This skill starts from LK handoff onward.
9. **Do NOT assume MTK connectivity (CONNSYS/WMT) drivers are independent** — Wi-Fi, Bluetooth, GNSS, and FM share a single combo chip and a unified WMT transport. Disabling one typically affects the others.

---

## Tool Calls

### Audit MTK Module KMI Symbol Dependencies

```bash
bash skills/L3-mediatek-kernel-expert/scripts/check_mtk_kmi_symbols.sh <path/to/module.ko>
```

**What it does:** Extracts undefined symbols from the module, cross-references against `android/abi_gki_aarch64.xml`, and reports any symbols not on the allowlist. Non-allowlisted symbols will cause module load failure on GKI.

**Input:** Path to a compiled `.ko` file.
**Output:** List of allowed symbols, non-allowed symbols, and a PASS/FAIL verdict.

### Identify Device SoC Part Number

```bash
# From a running device
adb shell getprop ro.vendor.mtk_platform       # e.g., "MT6989"
adb shell getprop ro.hardware                  # e.g., "mt6989"
adb shell cat /proc/device-tree/model          # e.g., "MediaTek MT6989 Dimensity 9300"

# From source
grep "TARGET_BOARD_PLATFORM" device/mediatek/<target>/BoardConfig.mk
```

### Check TINYSYS (SCP/SSPM/ADSP) Crash

```bash
adb shell cat /sys/class/mtk_scp/*/state
adb shell cat /sys/class/remoteproc/*/state
adb shell dmesg | grep -iE "scp|sspm|tinysys|ipi|adsp"
adb shell ls /sys/kernel/debug/scp/   # SCP debugfs traces
```

### Verify CONNSYS/WMT Combo Chip Status

```bash
adb shell cat /proc/driver/wmt_dev/state       # WMT state machine
adb shell cat /proc/driver/wmt_aee              # WMT AEE (Android Exception Engine) dump
adb shell dmesg | grep -iE "wmt|connsys|connac|mt66"
```

### Verify EMI/MPU Violations

```bash
adb shell dmesg | grep -iE "emi_mpu|permission violation|master_id" | tail -40
```

---

## Handoff Rules

| Condition | Route To |
|-----------|---------|
| Issue is in generic GKI paths (`kernel/`, `common/`, `drivers/`) without MTK specifics | Hand back to `L2-kernel-gki-expert` |
| Issue involves MTK Preloader (before LK executes) or LK itself | Hand to `L2-bootloader-lk-expert` |
| Issue involves MediaTek TEE (GenieZone, trustonic) or MTK BL31 | Hand to `L2-trusted-firmware-atf-expert` |
| Issue involves `vendor/mediatek/kernel_modules/mtk_audio/` and the ALSA/audio HAL layer above it | Hand to `L2-multimedia-audio-expert` |
| Issue involves `vendor/mediatek/` HAL AIDL implementations (non-kernel) | Hand to `L2-hal-vendor-interface-expert` |
| Issue involves MediaTek SELinux denials for `mtk_` services | Hand to `L2-security-selinux-expert` |
| Issue involves A15→A16 kernel API migration for MTK modules | Hand to `L2-version-migration-expert` (after confirming MTK-specific scope with this skill) |
| Issue involves Qualcomm (not MediaTek) kernel modules | Hand to `L3-qualcomm-kernel-expert` |

---

## References

- `skills/L2-kernel-gki-expert/SKILL.md` — Parent skill; read first for generic GKI guidance
- `skills/L3-mediatek-kernel-expert/references/mediatek_kernel_architecture.md` — Deep dive: SoC part numbers, module organization, TINYSYS internals
- `skills/L3-mediatek-kernel-expert/scripts/check_mtk_kmi_symbols.sh` — KMI symbol audit tool
- `references/16kb_page_migration_guide.md` — 16KB page size migration (applies to all MTK A16 targets)
- `memory/hindsight_notes/HS-033_gki_6_12_eevdf_vma_proxy_exec.md` — GKI 6.12 changes including EEVDF scheduler and `vm_flags` proxy exec removal
- `memory/hindsight_notes/HS-044_mediatek_kernel_modules_routing_gap.md` — MTK kernel module routing gap analog to HS-042
- MediaTek Open Source portal: `gitea.mediatek.com` (public portions)
- Android GKI ABI: `kernel/common/android/abi_gki_aarch64.xml`

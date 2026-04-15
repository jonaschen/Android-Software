---
name: qualcomm-kernel-expert
layer: L3
path_scope: vendor/qcom/opensource/, device/qcom/, kernel/msm-*/
version: 1.0.0
android_version_tested: Android 16 (GKI 6.12)
parent_skill: kernel-gki-expert
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `vendor/qcom/opensource/` | Qualcomm open-source kernel modules (camera, audio, wlan, data, video) |
| `vendor/qcom/opensource/camera-kernel/` | Camera kernel drivers (IFE, IPE, IOMMU, CCI) |
| `vendor/qcom/opensource/audio-kernel/` | Audio DSP interface modules (ADSP RPC, codec, platform) |
| `vendor/qcom/opensource/wlan/` | WLAN driver — qcacld-3.0 (CLD/WCN chips) |
| `vendor/qcom/opensource/dataipa/` | Data IPA (Inline Packet Accelerator) kernel driver |
| `vendor/qcom/opensource/video-driver/` | Video codec (Venus) kernel module |
| `vendor/qcom/opensource/mmrm-driver/` | Multimedia Resource Manager kernel driver |
| `device/qcom/<target>/` | Device-specific BoardConfig, defconfigs, DT overlays |
| `device/qcom/<target>/kernel-headers/` | SoC-specific kernel headers for vendor modules |
| `kernel/msm-<version>/` | Qualcomm MSM kernel fork (non-GKI legacy) |
| `kernel/msm-<version>/techpack/` | SoC-specific driver pack within the MSM kernel |
| `kernel/msm-<version>/techpack/camera/` | Camera techpack drivers (within MSM kernel only) |
| `kernel/msm-<version>/techpack/audio/` | Audio techpack (Q6ASM, AFE, ADM) in MSM kernel |
| `vendor/qcom/proprietary/` | Binary-only blobs — read-only, never modify |

### Inherited Paths (from parent L2 skill: kernel-gki-expert)

This L3 skill **extends** `kernel-gki-expert`. The parent skill handles standard AOSP/GKI paths.
Qualcomm deviations from the standard AOSP kernel model are documented here.

| Parent L2 Path | L3 Override / Extension |
|----------------|------------------------|
| `kernel/` | QC also uses `kernel/msm-<version>/` for non-GKI targets and `vendor/qcom/opensource/*/` for GKI out-of-tree modules |
| `drivers/` | QC out-of-tree drivers live in `vendor/qcom/opensource/` — not inside `kernel/drivers/` |
| `common/` | Snapdragon devices on GKI 6.12 use the `android14-6.1` or `android15-6.6` branch; confirm via `msm_show_epoch` |
| `device/<OEM>/` | QC target names follow `<SoC-codename>` convention (e.g., `lahaina`, `taro`, `kalama`, `sun`) |

---

## Trigger Conditions

Load this skill (after `kernel-gki-expert`) when the task involves:
- Qualcomm-specific kernel module build failure in `vendor/qcom/opensource/`
- `techpack/` driver errors within `kernel/msm-*/`
- qcacld-3.0 WLAN module KMI symbol or signing issues
- ADSP/CDSP firmware loading failures (`/vendor/firmware/adsp*.mbn`)
- Qualcomm IOMMU or SMMU mapping faults in camera or video pipeline
- QC Board DT overlay (`device/qcom/<target>/*.dtsi`) merge conflicts
- `BoardConfig.mk` kernel config fragments for Snapdragon targets
- Qualcomm Inline Packet Accelerator (IPA) driver integration
- `modinfo` showing wrong `vermagic` for a QC vendor module
- GKI ABI breakage caused by a QC-specific symbol not on the allowlist
- Any path referencing `qcom/`, `msm`, `lahaina`, `taro`, `kalama`, `sun`, `crow`, `pineapple`

### Escalation from Parent L2

`kernel-gki-expert` should escalate to this skill when:
- The task references `vendor/qcom/` or `device/qcom/` paths explicitly
- The error log contains `qcom_`, `msm_`, `lpass_`, `cam_ife_`, `qcacld` module names
- The user mentions a Snapdragon SoC codename (lahaina, taro, kalama, sun, pineapple, crow)
- The board uses Qualcomm's ABL/XBL boot chain (see `L3-qualcomm-boot-expert` for deeper boot analysis)

---

## Architecture Intelligence

### Qualcomm GKI Module Organization

Qualcomm ships kernel drivers as **out-of-tree modules** in separate Git repositories, not inside the `kernel/` tree. This is a fundamental deviation from the AOSP reference model.

```
GKI Kernel (vmlinux — Google signed)
│
├── vendor/qcom/opensource/camera-kernel/    ← Camera IFE/IPE/CCI modules
│     drivers/cam_core/        — Core camera framework
│     drivers/cam_isp/         — Image Signal Processor (IFE, ICP)
│     drivers/cam_sensor_module/ — Sensor, actuator, OIS, flash
│     drivers/cam_iommu/       — IOMMU/SMMU mapping for camera
│
├── vendor/qcom/opensource/audio-kernel/     ← Audio DSP modules
│     asoc/                    — ALSA SoC platform drivers
│     dsp/                     — Q6ASM/AFE/ADM ADSP interface
│     soc/                     — SoC audio codec drivers
│
├── vendor/qcom/opensource/wlan/             ← WLAN (qcacld-3.0)
│     qcacld-3.0/              — WCN685x/WCN7850 unified driver
│
├── vendor/qcom/opensource/dataipa/          ← IPA packet accelerator
│     drivers/platform/msm/ipa/ — IPA core driver
│
└── vendor/qcom/opensource/video-driver/     ← Venus video codec
      drivers/media/platform/msm/vidc/ — V4L2 video codec driver
```

### MSM Kernel vs GKI Kernel

| Aspect | MSM Kernel (`kernel/msm-<ver>/`) | GKI Kernel (`common/`) |
|--------|----------------------------------|------------------------|
| Scope | Qualcomm-internal, SoC-specific | AOSP standard, Google-managed |
| Drivers | `techpack/camera`, `techpack/audio` in-tree | Out-of-tree in `vendor/qcom/opensource/` |
| ABI | No KMI guarantee | KMI enforced (GKI ABI stability) |
| Android target | A10–A13 legacy devices | A13+ GKI-compliant devices |
| Signing | OEM-signed vmlinux | Google-signed vmlinux |
| Defconfig | `vendor/lahaina_GKI.config` | `gki_defconfig` + SoC fragments |

**Rule of thumb**: If the device ships with Android 13+ and Snapdragon 8 Gen 1 or newer, it uses GKI. Older Snapdragon 855/865/888 devices may still use the MSM kernel.

### Qualcomm SoC Codename → GKI Kernel Mapping

| SoC | Codename | GKI Branch | Android Target |
|-----|----------|-----------|---------------|
| Snapdragon 8 Gen 1 | Lahaina (SM8450) | android13-5.10 | A13 |
| Snapdragon 8 Gen 2 | Taro (SM8550) | android14-5.15 | A14 |
| Snapdragon 8 Gen 3 | Kalama (SM8650) | android14-6.1 | A15 |
| Snapdragon 8 Elite | Sun (SM8750) | android15-6.6 | A16 |
| Snapdragon 8s Gen 4 | Crow (SM7675) | android15-6.6 | A16 |
| Snapdragon X Elite | Hamoa (SC8380XP) | android15-6.6 | A16 (PC) |

### ADSP / CDSP Firmware Loading

Qualcomm DSPs use a firmware loading model absent in standard AOSP:

```
Boot → PIL (Peripheral Image Loader) → /vendor/firmware/adsp.mbn
                                       /vendor/firmware/cdsp.mbn
                                       /vendor/firmware/slpi.mbn
     → remoteproc framework loads firmware into DSP IOVA
     → FastRPC creates /dev/fastrpc-adsp, /dev/fastrpc-cdsp
     → HAL layer (libadsprpc.so) communicates via FastRPC
```

When ADSP crashes: check `/sys/bus/platform/drivers/qcom-pil/*/status` and `dmesg | grep -i "adsp\|pil\|remoteproc"`.

### Qualcomm IOMMU / SMMU in Camera Pipeline

Camera module failures often involve IOMMU faults (`cam_smmu`). The standard AOSP `iommu` driver does not apply here.

```
Camera HAL (AIDL v3)
    │
    ▼ ioctl() → /dev/video*
cam_req_mgr (camera kernel framework)
    │
    ├── cam_isp (IFE — Image Front End)
    ├── cam_icp (IPE — Image Processing Engine)
    └── cam_smmu (cam_iommu — custom SMMU wrapper)
              │
              ▼
         ARM SMMU-500 hardware
```

Error pattern: `cam_smmu: ERROR: iommu page fault addr <addr>` — usually a buffer not mapped before DMA.

### KMI Symbol Compliance for QC Modules

Qualcomm vendor modules must use only symbols on the GKI ABI allowlist (`android/abi_gki_aarch64.xml`). Common QC-specific violations:

| Symbol | Module | Issue |
|--------|--------|-------|
| `qcom_smem_get` | qca-wifi | Must use SMEM API via allowlisted wrapper |
| `msm_bus_*` | audio-kernel | Legacy bus API — replaced by ICC framework |
| `subsystem_get` | camera-kernel | Replaced by remoteproc API in GKI |

Use `scripts/check_qcom_kmi_symbols.sh <module.ko>` to audit a module's symbol dependencies.

---

## Forbidden Actions

> **Inherited from `kernel-gki-expert`**: Do not modify `android/abi_gki_aarch64.xml` without ABI review, do not link modules against non-KMI symbols, do not bypass `modpost` checks.

In addition, for Qualcomm-specific work:

1. **Do NOT modify `vendor/qcom/proprietary/`** — these are pre-built binaries signed by Qualcomm. Modification voids signing, causes boot failures.
2. **Do NOT assume `techpack/` paths in GKI kernels** — `techpack/camera` and `techpack/audio` exist only inside `kernel/msm-<version>/`. GKI targets use `vendor/qcom/opensource/` instead.
3. **Do NOT use QC-internal defconfig targets on GKI builds** — always use `gki_defconfig` plus SoC-specific config fragments (e.g., `vendor/kalama_GKI.config`). Do not use `msm8996_defconfig` on a GKI device.
4. **Do NOT link QC camera/audio modules against non-KMI symbols** — modules built for GKI must not call `msm_bus_*`, `subsystem_get`, or any non-allowlisted QC internal APIs.
5. **Do NOT modify Qualcomm firmware images** (`.mbn`, `.elf`, `.fv` files in `vendor/qcom/firmware/`) — they are signed and verified by PIL. Tampering breaks secure boot.
6. **Do NOT conflate MSM kernel paths with GKI paths** — if the device uses GKI, camera drivers are in `vendor/qcom/opensource/camera-kernel/`, NOT in `kernel/msm-<ver>/techpack/camera/`.
7. **Do NOT assume qcacld-3.0 WLAN module works with all GKI kernel versions** — check `WCN_CHIP_VERSION` in `qcacld-3.0/Kconfig` against the target GKI branch; there are chip-specific compatibility gates.
8. **Do NOT route Qualcomm ABL/XBL bootloader questions to this skill** — boot chain issues belong in `L2-bootloader-lk-expert` (and optionally `L3-qualcomm-boot-expert` when created).

---

## Tool Calls

### Audit QC Module KMI Symbol Dependencies

```bash
bash skills/L3-qualcomm-kernel-expert/scripts/check_qcom_kmi_symbols.sh <path/to/module.ko>
```

**What it does:** Extracts undefined symbols from the module, cross-references against `android/abi_gki_aarch64.xml`, and reports any symbols not on the allowlist. Non-allowlisted symbols will cause module load failure on GKI.

**Input:** Path to a compiled `.ko` file.
**Output:** List of allowed symbols, non-allowed symbols, and a PASS/FAIL verdict.

### Identify Device SoC Codename

```bash
# From a running device
adb shell getprop ro.board.platform          # e.g., "kalama"
adb shell getprop ro.product.board           # e.g., "kalama"
adb shell cat /sys/devices/soc0/soc_id       # Numeric SoC ID

# From source
grep "TARGET_BOARD_PLATFORM" device/qcom/<target>/BoardConfig.mk
```

### Check ADSP/CDSP Crash

```bash
adb shell cat /sys/bus/platform/drivers/qcom-pil/*/status
adb shell dmesg | grep -E "adsp|cdsp|pil|remoteproc|subsys"
adb logcat -s ADSPRPC,aDSPd,fastrpc
```

### Verify Camera IOMMU Faults

```bash
adb shell dmesg | grep -E "cam_smmu|iommu|smmu|page fault" | tail -40
```

---

## Handoff Rules

| Condition | Route To |
|-----------|---------|
| Issue is in generic GKI paths (`kernel/`, `common/`, `drivers/`) without QC specifics | Hand back to `L2-kernel-gki-expert` |
| Issue involves Qualcomm ABL (Android Bootloader) or XBL (eXtensible Bootloader) | Hand to `L2-bootloader-lk-expert` |
| Issue involves Qualcomm TrustZone / QSEECOM | Hand to `L2-trusted-firmware-atf-expert` |
| Issue involves `vendor/qcom/opensource/audio-kernel/` and ALSA/HAL layer above it | Hand to `L2-multimedia-audio-expert` |
| Issue involves `vendor/qcom/` HAL AIDL implementations (non-kernel) | Hand to `L2-hal-vendor-interface-expert` |
| Issue involves Qualcomm SELinux denials for `qcom_` services | Hand to `L2-security-selinux-expert` |
| Issue involves A15→A16 kernel API migration for QC modules | Hand to `L2-version-migration-expert` (after confirming QC-specific scope with this skill) |

---

## References

- `skills/L2-kernel-gki-expert/SKILL.md` — Parent skill; read first for generic GKI guidance
- `skills/L3-qualcomm-kernel-expert/references/qualcomm_kernel_architecture.md` — Deep dive: SoC codenames, module organization, ADSP/PIL internals
- `skills/L3-qualcomm-kernel-expert/scripts/check_qcom_kmi_symbols.sh` — KMI symbol audit tool
- `references/16kb_page_migration_guide.md` — 16KB page size migration (applies to all QC A16 targets)
- `memory/hindsight_notes/HS-033_gki_6_12_eevdf_vma_proxy_exec.md` — GKI 6.12 changes including EEVDF scheduler and `vm_flags` proxy exec removal
- Qualcomm Open Source portal: `codeaurora.org` (mirror: `git.codelinaro.org`)
- Android GKI ABI: `kernel/common/android/abi_gki_aarch64.xml`

# HS-042: Qualcomm Out-of-Tree Kernel Module Architecture

**Domain:** L3-qualcomm-kernel-expert → L2-kernel-gki-expert
**Created:** 2026-04-16
**Phase:** 6.1 (L3 OEM skill creation)

---

## Core Insight

Qualcomm ships critical kernel functionality (camera, audio DSP, WLAN, IPA, video) as **out-of-tree modules in `vendor/qcom/opensource/`**, not inside `kernel/drivers/`. This is a fundamental deviation from both standard AOSP (`kernel/drivers/`) and the L2 router's assumption that `vendor/` paths → HAL layer.

The practical consequence: when routing a Qualcomm kernel module issue, the L2 router will dispatch to `L2-hal-vendor-interface-expert` (because of the `vendor/` path prefix), but the actual expertise needed is kernel-level (KMI compliance, SMMU/IOMMU, remoteproc/PIL, DMA-BUF). This creates a routing gap that L3 skills are designed to bridge.

---

## Affected Paths

```
vendor/qcom/opensource/camera-kernel/   ← kernel modules (not HAL)
vendor/qcom/opensource/audio-kernel/    ← ADSP interface modules (not HAL)
vendor/qcom/opensource/wlan/qcacld-3.0/ ← WLAN kernel driver (not HAL)
vendor/qcom/opensource/dataipa/         ← IPA kernel driver (not HAL)
vendor/qcom/opensource/video-driver/    ← Venus V4L2 kernel driver (not HAL)
kernel/msm-<version>/techpack/          ← in-tree SoC drivers (MSM kernel only)
```

---

## Why the Confusion Exists

1. **Path prefix overlap**: `vendor/` conventionally means "vendor HAL / blobs" in AOSP, but Qualcomm reuses this prefix for kernel source code.
2. **No GKI in-tree**: GKI prohibits vendor-specific code in `kernel/drivers/`. QC must ship out-of-tree. `vendor/qcom/opensource/` is the sanctioned location.
3. **MSM kernel heritage**: Older Qualcomm devices (pre-A13) used `kernel/msm-<version>/techpack/` — in-tree. GKI transition moved these to `vendor/qcom/opensource/`.

---

## Routing Rule for L3-aware Systems

| Path Pattern | Correct Expert | Reason |
|-------------|---------------|--------|
| `vendor/qcom/opensource/*/drivers/` | L3-qualcomm-kernel-expert | Kernel module source code |
| `vendor/qcom/opensource/*/Kbuild` | L3-qualcomm-kernel-expert | Kernel build artifact |
| `vendor/qcom/proprietary/` | L2-hal-vendor-interface-expert | Binary blobs, HAL implementations |
| `vendor/qcom/interfaces/` | L2-hal-vendor-interface-expert | AIDL HAL definitions |
| `kernel/msm-<ver>/techpack/` | L3-qualcomm-kernel-expert | In-tree SoC driver pack |

**Trigger signal for L3 escalation from L2-hal-vendor-interface-expert:**
- Module file extension in path: `.ko`, `Kbuild`, `Kconfig`, `.c` + `drivers/` subdir
- Error messages: `Unknown symbol in module`, `KMI`, `abi_gki`, `SMMU`, `cam_smmu`, `remoteproc`
- Tool: `check_qcom_kmi_symbols.sh` — confirms kernel module scope

---

## Phase 6.1 Deliverables Created

- `skills/L3-qualcomm-kernel-expert/SKILL.md` — Full L3 skill with 8 forbidden actions
- `skills/L3-qualcomm-kernel-expert/scripts/check_qcom_kmi_symbols.sh` — KMI audit tool
- `skills/L3-qualcomm-kernel-expert/references/qualcomm_kernel_architecture.md` — SoC codename table, module org, PIL lifecycle, 16KB impact
- `tests/routing_accuracy/test_router.py` — TC-101–TC-105 documenting L2→L3 escalation pattern
- `memory/dirty_pages.json` — L3-qualcomm-kernel-expert registered (status: clean, Android 16)

---

## Key Technical Facts to Remember

1. **SoC → GKI branch**: SM8750 (sun/8 Elite) → `android15-6.6`. SM8650 (crow/8 Gen 3) → `android14-6.1`. SM8550 (taro/8 Gen 2) → `android14-5.15`.
2. **ADSP crash analysis**: Check `/sys/kernel/debug/rproc/*/trace0` — this is the ADSP crash log, not `dmesg`.
3. **ION is gone in A16**: `ion_alloc()` was removed. QC video/camera modules must use `dma_heap_buffer_alloc()`.
4. **cam_smmu ≠ AOSP iommu**: QC has its own SMMU wrapper (`cam_iommu.ko`) — generic AOSP IOMMU docs don't apply.
5. **qcacld-3.0 is GKI 6.12 compatible**: WCN7850 (Wi-Fi 7) shipped on SM8750 with android15-6.6 GKI.

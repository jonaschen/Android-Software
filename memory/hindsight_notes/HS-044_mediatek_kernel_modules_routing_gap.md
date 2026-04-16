# HS-044: MediaTek Out-of-Tree Kernel Module Architecture

**Domain:** L3-mediatek-kernel-expert → L2-kernel-gki-expert
**Created:** 2026-04-17
**Phase:** 6.2 (L3 OEM skill creation)
**Related:** HS-042 (analogous Qualcomm pattern)

---

## Core Insight

MediaTek ships critical kernel functionality (camera ISP, CONNSYS combo chip, display composition, TINYSYS loaders) as **out-of-tree modules in `vendor/mediatek/kernel_modules/`**, not inside `kernel/drivers/`. This is the same architectural pattern as Qualcomm (HS-042) but using a **single consolidated tree** rather than QC's split-repository model under `vendor/qcom/opensource/`.

The practical consequence is identical to HS-042: when routing a MediaTek kernel module issue, the L2 router will dispatch to `L2-hal-vendor-interface-expert` (because of the `vendor/` path prefix), but the actual expertise needed is kernel-level (KMI compliance, EMI MPU, SCP/SSPM firmware loading, MTK IOMMU, DMA-BUF). This creates a routing gap that the new L3-mediatek-kernel-expert skill is designed to bridge.

---

## Affected Paths

```
vendor/mediatek/kernel_modules/connectivity/   ← CONNSYS/WMT kernel drivers (not HAL)
vendor/mediatek/kernel_modules/mtk_cam/        ← Camera ISP kernel drivers (not HAL)
vendor/mediatek/kernel_modules/mtk_audio/      ← Audio platform + smart PA drivers (not HAL)
vendor/mediatek/kernel_modules/mtk_disp/       ← Display / MDP / MML kernel drivers (not HAL)
vendor/mediatek/kernel_modules/scp/            ← SCP firmware loader (not HAL)
vendor/mediatek/kernel_modules/sspm/           ← SSPM firmware loader (not HAL)
vendor/mediatek/kernel_modules/mtk_emi/        ← EMI MPU driver (not HAL)
vendor/mediatek/kernel_modules/gpu/            ← Mali integration + GED driver (not HAL)
kernel/mediatek/<branch>/drivers/misc/mediatek/ ← in-tree drivers (pre-GKI legacy only)
```

---

## Why the Confusion Exists (Same Root Cause as HS-042)

1. **Path prefix overlap**: `vendor/` conventionally means "vendor HAL / blobs" in AOSP, but MediaTek reuses this prefix for kernel source code.
2. **No GKI in-tree**: GKI prohibits vendor-specific code in `kernel/drivers/`. MTK must ship out-of-tree. `vendor/mediatek/kernel_modules/` is the sanctioned location.
3. **Legacy MTK kernel heritage**: Pre-GKI MediaTek devices (A11–A12) used `kernel/mediatek/<branch>/drivers/misc/mediatek/` — in-tree. GKI transition moved these to `vendor/mediatek/kernel_modules/`.

---

## Routing Rule for L3-aware Systems

| Path Pattern | Correct Expert | Reason |
|-------------|---------------|--------|
| `vendor/mediatek/kernel_modules/` | L3-mediatek-kernel-expert | Kernel module source code |
| `vendor/mediatek/kernel_modules/*/Kbuild` | L3-mediatek-kernel-expert | Kernel build artifact |
| `vendor/mediatek/proprietary/` | L2-hal-vendor-interface-expert | Binary blobs, HAL implementations |
| `vendor/mediatek/proprietary/tinysys/` | L3-mediatek-kernel-expert | TINYSYS firmware binaries (kernel-owned lifecycle) |
| `device/mediatek/<part>/` | L3-mediatek-kernel-expert | Board config, defconfig, DT overlays |
| `kernel/mediatek/<branch>/` | L3-mediatek-kernel-expert | Pre-GKI MTK kernel tree |

**Trigger signal for L3 escalation from L2-hal-vendor-interface-expert:**
- Module file extension in path: `.ko`, `Kbuild`, `Kconfig`, `.c` + `drivers/` subdir
- Error messages: `Unknown symbol in module`, `KMI`, `abi_gki`, `mtk_iommu`, `emi_mpu`, `scp_`, `sspm_`, `wmt_`, `connsys_`
- SoC part number in log: `MT6983`, `MT6985`, `MT6989`, `MT6991`
- Tool: `check_mtk_kmi_symbols.sh` — confirms kernel module scope

---

## Phase 6.2 Deliverables Created

- `skills/L3-mediatek-kernel-expert/SKILL.md` — Full L3 skill with 9 forbidden actions
- `skills/L3-mediatek-kernel-expert/scripts/check_mtk_kmi_symbols.sh` — KMI audit tool with MTK red-flag symbol detection
- `skills/L3-mediatek-kernel-expert/references/mediatek_kernel_architecture.md` — SoC part table, module org, TINYSYS lifecycle, 16KB impact, QC↔MTK comparison table
- `tests/routing_accuracy/test_router.py` — TC-106–TC-110 documenting L2→L3 escalation pattern for MediaTek
- `memory/dirty_pages.json` — L3-mediatek-kernel-expert registered (status: clean, Android 16)

---

## Key Technical Facts to Remember (MediaTek-Specific)

1. **Part number → GKI branch**: MT6991 (D9400) → `android15-6.6`. MT6989 (D9300) → `android14-6.1`. MT6985 (D9200) → `android14-5.15`. MT6983 (D9000) → `android13-5.15`.
2. **Three-stage boot chain**: BROM → Preloader → LK → kernel. **Preloader** (`preloader_<target>.bin`) runs before USB enumeration and is MTK-proprietary; fastboot hits **LK**, not the preloader.
3. **TINYSYS crash analysis**: Check `/sys/kernel/debug/scp/scp_A_log` and `/data/aee_exp/` (AEE — Android Exception Engine) — **not** `dmesg` as the primary source.
4. **MTK ION is gone in A16**: `mtk_ion_alloc()` was removed. MTK camera/audio/display modules must use `dma_heap_buffer_alloc()` with the `mtk_mm-uncached` heap for secure memory.
5. **mtk_iommu ≠ AOSP iommu**: MTK uses its own IOMMU driver with per-master-ID fault reporting. Generic AOSP IOMMU docs don't apply. Fault decoding requires DT `iommu-port-id` mapping.
6. **CONNSYS is unified**: Wi-Fi, Bluetooth, GPS, FM share a single combo chip and WMT transport. A WMT reset tears down all four simultaneously — diagnosing one radio requires awareness of the others.
7. **EMI MPU uses SMC**: Memory protection configuration is done via SMC call to ATF BL31 (`SIP_SVC_EMI_MPU_SET`), not direct register access. Direct writes from the kernel bypass TEE enforcement and are forbidden.
8. **Two TEE choices**: GenieZone (MTK-owned, `/dev/gz_cli`) or Trustonic Kinibi (`/dev/mobicore`). The choice affects ATF BL32 dispatch and the Linux userspace TEE API.

---

## Analogy Table: Qualcomm ↔ MediaTek Equivalents

Cross-refer when debugging: if the QC answer is X, the MTK answer is usually analogous but uses different names.

| Concept | Qualcomm | MediaTek |
|---------|----------|----------|
| Out-of-tree module root | `vendor/qcom/opensource/` | `vendor/mediatek/kernel_modules/` |
| DSP loader | PIL + remoteproc | scp + sspm drivers |
| DSP firmware | `adsp.mbn`, `cdsp.mbn` | `scp.img`, `sspm.img`, `audio_dsp.img` |
| DSP userspace IPC | `/dev/fastrpc-adsp` (FastRPC) | `/dev/scp`, `/dev/sspm` (IPI) |
| Boot chain | XBL → ABL → kernel | BROM → Preloader → LK → kernel |
| Fastboot owner | ABL (`app/aboot/`) | LK (MTK-customized) |
| Wi-Fi driver | qcacld-3.0 (Wi-Fi only) | CONNSYS/WMT (unified Wi-Fi+BT+GPS+FM) |
| IOMMU | cam_smmu (custom wrapper) | mtk_iommu (per-master-ID) |
| Memory protection | Hyp stage-2 + HLOS iommu | EMI MPU (HW) + SMC to ATF |
| TEE | QSEECOM / Trusty | GenieZone / Trustonic |
| Part # format | Codename (lahaina, kalama, sun) | MT-number (mt6983, mt6989) |

---

## Phase 6 Gate Progress

Per `ROADMAP.md` Phase 6 gate: **≥ 2 concrete L3 skills deployed** (Qualcomm + MediaTek).

With this deliverable:
- ✅ Phase 6.1 — L3-qualcomm-kernel-expert (done 2026-04-16)
- ✅ Phase 6.2 — L3-mediatek-kernel-expert (done 2026-04-17)

Remaining Phase 6 work: 6.3 (AOSP A16 source-drop response — pending source drop), 6.4 (L3-aware router upgrade), 6.5 (ongoing research log).

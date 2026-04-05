# Layer 3 Extension Guide — OEM/SoC Skill Development

> **Version:** 1.0.0
> **Date:** 2026-04-06
> **Prerequisite:** Familiarity with the L1/L2 architecture in `ANDROID_SW_OWNER_DEV_PLAN.md`

---

## What Are L3 Skills?

Layer 3 skills are **plug-and-play extensions** that add OEM-specific or SoC-specific knowledge on top of existing L2 expert skills. They follow the same SKILL.md template but add a **parent-child relationship** with an L2 skill.

```
[L1] aosp-root-router
 │
 ├── [L2] kernel-gki-expert              ← Generic AOSP kernel knowledge
 │    ├── [L3] qualcomm-kernel-expert     ← Qualcomm MSM kernel specifics
 │    └── [L3] mediatek-kernel-expert     ← MediaTek kernel specifics
 │
 ├── [L2] hal-vendor-interface-expert    ← Generic HAL/AIDL/Treble knowledge
 │    ├── [L3] qualcomm-hal-expert        ← QC vendor HAL extensions
 │    └── [L3] mediatek-hal-expert        ← MTK vendor HAL extensions
 │
 └── [L2] init-boot-sequence-expert      ← Generic init/boot knowledge
      ├── [L3] qualcomm-boot-expert       ← QC ABL/XBL boot chain
      └── [L3] mediatek-boot-expert       ← MTK preloader/LK boot chain
```

### When to Create an L3 Skill

Create an L3 skill when:
- Your OEM/SoC has **proprietary paths** not present in standard AOSP
- The SoC has **different architecture** for a subsystem (e.g., Qualcomm ADSP vs generic AudioFlinger)
- You have **recurring BSP-specific questions** that the L2 skill cannot answer
- Your team has **vendor-specific tooling** (e.g., QXDM, MTK Flash Tool)

Do NOT create an L3 skill when:
- The question can be answered by the L2 skill with generic AOSP knowledge
- The OEM deviation is a one-off patch with no recurring pattern
- The information is under NDA and cannot be documented

---

## Parent-Child Relationship

### Inheritance Rules

| Aspect | Behavior |
|--------|----------|
| **Path scope** | L3 **extends** (does not replace) the parent L2 path scope with vendor-specific paths |
| **Trigger conditions** | L3 triggers are a subset — only when the task is OEM/SoC-specific |
| **Architecture intelligence** | L3 documents vendor deviations; parent L2 covers standard AOSP behavior |
| **Forbidden actions** | L3 **inherits all** parent L2 forbidden actions and adds vendor-specific ones (minimum 5 additional) |
| **Handoff rules** | L3 must hand back to parent L2 when the task leaves vendor scope |
| **Tool calls** | L3 may provide vendor-specific scripts; parent L2 scripts remain available |

### Loading Order

```
1. User task arrives at L1 (aosp-root-router)
2. L1 routes to L2 (e.g., kernel-gki-expert)
3. L2 evaluates: does the task reference vendor/<oem>/ or device/<oem>/ paths?
   ├── No  → L2 handles it directly
   └── Yes → L2 hands off to L3 (e.g., qualcomm-kernel-expert)
4. L3 handles the OEM-specific part
5. If L3 needs generic AOSP guidance → hands back to parent L2
```

### `parent_skill` Field

Every L3 SKILL.md must set `parent_skill` in its YAML frontmatter:

```yaml
---
name: qualcomm-kernel-expert
layer: L3
path_scope: vendor/qcom/, device/qcom/
version: 1.0.0
android_version_tested: Android 15
parent_skill: kernel-gki-expert          # ← Must match an existing L2 skill name
---
```

The `parent_skill` field:
- Must reference an existing L2 skill by its `name` field
- Establishes the handoff relationship for routing
- Is validated by `scripts/skill_lint.py` (Phase 4.4)

---

## How to Create an L3 Skill

### Step 1: Copy the Template

```bash
cp -r skills/L3-TEMPLATE skills/L3-<oem>-<subsystem>-expert
```

### Step 2: Fill in the SKILL.md

Replace all `<placeholder>` values in the template:

1. **YAML frontmatter** — set `name`, `path_scope`, `parent_skill`
2. **Path Scope** — list all OEM-specific paths and their responsibilities
3. **Inherited Paths** — map parent L2 paths to your vendor-specific overrides
4. **Trigger Conditions** — list the OEM-specific scenarios
5. **Architecture Intelligence** — document SoC architecture, vendor deviations
6. **Forbidden Actions** — minimum 5 OEM-specific prohibitions (inherited L2 prohibitions still apply)
7. **Tool Calls** — add any vendor-specific scripts
8. **Handoff Rules** — define when to return to parent L2 or route elsewhere
9. **References** — add vendor-specific documentation

### Step 3: Add Scripts and References

```
skills/L3-<oem>-<subsystem>-expert/
├── SKILL.md
├── scripts/
│   └── <oem>_specific_tool.sh      # OEM-specific automation
└── references/
    └── <oem>_architecture.md        # Deep-dive vendor docs
```

### Step 4: Register in L1 Router

Add a row to the L1 router's Intent-to-Path Mapping Table:

```markdown
| Qualcomm kernel module, MSM driver | `vendor/qcom/`, `device/qcom/` | `L3-qualcomm-kernel-expert` |
```

### Step 5: Update Dirty Pages

Add the new skill to `memory/dirty_pages.json`:

```json
{
  "skill": "L3-qualcomm-kernel-expert",
  "status": "clean",
  "last_validated": "Android 15",
  "reason": null
}
```

### Step 6: Add Routing Test Cases

Add at least 5 test cases to `tests/routing_accuracy/test_router.py`:

```python
# L3 Qualcomm kernel routing
("TC-NNN", "QC MSM camera driver module signing failure", ["L3-qualcomm-kernel-expert"]),
("TC-NNN", "vendor/qcom/opensource/camera-kernel build error", ["L3-qualcomm-kernel-expert"]),
```

---

## Example: Qualcomm SoC Expert

A Qualcomm L3 extension might span multiple subsystems. Here is a focused example for the kernel subsystem.

### `skills/L3-qualcomm-kernel-expert/SKILL.md` (excerpt)

```yaml
---
name: qualcomm-kernel-expert
layer: L3
path_scope: vendor/qcom/opensource/, device/qcom/, kernel/msm-*/
version: 1.0.0
android_version_tested: Android 15
parent_skill: kernel-gki-expert
---
```

**Key paths:**
- `vendor/qcom/opensource/camera-kernel/` — Qualcomm camera kernel modules
- `vendor/qcom/opensource/audio-kernel/` — Qualcomm audio kernel modules (ADSP)
- `vendor/qcom/opensource/wlan/` — WLAN driver (qcacld-3.0)
- `device/qcom/<target>/BoardConfig.mk` — Board-level kernel configs
- `kernel/msm-<version>/` — Qualcomm MSM kernel fork (if using non-GKI)

**Vendor deviations:**
- Qualcomm ships many kernel modules as separate repos (`vendor/qcom/opensource/*`) rather than in-tree `drivers/`
- QC uses `techpack/` directories within the kernel tree for SoC-specific drivers
- ADSP and CDSP firmware are loaded at runtime from `/vendor/firmware/`
- Board DT overlays live in `device/qcom/<target>/` rather than `kernel/arch/arm64/boot/dts/`

**Forbidden actions (in addition to parent L2):**
1. Do NOT modify `vendor/qcom/proprietary/` files — these are binary blobs, not source
2. Do NOT assume `techpack/` paths exist in GKI kernels — they are QC MSM kernel only
3. Do NOT use QC-internal `defconfig` targets on GKI builds — use `gki_defconfig` + fragments
4. Do NOT link QC camera/audio modules against non-KMI symbols
5. Do NOT modify QC firmware files (`.mbn`, `.elf`) — they are signed by QC

---

## Example: MediaTek SoC Expert

### `skills/L3-mediatek-kernel-expert/SKILL.md` (excerpt)

```yaml
---
name: mediatek-kernel-expert
layer: L3
path_scope: vendor/mediatek/, device/mediatek/
version: 1.0.0
android_version_tested: Android 15
parent_skill: kernel-gki-expert
---
```

**Key paths:**
- `vendor/mediatek/kernel_modules/` — MTK kernel module source
- `vendor/mediatek/proprietary/` — Proprietary HAL and firmware
- `device/mediatek/<platform>/` — Platform-specific configs (e.g., `mt6983`, `mt6895`)
- `vendor/mediatek/kernel_modules/connectivity/` — MTK combo chip (Wi-Fi + BT + GPS + FM)

**Vendor deviations:**
- MediaTek uses a single "combo chip" driver for Wi-Fi, Bluetooth, GPS, and FM radio
- MTK kernel modules are shipped under `vendor/mediatek/kernel_modules/`, not `vendor/qcom/opensource/`
- Platform identifiers are chip model numbers (e.g., `mt6983` = Dimensity 9200)
- MTK preloader is a separate boot stage before LK (absent in Qualcomm's ABL flow)

**Forbidden actions (in addition to parent L2):**
1. Do NOT assume Qualcomm BSP paths when working on a MediaTek platform
2. Do NOT separate Wi-Fi/BT/GPS drivers — MTK uses a single combo chip module (`wmt_drv.ko`)
3. Do NOT modify `vendor/mediatek/proprietary/` files — binary, signed by MTK
4. Do NOT use QC-style `techpack/` paths — MTK uses `vendor/mediatek/kernel_modules/`
5. Do NOT skip the preloader stage in MTK boot analysis — it executes before LK

---

## Naming Convention

L3 skills follow the pattern:

```
L3-<vendor>-<subsystem>-expert
```

| Vendor | Example Skills |
|--------|---------------|
| `qualcomm` | `L3-qualcomm-kernel-expert`, `L3-qualcomm-hal-expert`, `L3-qualcomm-boot-expert` |
| `mediatek` | `L3-mediatek-kernel-expert`, `L3-mediatek-hal-expert`, `L3-mediatek-boot-expert` |
| `samsung` | `L3-samsung-exynos-expert` |
| `google` | `L3-google-tensor-expert` |
| `unisoc` | `L3-unisoc-platform-expert` |

### Multiple L3 Skills per Vendor

A single vendor can have multiple L3 skills, each extending a different L2 parent:

```
L3-qualcomm-kernel-expert    → parent: kernel-gki-expert
L3-qualcomm-hal-expert       → parent: hal-vendor-interface-expert
L3-qualcomm-boot-expert      → parent: bootloader-lk-expert
L3-qualcomm-audio-expert     → parent: multimedia-audio-expert
```

This keeps each L3 skill focused and follows the Paging Model principle (on-demand loading).

---

## Dirty Pages and Version Migration

L3 skills are tracked in `memory/dirty_pages.json` alongside L1 and L2 skills.

When a BSP update arrives:
1. Run `scripts/detect_dirty_pages.py` with the git diff from the BSP update
2. L3 skills whose `path_scope` matches changed files will be flagged dirty
3. Use `scripts/migration_impact.py` to generate a per-skill refresh checklist
4. Update the L3 SKILL.md content and bump `android_version_tested`

L3 skills are **more likely** to become dirty than L2 skills during BSP updates, because vendor paths change more frequently than AOSP paths.

---

## Validation Checklist

Before considering an L3 skill complete:

- [ ] SKILL.md follows the template (`skills/L3-TEMPLATE/SKILL.md`)
- [ ] `parent_skill` references a valid L2 skill name
- [ ] Path scope only contains OEM/vendor-specific paths
- [ ] At least 5 forbidden actions specific to this OEM/SoC (beyond inherited L2 prohibitions)
- [ ] Handoff rules include a path back to the parent L2 skill
- [ ] At least one script or reference document is provided
- [ ] Skill is registered in `memory/dirty_pages.json`
- [ ] At least 5 routing test cases added to `tests/routing_accuracy/test_router.py`
- [ ] `scripts/skill_lint.py` passes (once available)

---

*L3 Extension Guide v1.0.0 — Defines the framework for adding OEM/SoC-specific skills to the Hierarchical AI Agent Skill Set.*

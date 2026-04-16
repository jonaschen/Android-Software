# Android-Software-Owner Skill Set — Development Roadmap

> **Version:** 1.3
> **Date:** 2026-04-09
> **Based on:** ANDROID_SW_OWNER_DEV_PLAN.md v1.4
> **Target AOSP:** Android 14.0.0_r1 (extensible to A15+)

---

## Project Status Summary

> **As of:** 2026-04-17

| Area | Status | Notes |
|------|--------|-------|
| Architecture & Design | ✅ Complete | `CLAUDE.md`, `AGENTS.md`, `ANDROID_SW_OWNER_DEV_PLAN.md` v1.4 finalized |
| `skills/` directory | ✅ Phase 2 complete | L1 router + 12 L2 expert skills + 2 L3 OEM skills (Qualcomm, MediaTek) deployed |
| `memory/` directory | ✅ Phase 3 complete | 44 hindsight notes, `cross_skill_triggers.md` (12 patterns), `dirty_pages.json` validated |
| `tests/` directory | ✅ Phase 3 complete | `test_router.py` with 110 routing cases (30 multi-skill cross-domain, 10 L3 OEM) |
| `references/` directory | ✅ Phase 2 complete | `aosp_top_level_paths.md` v1.2 (49 path entries) |
| `scripts/` directory | ✅ Phase 4 complete | `validate_dirty_pages.py`, `detect_dirty_pages.py`, `migration_impact.py`, `skill_lint.py` |
| Git history | Active | Phase 1–5 deliverables complete; Phase 6 in progress (6.1, 6.2 done; 6.3–6.5 planned) |

### Current Phase
**Phase 6 — In Progress** (OEM/SoC L3 skill buildout — 6.1, 6.2 done; 6.3–6.5 planned)

Phase 5 — Complete ✅ (all deliverables 5.1–5.5 done)

Phase 4 — Complete ✅ (all deliverables 4.1–4.5 done)

Phase 3 — Complete ✅

---

## Alpha v0.1 Release — 2026-03-15

> **Status:** Published to GitHub. Open for BSP engineer field testing.

### What Is Released

| Component | Count | Notes |
|-----------|-------|-------|
| L1 Router | 1 | 40 intent-to-path mappings, 19 forbidden actions |
| L2 Expert Skills | 12 | Full SKILL.md + scripts + references per skill |
| Automation scripts | 6 | bp_lint, audit2allow_safe, check_aidl_version, validate_rc, check_pkvm_status, validate_dirty_pages |
| Hindsight notes | 22 | HS-001–HS-022 covering all 12 skill domains |
| Cross-skill patterns | 12 | Named multi-skill task patterns |
| Test cases | 100 | Ground-truth routing spec (30 multi-skill scenarios) |

### Alpha Scope Statement

> The skill content is complete and usable with any AI agent (Claude Code, Gemini, etc.) today.
> Routing is performed by the AI agent using the SKILL.md specification — no compiled router binary.
> Skills are validated against Android 14. A15 delta and automated accuracy benchmarking are Phase 4.

### Known Alpha Gaps

| Gap | Tracking |
|-----|---------|
| Router implementation (test suite runs in stub mode) | Phase 4.1 |
| Android 15 validation pass | Phase 4.5 |
| OEM/SoC Layer 3 extension skills | Phase 4.3 |
| `skill_lint.py` automated conformance check | Phase 4.4 |

### How to Report Alpha Feedback

See [CONTRIBUTING.md](CONTRIBUTING.md) — open a GitHub Issue for wrong paths, missing skills, or routing errors found during daily BSP work.

---

## Overview

This roadmap translates the four-phase architecture blueprint into concrete, deliverable milestones. Each phase has a clear gate criterion before the next phase begins.

---

## Phase 1: Infrastructure & L1 Router

**Goal:** Establish the routing backbone. No L2 work begins until L1 is validated.

### Deliverables

| # | Task | Output | Status |
|---|------|--------|--------|
| 1.1 | Create `skills/L1-aosp-root-router/SKILL.md` | L1 router with full intent-to-path mapping table | ✅ Done |
| 1.2 | Define path scope coverage | All top-level AOSP directories mapped (≥30 paths) | ✅ 34 paths |
| 1.3 | Document forbidden cross-domain actions | At least 10 explicit prohibitions in SKILL.md | ✅ 12 prohibitions |
| 1.4 | Scaffold `memory/` directory | `hindsight_notes/` dir + `dirty_pages.json` (empty template) | ✅ Done |
| 1.5 | Scaffold `tests/routing_accuracy/` | `test_router.py` stub + 26 routing test cases | ✅ Done |
| 1.6 | Scaffold `references/` directory | `aosp_top_level_paths.md` reference doc | ✅ 44 entries |

### Gate Criterion
- ✅ L1 router SKILL.md is complete with 20 ground-truth routing test cases defined.
- ✅ Directory structure matches the standard in `ANDROID_SW_OWNER_DEV_PLAN.md §8`.

---

## Phase 2: Layer 2 Expert Skills

**Goal:** Deploy all 9 L2 expert skills in priority order. Each skill is self-contained and independently loadable.

### Priority Tiers

#### Tier 1 — High Priority (Core platform stability)

| Skill | Path Scope | Key Deliverables |
|-------|-----------|-----------------|
| `L2-build-system-expert` | `build/`, `Android.bp`, `Android.mk` | Soong module type reference, `bp_lint.sh`, build error pattern guide |
| `L2-security-selinux-expert` | `system/sepolicy/`, `*.te` files | `audit2allow_safe.sh`, avc:denied resolution runbook, policy audit checklist |
| `L2-hal-vendor-interface-expert` | `hardware/interfaces/`, `vendor/` | AIDL/HIDL version matrix, Treble compliance checklist, VNDK boundary guide |

#### Tier 2 — Medium Priority (Boot & framework stability)

| Skill | Path Scope | Key Deliverables |
|-------|-----------|-----------------|
| `L2-framework-services-expert` | `frameworks/base/`, `frameworks/native/` | SystemServer lifecycle doc, @SystemApi usage guide, ANR prevention patterns |
| `L2-init-boot-sequence-expert` | `system/core/init/`, `*.rc` files | RC syntax reference, boot phase diagram, overlay rules guide |
| `L2-version-migration-expert` | Cross-cutting (diff analysis) | A14→A15 delta checklist, 16KB page migration guide, API compatibility matrix |
| `L2-bootloader-lk-expert` | `bootloader/lk/`, `bootable/bootloader/` ¹ | LK boot flow doc, fastboot protocol guide, A/B slot reference |
| `L2-trusted-firmware-atf-expert` | `atf/`, `trusty/` ¹ | ATF boot stages doc, SMC calling convention guide, PSCI reference |
| `L2-virtualization-pkvm-expert` | `packages/modules/Virtualization/`, `external/crosvm/` | pKVM EL2 architecture doc, crosvm VMM guide, Microdroid boot flow, vsock IPC reference |

#### Tier 3 — Standard Priority (Subsystem specialists)

| Skill | Path Scope | Key Deliverables |
|-------|-----------|-----------------|
| `L2-multimedia-audio-expert` | `frameworks/av/`, `hardware/interfaces/audio/` | AudioFlinger architecture doc, MediaCodec flow guide, Camera HAL checklist |
| `L2-connectivity-network-expert` | `packages/modules/Connectivity/`, `system/netd/` | netd architecture doc, ConnectivityService flow, Wi-Fi HAL guide |
| `L2-kernel-gki-expert` | `kernel/`, `drivers/` | GKI module interface guide, Kconfig standards, module signing checklist |

### Per-Skill Standard Checklist
Each L2 skill must include:
- [ ] `SKILL.md` using the template from `ANDROID_SW_OWNER_DEV_PLAN.md §11`
- [ ] `scripts/` with at least one automation tool (Python or Bash)
- [ ] `references/` with at least one deep-dive architecture document
- [ ] Defined `Trigger Conditions` and `Handoff Rules` to adjacent skills
- [ ] Explicit `Forbidden Actions` list (minimum 5 entries)

> ¹ Vendor-supplied paths — not in standard AOSP; confirmed at routing time by BSP layout.

### Gate Criterion
- All 12 L2 SKILL.md files present and conforming to template.
- Each skill passes a 10-case subsystem-specific routing test.
- Target: ≥85% subsystem resolution rate.

---

## Phase 3: Cross-Skill Collaboration & Hindsight Memory ✅

**Goal:** Enable multi-skill workflows and build the persistent learning system.

### Deliverables

| # | Task | Output | Status |
|---|------|--------|--------|
| 3.1 | Define cross-skill handoff protocols | Handoff Rules standardized across all 12 skills; pKVM handoff rows added to 4 skills; emit lines consistent | ✅ Done |
| 3.2 | Build parallel skill trigger patterns | `memory/cross_skill_triggers.md` — 12 named multi-skill patterns with skill priority order | ✅ Done |
| 3.3 | Populate `memory/hindsight_notes/` | 22 seed insights (HS-001–HS-022) covering all 12 L2 skill domains | ✅ 22 notes |
| 3.4 | Define `dirty_pages.json` schema | `scripts/validate_dirty_pages.py` — schema validator; passes 0 errors on 13 skills | ✅ Done |
| 3.5 | Expand test suite to 100 cases | `tests/routing_accuracy/test_router.py` — 100 cases (TC-001–TC-100), 30 multi-skill cross-domain | ✅ 100 cases |
| 3.6 | Run routing accuracy benchmark | 100 cases registered; 0 errors; stub mode pending real router (Phase 4) | ✅ Done |

### Gate Criterion
- ✅ 100-case test suite complete with 30 multi-skill scenarios.
- ✅ `validate_dirty_pages.py` passes 0 errors; dirty_pages.json ↔ skills/ in sync.
- ✅ All 12 skills have consistent Handoff Rules tables and emit lines.
- ⏳ Routing accuracy ≥95%: pending real router implementation (Phase 4 prerequisite).
- ⏳ Hallucination rate ≤5%: pending formal audit (Phase 4).
- ⏳ Cross-domain success rate ≥70%: pending real router (Phase 4).

---

## Phase 4: Dynamic Update & Version Migration Automation

**Goal:** Make the skill set self-maintaining across Android OS upgrades.

### Deliverables

| # | Task | Output | Status |
|---|------|--------|--------|
| 4.1 | Git-diff driven dirty page detection | `scripts/detect_dirty_pages.py` — scans git diff output against `path_scope` fields | ✅ Done |
| 4.2 | Automated migration impact report | `scripts/migration_impact.py` — generates per-skill refresh checklist for version bump | ✅ Done |
| 4.3 | Layer 3 extension framework | Template + guide for adding OEM skills (`qualcomm-soc-expert`, `mediatek-soc-expert`) | ✅ Done |
| 4.4 | SKILL.md version linting | `scripts/skill_lint.py` — validates all SKILL.md files against the template schema | ✅ Done |
| 4.5 | Android A15 validation pass | Update `android_version_tested` field across all skills; document deltas | ✅ Done |

### Gate Criterion
- `detect_dirty_pages.py` correctly identifies affected skills for a synthetic A14→A15 diff.
- Migration agility ≥80%: at least 80% of affected skills auto-identified after an OS upgrade.
- `skill_lint.py` passes clean on all skill files.

---

## Phase 5: Android 16 Readiness & Quality Hardening

**Goal:** Prepare the skill set for Android 16, harden routing accuracy with a live benchmark, and close documentation gaps exposed by Phase 4 completion.

### Deliverables

| # | Task | Output | Status |
|---|------|--------|--------|
| 5.1 | Android A16 validation pass | Update `android_version_tested` to Android 16 across all skills; document A15→A16 deltas per skill; leverage HS-033–HS-039 forward intelligence | ✅ Done |
| 5.2 | GBL bootloader skill refresh | Expand L2-bootloader-lk-expert to cover Generic Bootloader (GBL) alongside LK; update path_scope, architecture intelligence, and skill name if warranted (ref: HS-034) | ✅ Done |
| 5.3 | 16KB page size deep-dive content | Add 16KB page size migration guidance to L2-kernel-gki-expert and L2-version-migration-expert; create `references/16kb_page_migration_guide.md` with concrete audit steps | ✅ Done |
| 5.4 | Live routing accuracy benchmark | Implement a real router in `test_router.py` that loads SKILL.md path_scope fields and matches test-case paths; exit stub mode; target ≥95% accuracy on 100 cases | ✅ Done (100%) |
| 5.5 | Documentation refresh | Update README.md Alpha Status to reflect Phase 4 completion; update repository layout section; add Phase 5 references | ✅ Done |

### Gate Criterion
- All 13 skills pass `skill_lint.py` with `android_version_tested: Android 16`.
- `references/a15_to_a16_delta_summary.md` documents per-skill A16 deltas.
- `test_router.py` runs in live mode with ≥95% routing accuracy on 100 cases.
- `references/16kb_page_migration_guide.md` exists with audit steps for ELF alignment, mmap usage, and page-size assumptions.
- README.md reflects current project state (Phase 4 complete, Phase 5 active).

---

## Phase 6: OEM/SoC L3 Skill Buildout & Maintenance Mode

**Goal:** Populate the L3 extension framework with concrete OEM skills; enter structured maintenance mode monitoring for Q2 2026 AOSP source drop.

### Current Phase
**Phase 6 — In Progress** (started 2026-04-16)

### Deliverables

| # | Task | Output | Status |
|---|------|--------|--------|
| 6.1 | Qualcomm kernel L3 skill | `skills/L3-qualcomm-kernel-expert/` — first real L3 OEM skill; covers `vendor/qcom/opensource/` + `device/qcom/` + `kernel/msm-*/`; KMI audit script; SoC architecture reference; 5 routing test cases (TC-101–TC-105) | ✅ Done |
| 6.2 | MediaTek kernel L3 skill | `skills/L3-mediatek-kernel-expert/` — second L3 OEM skill; covers `vendor/mediatek/kernel_modules/` + `vendor/mediatek/proprietary/` + `device/mediatek/` + `kernel/mediatek/`; MTK KMI audit script with red-flag symbol detection; TINYSYS (SCP/SSPM/ADSP) architecture reference; 5 routing test cases (TC-106–TC-110); HS-044 hindsight note | ✅ Done |
| 6.3 | Q2 2026 AOSP source drop response | When AOSP A16 source lands: run `detect_dirty_pages.py`, generate migration impact report, update all affected skills | ⏳ Pending source drop |
| 6.4 | L3-aware routing upgrade | Extend `test_router.py` live router to load L3 skills from `skills/L3-*/SKILL.md`; route `vendor/<oem>/` paths to L3 before L2; target: TC-101–TC-105 route to L3-qualcomm-kernel-expert | ⏳ Planned |
| 6.5 | Phase 6 research log | Track Android 16 QPR1 (Q3 2026), ASB updates, GKI 6.12 LTS stability status | ⏳ Ongoing |

### Gate Criterion
- At least 2 concrete L3 skills deployed (Qualcomm + MediaTek).
- `skill_lint.py` passes on all L3 skills.
- `dirty_pages.json` includes all L3 skills.
- Routing test suite at ≥105 cases with L3 scenarios documented.
- AOSP A16 source drop processed within 1 session of availability.

---

## Milestones Summary

| Milestone | Phase | Key Metric | Status |
|-----------|-------|-----------|--------|
| M1: Router Live | End of Phase 1 | L1 SKILL.md complete, 20-case spot check passes | ✅ 2026-03-15 |
| M2: Core Skills Ready | End of Phase 2 Tier 1 | Build + Security + HAL skills deployed | ✅ 2026-03-15 |
| M3: All L2 Skills Ready | End of Phase 2 Tier 3 | All 12 L2 skills deployed, ≥85% subsystem resolution | ✅ 2026-03-15 |
| M4: Collaborative Agent | End of Phase 3 | 100-case suite, 22 hindsight notes, 12 cross-skill patterns, validator | ✅ 2026-03-15 |
| M5: Self-Maintaining | End of Phase 4 | Dirty page detection live, ≥80% migration agility, A15 validated | ✅ 2026-04-08 |
| M6: A16-Ready | End of Phase 5 | A16 validated, GBL covered, 16KB guide, live routing benchmark ≥95% | ✅ 2026-04-12 |
| M7: OEM-Ready | End of Phase 6 | ≥2 L3 OEM skills, L3-aware router, AOSP A16 source verified | ⏳ In progress |

---

## Acceptance Criteria (Final)

| Metric | Target |
|--------|--------|
| Routing Accuracy | ≥ 95% |
| Subsystem Resolution | ≥ 85% |
| Cross-Domain Success | ≥ 70% |
| Migration Agility | ≥ 80% |
| Hallucination Rate | ≤ 5% |

---

*Roadmap v1.6 — Phase 6.2 complete (2026-04-17): L3-mediatek-kernel-expert deployed (vendor/mediatek/kernel_modules/, vendor/mediatek/proprietary/, device/mediatek/, kernel/mediatek/); MTK KMI audit script with red-flag symbol detection; TINYSYS (SCP/SSPM/ADSP) architecture reference; 5 L3 routing test cases (TC-106–TC-110); HS-044 hindsight note with QC↔MTK analogy table. dirty_pages.json updated to 16 skills. Routing accuracy 110/110 (100%). Phase 6 gate (≥2 L3 OEM skills) satisfied. Phase 6.1 (2026-04-16): L3-qualcomm-kernel-expert deployed (vendor/qcom/opensource/, device/qcom/, kernel/msm-*/); KMI audit script; SoC codename/GKI branch reference; 5 L3 routing test cases (TC-101–TC-105); HS-042 hindsight note. Phase 5 complete (2026-04-12): All deliverables 5.1–5.5 done. Phase 5.1 (2026-04-12): A16 validation pass — all 13 skills updated to Android 16, 6 dirty skills refreshed with A16 deltas from HS-033–HS-039, a15_to_a16_delta_summary.md created, dirty_pages.json baseline set to Android 16. Phase 5.2 (2026-04-11): GBL bootloader skill refresh. Phase 5.3 (2026-04-10): 16KB page migration guide. Phase 5.4 (2026-04-10): Live routing benchmark 100%. Phase 5.5 (2026-04-10): Documentation refresh. Derived from ANDROID_SW_OWNER_DEV_PLAN.md v1.4*

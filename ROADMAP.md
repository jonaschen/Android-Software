# Android-Software-Owner Skill Set — Development Roadmap

> **Version:** 1.0
> **Date:** 2026-03-14
> **Based on:** ANDROID_SW_OWNER_DEV_PLAN.md v1.1
> **Target AOSP:** Android 14.0.0_r1 (extensible to A15+)

---

## Project Status Summary

> **As of:** 2026-03-15

| Area | Status | Notes |
|------|--------|-------|
| Architecture & Design | ✅ Complete | `CLAUDE.md`, `AGENTS.md`, `ANDROID_SW_OWNER_DEV_PLAN.md` v1.1 finalized |
| `skills/` directory | ✅ Phase 1 complete | `L1-aosp-root-router` deployed (34 paths, 12 forbidden actions) |
| `memory/` directory | ✅ Phase 1 complete | `hindsight_notes/` scaffolded, `dirty_pages.json` initialized |
| `tests/` directory | ✅ Phase 1 complete | `test_router.py` with 20 ground-truth routing cases |
| `references/` directory | ✅ Phase 1 complete | `aosp_top_level_paths.md` (44 path entries) |
| Git history | Active | Phase 1 deliverables committed |

### Current Phase
**Phase 1 — Complete (6 / 6 deliverables done) ✅**

**Next:** Phase 2 — Deploy Layer 2 Expert Skills (start with Tier 1: Build, Security, HAL).

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
| 1.5 | Scaffold `tests/routing_accuracy/` | `test_router.py` stub + 20 initial test cases | ✅ Done |
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
| `L2-bootloader-lk-expert` | `bootloader/lk/`, `bootable/bootloader/` | LK boot flow doc, fastboot protocol guide, partition table reference |
| `L2-trusted-firmware-atf-expert` | `atf/`, `trusty/`, `arm-trusted-firmware/` | ATF boot stages doc, TrustZone/EL3 architecture guide, secure boot chain reference |

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

### Gate Criterion
- All 11 L2 SKILL.md files present and conforming to template.
- Each skill passes a 10-case subsystem-specific routing test.
- Target: ≥85% subsystem resolution rate.

---

## Phase 3: Cross-Skill Collaboration & Hindsight Memory

**Goal:** Enable multi-skill workflows and build the persistent learning system.

### Deliverables

| # | Task | Output |
|---|------|--------|
| 3.1 | Define cross-skill handoff protocols | Handoff Rules section standardized across all skills |
| 3.2 | Build parallel skill trigger patterns | Document which task types activate ≥2 skills simultaneously |
| 3.3 | Populate `memory/hindsight_notes/` | Minimum 20 seed insights from Phase 1 & 2 learnings |
| 3.4 | Define `dirty_pages.json` schema | Version-keyed invalidation tracking spec + validator script |
| 3.5 | Expand test suite to 100 cases | Includes 30 multi-skill cross-domain scenarios |
| 3.6 | Run routing accuracy benchmark | Full 100-case blind test, target ≥95% routing accuracy |

### Gate Criterion
- Routing accuracy ≥95% on 100-case test suite.
- Hallucination rate ≤5% on random path citation audit.
- Cross-domain success rate ≥70% on ≥3-skill scenario tests.

---

## Phase 4: Dynamic Update & Version Migration Automation

**Goal:** Make the skill set self-maintaining across Android OS upgrades.

### Deliverables

| # | Task | Output |
|---|------|--------|
| 4.1 | Git-diff driven dirty page detection | `scripts/detect_dirty_pages.py` — scans git diff output against `path_scope` fields |
| 4.2 | Automated migration impact report | `scripts/migration_impact.py` — generates per-skill refresh checklist for version bump |
| 4.3 | Layer 3 extension framework | Template + guide for adding OEM skills (`qualcomm-soc-expert`, `mediatek-soc-expert`) |
| 4.4 | SKILL.md version linting | `scripts/skill_lint.py` — validates all SKILL.md files against the template schema |
| 4.5 | Android A15 validation pass | Update `android_version_tested` field across all skills; document deltas |

### Gate Criterion
- `detect_dirty_pages.py` correctly identifies affected skills for a synthetic A14→A15 diff.
- Migration agility ≥80%: at least 80% of affected skills auto-identified after an OS upgrade.
- `skill_lint.py` passes clean on all skill files.

---

## Milestones Summary

| Milestone | Phase | Key Metric | Status |
|-----------|-------|-----------|--------|
| M1: Router Live | End of Phase 1 | L1 SKILL.md complete, 20-case spot check passes | ✅ 2026-03-15 |
| M2: Core Skills Ready | End of Phase 2 Tier 1 | Build + Security + HAL skills deployed | ⏳ Up next |
| M3: All L2 Skills Ready | End of Phase 2 Tier 3 | All 11 L2 skills deployed, ≥85% subsystem resolution | — |
| M4: Collaborative Agent | End of Phase 3 | ≥95% routing accuracy, ≥70% cross-domain success | — |
| M5: Self-Maintaining | End of Phase 4 | Dirty page detection live, ≥80% migration agility | — |

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

*Roadmap v1.0 — derived from ANDROID_SW_OWNER_DEV_PLAN.md v1.1*

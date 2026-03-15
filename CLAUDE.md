# Claude Development Guide: Android-Software-Owner Skill Set

This repository implements a **Hierarchical AI Agent Skill Set** based on an **MMU-driven Memory Model** for managing AOSP.

## 🏗️ Architecture Design
- **Layer 1 (Router):** The `aosp-root-router` maps semantic intent (e.g., "Add a new HAL") to physical paths (e.g., `hardware/interfaces/`).
- **Layer 2 (Experts):** Specialized Skills (`build`, `security`, `framework`, etc.) that hold deep architectural knowledge and domain scripts for specific paths.
- **Layer 3 (Extensions):** Plug-and-play Skills for OEM/SoC specific extensions (planned — Phase 4).

## 🗂️ Deployed Skills

### Layer 1
| Skill | Path Scope |
|-------|-----------|
| `skills/L1-aosp-root-router/` | All AOSP root paths — 34 mappings, 12 forbidden actions |

### Layer 2
| Skill | Path Scope | Script | Reference |
|-------|-----------|--------|-----------|
| `skills/L2-build-system-expert/` | `build/`, `Android.bp`, `*.mk`, `prebuilts/` | `bp_lint.sh` | `soong_module_types.md` |
| `skills/L2-security-selinux-expert/` | `system/sepolicy/`, `*.te`, `*_contexts` | `audit2allow_safe.sh` | `selinux_policy_guide.md` |
| `skills/L2-hal-vendor-interface-expert/` | `hardware/interfaces/`, `vendor/`, `system/vndk/` | `check_aidl_version.py` | `aidl_hidl_treble_guide.md` |
| `skills/L2-framework-services-expert/` | `frameworks/base/`, `frameworks/native/` | `find_system_service.sh` | `system_server_lifecycle.md` |
| `skills/L2-init-boot-sequence-expert/` | `system/core/init/`, `*.rc`, `bootable/` | `validate_rc_syntax.py` | `init_rc_reference.md` |
| `skills/L2-version-migration-expert/` | Cross-cutting (diff analysis) | `check_api_compatibility.py` | `a14_to_a15_migration_checklist.md` |
| `skills/L2-multimedia-audio-expert/` | `frameworks/av/`, `hardware/interfaces/audio/` | `trace_audio_buffer.sh` | `audioflinger_architecture.md` |
| `skills/L2-connectivity-network-expert/` | `packages/modules/Connectivity/`, `system/netd/` | `dump_netd_rules.sh` | `netd_connectivity_architecture.md` |
| `skills/L2-kernel-gki-expert/` | `kernel/`, `drivers/` | `check_gki_symbol_list.sh` | `gki_module_development_guide.md` |

## 📜 Development Standards

### Skill Structure (`skills/<layer>-<name>/`)
- **SKILL.md:** Must follow the template in `ANDROID_SW_OWNER_DEV_PLAN.md §11`.
- **scripts/:** Use Python for complex logic, Bash for simple shell wrappers.
- **references/:** Markdown files for deep architectural insights.

### Coding Principles
1. **Path Discipline:** All knowledge MUST be indexed by AOSP source paths.
2. **Forbidden Actions:** Every `SKILL.md` must list actions the agent is **prohibited** from doing (minimum 5 entries).
3. **Paging Model:** Design Skills for on-demand loading, not monolithic context.
4. **Hindsight Memory:** After solving a problem, record the insight in `memory/hindsight_notes/`.
5. **Dirty Pages:** After an OS version change, mark affected skills in `memory/dirty_pages.json`.

## 🛠️ Build & Test Commands
- **Verify Routing:** `python3 tests/routing_accuracy/test_router.py`
- **Validate .rc files:** `python3 skills/L2-init-boot-sequence-expert/scripts/validate_rc_syntax.py <file.rc>`
- **Check AIDL versions:** `python3 skills/L2-hal-vendor-interface-expert/scripts/check_aidl_version.py hardware/interfaces/`
- **Check API compatibility:** `python3 skills/L2-version-migration-expert/scripts/check_api_compatibility.py <before.txt> <after.txt>`
- **Check dirty pages:** `python3 skills/L2-version-migration-expert/scripts/check_api_compatibility.py --dirty-pages memory/dirty_pages.json`
- **Skill Linting:** `scripts/skill_lint.py` (planned — Phase 4)

## 🚀 Key Directories
- `skills/`: Core logic of the Hierarchical Agent (L1 + 9 × L2 deployed).
- `memory/hindsight_notes/`: Persistent insight library built up over time.
- `memory/dirty_pages.json`: Tracks which skills need refresh after an OS version bump.
- `tests/routing_accuracy/`: Routing accuracy evaluation suite (20 ground-truth cases).
- `references/`: General AOSP documentation (`aosp_top_level_paths.md`).

## 📂 AOSP Source Code
The AOSP source tree is cloned into this repository for **reference only**. It exists to inform skill content — path mappings, architectural patterns, and forbidden action boundaries.
- **Do not modify** any AOSP source files.
- **Do not treat** AOSP source as a development deliverable.
- All development work targets `skills/`, `memory/`, `tests/`, and `references/` exclusively.

---
**Focus on "Path as Truth" to eliminate cross-subsystem hallucinations.**

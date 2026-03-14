# Claude Development Guide: Android-Software-Owner Skill Set

This repository implements a **Hierarchical AI Agent Skill Set** based on an **MMU-driven Memory Model** for managing AOSP.

## 🏗️ Architecture Design
- **Layer 1 (Router):** The `aosp-root-router` maps semantic intent (e.g., "Add a new HAL") to physical paths (e.g., `hardware/interfaces/`).
- **Layer 2 (Experts):** Specialized Skills (`build`, `security`, `framework`, etc.) that hold deep architectural knowledge and domain scripts for specific paths.
- **Layer 3 (Extensions):** Plug-and-play Skills for OEM/SoC specific extensions.

## 📜 Development Standards

### Skill Structure (`skills/<layer>-<name>/`)
- **SKILL.md:** Must follow the template in `ANDROID_SW_OWNER_DEV_PLAN.md`.
- **scripts/:** Use Python for complex logic, Bash for simple shell wrappers.
- **references/:** Markdown files for deep architectural insights.

### Coding Principles
1. **Path Discipline:** All knowledge MUST be indexed by AOSP source paths.
2. **Forbidden Actions:** Every `SKILL.md` must list actions the agent is **prohibited** from doing (e.g., "No Java service mods in `system/core/`").
3. **Paging Model:** Design Skills for on-demand loading, not monolithic context.
4. **Hindsight Memory:** After solving a problem, record the "Insight" in `memory/hindsight_notes/`.

## 🛠️ Build & Test Commands
- **Verify Routing:** Run `python3 tests/routing_accuracy/test_router.py`
- **Skill Linting:** Run `scripts/skill_lint.py` to verify `SKILL.md` format (when implemented).

## 🚀 Key Directories
- `skills/`: Core logic of the Hierarchical Agent.
- `memory/`: Persistent storage for insights and migration tracking.
- `tests/`: Evaluation suites for routing and expert knowledge.
- `references/`: General AOSP documentation.

## 📂 AOSP Source Code
The AOSP source tree is cloned into this repository for **reference only**. It exists to inform skill content — path mappings, architectural patterns, and forbidden action boundaries.
- **Do not modify** any AOSP source files.
- **Do not treat** AOSP source as a development deliverable.
- All development work targets `skills/`, `memory/`, `tests/`, and `references/` exclusively.

---
**Focus on "Path as Truth" to eliminate cross-subsystem hallucinations.**

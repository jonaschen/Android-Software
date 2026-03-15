# Android-Software-Owner Agent Skill Set Development Plan & Blueprint

> **Version:** v1.4
> **Date:** 2026-03-15
> **Reference Architecture:** AOSP Hierarchical AI Agent Skill Set (MMU Page Table Driven Memory Model)  
> **Target Audience:** Android SW Owners, AOSP Integration Engineers, Platform AI Tooling Teams

---

## Table of Contents

1. [Role Definition & Design Intent](#1-role-definition--design-intent)
2. [MMU Page Table Memory Mapping](#2-mmu-page-table-memory-mapping)
3. [Skill Set Overall Architecture](#3-skill-set-overall-architecture)
4. [Layer 1 Skill: AOSP Root Router](#4-layer-1-skill-aosp-root-router)
5. [Layer 2 Skill: Subsystem Experts](#5-layer-2-skill-subsystem-experts)
6. [Layer 3 Extensibility](#6-layer-3-extensibility)
7. [Four-Phase Roadmap](#7-four-phase-roadmap)
8. [Skill Directory Structure Standards](#8-skill-directory-structure-standards)
9. [Project Migration & Dynamic Memory Update](#9-project-migration--dynamic-memory-update)
10. [Milestones & Acceptance Criteria](#10-milestones--acceptance-criteria)
11. [Appendix: SKILL.md Template](#11-appendix-skillmd-template)

---

## 1. Role Definition & Design Intent

### 1.1 Who is the Android Software Owner?

The **Android Software Owner (Android SW Owner)** is the technical lead responsible for AOSP platform integration. Their responsibilities span multiple technical layers:

| Responsibility | Scope of Work |
|----------|-------------|
| **Platform Integration** | Merging OEM customizations into AOSP mainline, managing `device/` and `vendor/` partitions. |
| **Cross-Dept Coordination** | Bridging BSP engineers, framework engineers, and product management. |
| **Version Migration** | Leading Android OS upgrades (e.g., A14 → A15), impact assessment, and migration planning. |
| **Build System Gatekeeper** | Reviewing `Android.bp` / `Makefile` changes and maintaining build health. |
| **Security Maintenance** | Ensuring SELinux policy integrity and auditing new service security boundaries. |
| **HAL Interface Management** | Managing AIDL/HIDL version compatibility and coordinating vendor interface upgrades. |

### 1.2 Why a Claude-Compatible Skill Set?

AOSP exceeds **50 million lines of code** across C++, Rust, Java, Kotlin, and Go. Using a generic AI Agent leads to:

- **Context Bloat:** Single queries cannot cover all relevant subsystems.
- **"Lost in the Middle":** LLM attention decay in ultra-long contexts.
- **Hallucination Paths:** Confusion between boundaries like `system/core/` and `frameworks/base/`.
- **Knowledge Drift:** OS upgrades invalidate previous architectural assumptions.

**Solution:** A **Claude-compatible Skill Set** using an **OS MMU-driven** hierarchical architecture. The Agent loads knowledge "pages" (Skills) on-demand, mirroring how an OS manages memory.

### 1.3 Core Design Principles

| Principle | Description |
|------|------|
| **Path as Truth** | All knowledge is indexed by AOSP source paths to eliminate ambiguity. |
| **Paging On-Demand** | Load subsystem knowledge only when the task requires it; zero redundant context. |
| **Path Discipline** | Layer 1 strictly constrains search space to prevent cross-domain hallucinations. |
| **Dynamic Invalidation** | Mark "Dirty Pages" during version upgrades to refresh only affected Skills. |
| **Progressive Disclosure** | Deep details are loaded via `references/` only when the Agent explicitly needs them. |

---

## 2. MMU Page Table Memory Mapping

### 2.1 Concept Mapping Table

| OS Memory Management | Android-SW-Owner Agent Implementation | Function |
|---|---|---|
| **Virtual Address Space** | SW Owner's Semantic Intent | "Review HAL changes for this PR." |
| **Physical Memory (RAM)** | Active LLM Context Window | Files and instructions currently in use. |
| **Page Directory (L1)** | `aosp-root-router` Skill | Maps intent to `build/`, `system/`, `frameworks/`, etc. |
| **Page Table (L2)** | Subsystem Skill Group | Path-specific syntax, patterns, and tools. |
| **Page Fault** | Tool Call (`read_file` / `grep`) | Triggered when the Agent lacks specific code context. |
| **TLB (Cache)** | Prefix Caching | Fast reuse of recently loaded Skill instructions. |
| **Swap / Eviction** | Hindsight Notes | Evicting old context while retaining compressed insights. |
| **Dirty Page** | Invalidated Skills | Skills marked for refresh after Git detects path changes. |

---

## 3. Skill Set Overall Architecture

```
Android-Software-Owner Skill Set
│
├── 🗺️  [L1-ROUTER] aosp-root-router
│   └── AOSP Root Architecture Routing, Intent-to-Path Mapping, Guardrails.
│
├── ⚙️  [L2-BUILD] build-system-expert
│   └── Soong/Kati/Ninja, Android.bp syntax, Build debugging.
│
├── 🔒 [L2-SECURITY] security-selinux-expert
│   └── SELinux .te rules, avc:denied analysis, Policy auditing.
│
├── 🏗️  [L2-FRAMEWORK] framework-services-expert
│   └── System Server, @SystemApi, ANR prevention, Lifecycle.
│
├── 🔌 [L2-HAL] hal-vendor-interface-expert
│   └── AIDL/HIDL definitions, Binder IPC, VNDK, Treble.
│
├── 🚀 [L2-INIT] init-boot-sequence-expert
│   └── .rc syntax, Boot lifecycle, Overlay rules.
│
├── 🎵 [L2-MEDIA] multimedia-audio-expert
│   └── AudioFlinger, MediaCodec, Camera HAL, SurfaceFlinger.
│
├── 🌐 [L2-CONNECTIVITY] connectivity-network-expert
│   └── netd, ConnectivityService, Bluetooth, Wi-Fi HAL.
│
├── 📱 [L2-MIGRATION] version-migration-expert
│   └── Diff analysis, 16KB page migration, API compatibility.
│
├── 🔧 [L2-KERNEL] kernel-gki-expert
│   └── GKI modules, Driver interfaces, Kconfig, Module signing.
│
├── 🥾 [L2-BOOTLOADER] bootloader-lk-expert
│   └── little-kernel (LK) / ABL, Fastboot protocol, Partition table, A/B slots, AVB.
│   └── ⚠ Paths are vendor/SoC-supplied (bootloader/lk/); not in standard AOSP.
│
├── 🔐 [L2-ATF] trusted-firmware-atf-expert
│   └── ARM Trusted Firmware (TF-A), BL1/BL2/BL31/BL32, SMC, PSCI, TrustZone, Trusty TEE.
│   └── ⚠ Paths are vendor/SoC-supplied (atf/, trusty/); not in standard AOSP.
│
└── 🖥️  [L2-VIRT] virtualization-pkvm-expert
    └── pKVM (EL2 stage-2 isolation), Android Virtualization Framework (AVF),
    └── VirtualizationService, crosvm VMM, Microdroid guest OS, vsock IPC, vmbase.
    └── Paths: packages/modules/Virtualization/, external/crosvm/
```

---

## 4. Layer 1 Skill: AOSP Root Router

### 4.1 `aosp-root-router` Responsibilities

**Role:** The Page Directory. Acts as the entry point for all tasks, mapping intent to physical AOSP paths and enforcing cross-domain boundaries.

**Core Instruction Snippet:**
- ❌ **Forbidden:** Searching for Java services in `system/core/` (Use `frameworks/base/`).
- ❌ **Forbidden:** Modifying SELinux in `frameworks/` (Use `system/sepolicy/`).
- ❌ **Forbidden:** Modifying `init.rc` directly in `/system/` (Use `vendor/` overlays).

---

## 5. Layer 2 Skill: Subsystem Experts

Each L2 Skill is a standalone Claude Skill containing:
- **SKILL.md:** Core instructions, architectural patterns, and forbidden actions.
- **scripts/:** Specialized Python/Bash tools (e.g., `audit2allow_safe.sh`).
- **references/:** Deep-dive architecture docs (e.g., `binder_internal.md`).

---

## 6. Layer 3 Extensibility

Supports loading OEM-specific Layer 3 Skills from:
- `qualcomm-soc-expert/`: QC specific toolchains and HAL quirks.
- `mediatek-soc-expert/`: MTK specific integrations.
- `art-runtime-expert/`: Deep ART optimizations.

---

## 7. Four-Phase Roadmap

### Phase 1: AGENTS.md Routing & Infrastructure
- Establish `AGENTS.md` as the master router.
- Lock tool definitions to prevent KV-cache fragmentation.
- Deploy `aosp-root-router` (Layer 1).

### Phase 2: Layer 2 Expert Deployment
- Deploy High-Priority Skills: Build, Security, HAL.
- Deploy Medium-Priority Skills: Framework, Init, Migration, Bootloader (LK), Trusted Firmware (ATF).
- Deploy Standard-Priority Skills: Media, Connectivity, Kernel.

### Phase 3: Cross-Skill Collaboration & Hindsight Memory
- Implement parallel Skill triggering for multi-subsystem tasks.
- Build the "Hindsight Notes" repository for persistent learning.

### Phase 4: Dynamic Update & Version Migration Automation
- Git-diff driven "Dirty Page" invalidation.
- Automated migration impact reports for Android OS upgrades.

---

## 8. Skill Directory Structure Standards

```
android-sw-owner/
├── AGENTS.md                          # Master Router (L1 Entry)
├── skills/
│   ├── L1-aosp-root-router/
│   │   └── SKILL.md                   # Routing & Path Discipline
│   ├── L2-build-system-expert/
│   │   ├── SKILL.md
│   │   ├── scripts/                   # bp_lint.sh, etc.
│   │   └── references/                # soong_module_types.md
│   ├── L2-bootloader-lk-expert/
│   │   ├── SKILL.md
│   │   ├── scripts/                   # fastboot_check.sh
│   │   └── references/                # lk_boot_flow.md
│   ├── L2-trusted-firmware-atf-expert/
│   │   ├── SKILL.md
│   │   ├── scripts/                   # atf_image_verify.sh
│   │   └── references/                # atf_boot_stages.md
│   └── ... (other L2 skills)
├── memory/
│   ├── hindsight_notes/               # 22 seed insights (HS-001–HS-022)
│   ├── cross_skill_triggers.md        # 12 multi-skill task patterns
│   └── dirty_pages.json               # Invalidation tracking (validated)
├── scripts/
│   └── validate_dirty_pages.py        # dirty_pages.json schema validator
└── tests/                             # Routing & Skill accuracy tests
    └── routing_accuracy/
        └── test_router.py             # 100-case suite (30 multi-skill)
```

---

## 10. Milestones & Acceptance Criteria

| Metric | Target | Method |
|---|---|---|
| **Routing Accuracy** | ≥ 95% | 100-case blind test on path mapping. |
| **Subsystem Resolution** | ≥ 85% | Success rate of L2 expert tasks. |
| **Cross-Domain Success** | ≥ 70% | Complex tasks requiring ≥ 3 Skills. |
| **Migration Agility** | ≥ 80% | Skill refresh coverage after OS upgrade. |
| **Hallucination Rate** | ≤ 5% | Random audit of path citations. |

---

## 11. Appendix: SKILL.md Template

```markdown
---
name: <skill-name>
layer: L2
path_scope: <AOSP_PATH_PREFIX>
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

## Path Scope
## Trigger Conditions
## Architecture Intelligence
## Forbidden Actions
## Tool Calls
## Handoff Rules
## References
```

---
*Blueprint v1.4 (2026-03-15): Phase 3 complete — 22 hindsight notes, 12 cross-skill trigger patterns, dirty_pages.json schema validator, 100-case routing test suite (30 multi-skill scenarios), all handoff rules standardized across 12 L2 skills. Added L2-virtualization-pkvm-expert (pKVM, AVF, Microdroid, crosvm). Phase 4 next: detect_dirty_pages.py, migration_impact.py, skill_lint.py, A15 validation pass.*

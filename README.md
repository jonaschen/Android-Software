# Android-Software-Owner Skill Set

A **Hierarchical AI Agent Skill Set** for managing AOSP platform integration, built on an **MMU-driven Memory Model**. Designed for Android Software Owners who need accurate, path-scoped AI assistance across a 50M+ LOC codebase.

---

## The Problem

Using a generic AI agent on AOSP leads to:

- **Context bloat** — no single query can cover all relevant subsystems
- **Hallucination paths** — confusion between boundaries like `system/core/` and `frameworks/base/`
- **Knowledge drift** — OS upgrades silently invalidate architectural assumptions

## The Solution

A three-layer agent architecture that mirrors how an OS MMU manages memory. Knowledge is loaded as "pages" on-demand — only the subsystem relevant to the current task is loaded into context.

| OS Concept | Agent Equivalent |
|---|---|
| Page Directory (L1) | `aosp-root-router` — maps intent to AOSP paths |
| Page Table (L2) | Subsystem expert skills (Build, HAL, SELinux, …) |
| Page Fault | Tool call (`read_file` / `grep`) for missing context |
| Dirty Page | Skill marked stale after a version migration |
| Swap / Eviction | Hindsight notes — compressed insights from past tasks |

---

## Architecture

```
Android-Software-Owner Skill Set
│
├── [L1] aosp-root-router          # Entry point — all tasks routed here first
│
├── [L2] build-system-expert       # build/, Android.bp, Soong/Kati/Ninja
├── [L2] security-selinux-expert   # system/sepolicy/, SELinux .te rules
├── [L2] hal-vendor-interface-expert  # hardware/interfaces/, AIDL/HIDL, Treble
├── [L2] framework-services-expert # frameworks/base/, SystemServer, @SystemApi
├── [L2] init-boot-sequence-expert # system/core/init/, .rc syntax, boot lifecycle
├── [L2] version-migration-expert  # Cross-cutting — A14→A15 diffs, 16KB pages
├── [L2] multimedia-audio-expert   # frameworks/av/, AudioFlinger, Camera HAL
├── [L2] connectivity-network-expert  # netd, ConnectivityService, Wi-Fi HAL
├── [L2] kernel-gki-expert         # kernel/, GKI modules, Kconfig, signing
│
└── [L3] OEM Extensions            # qualcomm-soc-expert, mediatek-soc-expert, …
```

---

## Repository Structure

```
Android-Software/
├── AGENTS.md                      # Master routing entry point
├── CLAUDE.md                      # Development standards and principles
├── ANDROID_SW_OWNER_DEV_PLAN.md   # Full architecture blueprint (v1.1)
├── ROADMAP.md                     # Phased development roadmap
├── skills/                        # Skill implementations (L1, L2, L3)
├── memory/
│   ├── hindsight_notes/           # Persistent insights from past tasks
│   └── dirty_pages.json           # Stale skill tracking across OS upgrades
├── tests/
│   └── routing_accuracy/          # Routing benchmark test suite
└── references/                    # General AOSP architectural documentation
```

---

## Design Principles

| Principle | Description |
|---|---|
| **Path as Truth** | All knowledge indexed by AOSP source paths — no ambiguous references |
| **Paging On-Demand** | Load only the subsystem skill needed; zero redundant context |
| **Forbidden Actions** | Every skill explicitly lists prohibited cross-domain operations |
| **Dynamic Invalidation** | Git-diff detection marks affected skills dirty after a version bump |
| **Progressive Disclosure** | Deep docs in `references/` loaded only when explicitly needed |

---

## Current Status

**Phase 1 — Infrastructure & L1 Router (In Progress)**

Architecture and design are complete. Skill implementation has not yet begun. See [ROADMAP.md](ROADMAP.md) for the full delivery plan and milestone criteria.

---

## Quality Targets

| Metric | Target |
|--------|--------|
| Routing Accuracy | ≥ 95% |
| Subsystem Resolution | ≥ 85% |
| Cross-Domain Success | ≥ 70% |
| Migration Agility | ≥ 80% |
| Hallucination Rate | ≤ 5% |

---

## Documentation

| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent routing entry point and global guardrails |
| `CLAUDE.md` | Coding standards for skill development |
| `ANDROID_SW_OWNER_DEV_PLAN.md` | Full architecture blueprint and SKILL.md template |
| `ROADMAP.md` | Phased roadmap with deliverables and gate criteria |

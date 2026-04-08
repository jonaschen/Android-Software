# Android Software Owner — AI Agent Skill Set

> **Beta v0.5** — Phase 4 complete. Skills validated against Android 15 with A16 forward intelligence staged.
> See [How to Report Gaps](#reporting-gaps-and-feedback) to help improve this.

A **Hierarchical AI Agent Skill Set** for Android Software Owners and BSP engineers working with AOSP. Built on an **MMU-driven Memory Model** — the agent loads only the subsystem knowledge relevant to your current task, preventing context bloat and hallucinated paths across a 50M+ LOC codebase.

---

## Who Is This For?

- **Android Software Owners** managing platform integration across build, HAL, SELinux, init, framework, and kernel
- **BSP engineers** working with SoC-specific layers (LK/ABL bootloader, ATF/TF-A, vendor HALs, pKVM)
- **Platform engineers** handling Android version migrations (A14 → A15, 16KB page size, GKI compliance)
- Anyone who has been burned by an AI agent confidently citing the wrong AOSP path

---

## The Problem This Solves

Generic AI agents on AOSP produce three failure modes:

| Failure | Example |
|---------|---------|
| **Hallucinated paths** | "Edit `system/core/services/FooService.java`" — that path doesn't exist |
| **Cross-domain confusion** | Routing a LK bootloader bug to `init`, or an ATF EL3 issue to the Linux kernel |
| **Knowledge drift** | Confidently describing Android 13 behavior on an Android 15 device |

This skill set fixes these by forcing the agent through a **Layer 1 router** that maps intent to verified AOSP paths, then loads the correct **Layer 2 expert** with subsystem-specific knowledge, forbidden actions, and tooling.

---

## Architecture

```
Your task
   │
   ▼
[L1] aosp-root-router          ← Always loads first. Maps intent → path.
   │
   ├──► [L2] build-system-expert          build/, Android.bp, Soong
   ├──► [L2] security-selinux-expert      system/sepolicy/, .te rules
   ├──► [L2] hal-vendor-interface-expert  hardware/interfaces/, AIDL/HIDL
   ├──► [L2] framework-services-expert    frameworks/base/, SystemServer
   ├──► [L2] init-boot-sequence-expert    system/core/init/, .rc files
   ├──► [L2] version-migration-expert     A14→A15 diffs, 16KB page migration
   ├──► [L2] multimedia-audio-expert      frameworks/av/, AudioFlinger
   ├──► [L2] connectivity-network-expert  netd, ConnectivityService, Wi-Fi
   ├──► [L2] kernel-gki-expert            kernel/, GKI modules, Kconfig
   ├──► [L2] bootloader-lk-expert         bootloader/lk/, fastboot, A/B slots ¹
   ├──► [L2] trusted-firmware-atf-expert  atf/, BL31, SMC, PSCI, Trusty ¹
   └──► [L2] virtualization-pkvm-expert   packages/modules/Virtualization/, crosvm
```

> ¹ Vendor-supplied paths — not in standard AOSP. Routing is by subsystem intent, not path presence.

---

## Quickstart (5 minutes)

### Prerequisites

- [Claude Code](https://github.com/anthropics/claude-code) (recommended) or any AI agent that can load files from a local directory
- An AOSP workspace (or just the questions — the agent works without local source)

### Step 1: Clone

```bash
git clone <repo-url> Android-Software
cd Android-Software
```

### Step 2: Point your AI agent at the project

**With Claude Code:**
```bash
cd Android-Software
claude
```

Claude Code automatically reads `CLAUDE.md` and `AGENTS.md` at startup — the routing system is live immediately.

**With any other AI agent:**
Load `AGENTS.md` as your system prompt, then load `skills/L1-aosp-root-router/SKILL.md`. The agent will request the correct L2 skill as needed.

### Step 3: Ask your first question

```
"I'm getting avc: denied { read } for my new vendor daemon on /data/vendor/foo/.
 What SELinux policy do I need?"
```

The agent routes to `L2-security-selinux-expert`, applies the forbidden-action guardrails, and gives you a path-scoped answer.

---

## BSP-Specific Setup

### Vendor Path Tuning

If your BSP places vendor trees at non-standard paths, update the L1 router's footnote entries:

```
skills/L1-aosp-root-router/SKILL.md  ← routing table
```

The default vendor path footnotes are:
- `bootloader/lk/` — Qualcomm ABL / little-kernel
- `atf/` or `arm-trusted-firmware/` — ARM TF-A
- `trusty/` — Trusty TEE

If your SoC uses different paths (e.g., `vendor/qcom/proprietary/abl/`), add a row to the mapping table pointing to your actual path and the same L2 skill.

### Adding Your Own Hindsight Notes

After solving a tricky BSP problem, record it:

```bash
# Create memory/hindsight_notes/HS-023_your_insight.md
# Follow the format of existing notes (HS-001 through HS-022)
```

These persist across sessions and teach the agent your platform's specific behavior.

### Marking Skills Dirty After a BSP Update

When you pull a new BSP drop or update your Android version:

```bash
# Auto-detect dirty skills from a git diff
git diff --name-only A14..A15 | python3 scripts/detect_dirty_pages.py --apply

# Generate a per-skill migration impact report
python3 scripts/migration_impact.py --from A14 --to A15

# Validate dirty_pages.json schema
python3 scripts/validate_dirty_pages.py

# Lint all SKILL.md files against the template schema
python3 scripts/skill_lint.py
```

The `detect_dirty_pages.py` script reads changed file paths, matches them against each skill's `path_scope`, and updates `memory/dirty_pages.json` automatically.

---

## What Each Skill Covers

| Skill | When to Use |
|-------|------------|
| `L2-build-system-expert` | Android.bp errors, Soong module types, VNDK linking, prebuilts |
| `L2-security-selinux-expert` | `avc: denied`, new daemon domain, `neverallow` violations, property_contexts |
| `L2-hal-vendor-interface-expert` | AIDL/HIDL interface definition, version freeze, Treble compliance, VNDK |
| `L2-framework-services-expert` | SystemServer, `@SystemApi`, ANR, Binder, SurfaceFlinger |
| `L2-init-boot-sequence-expert` | `.rc` syntax, boot phase ordering, ueventd, property triggers |
| `L2-version-migration-expert` | A14→A15 impact, 16KB page alignment, API compatibility check |
| `L2-multimedia-audio-expert` | AudioFlinger, audio HAL, MediaCodec, CameraService |
| `L2-connectivity-network-expert` | netd, ConnectivityService, Wi-Fi HAL, Bluetooth, eBPF |
| `L2-kernel-gki-expert` | GKI modules, symbol list, Kconfig, `aarch64-abi` |
| `L2-bootloader-lk-expert` | LK/ABL fastboot, A/B slot, AVB, partition table |
| `L2-trusted-firmware-atf-expert` | ATF BL31, SMC handlers, PSCI, Trusty TEE |
| `L2-virtualization-pkvm-expert` | pKVM, AVF, Microdroid, crosvm, vsock IPC |

---

## Useful Commands

```bash
# Run the 100-case routing accuracy test suite
python3 tests/routing_accuracy/test_router.py

# Detect dirty skills from a git diff
git diff --name-only A14..A15 | python3 scripts/detect_dirty_pages.py --apply

# Generate migration impact report
python3 scripts/migration_impact.py --from A14 --to A15

# Validate dirty_pages.json schema
python3 scripts/validate_dirty_pages.py

# Lint all SKILL.md files against the template schema
python3 scripts/skill_lint.py

# Check pKVM / AVF support on a connected device
bash skills/L2-virtualization-pkvm-expert/scripts/check_pkvm_status.sh

# Validate an .rc file for syntax errors
python3 skills/L2-init-boot-sequence-expert/scripts/validate_rc_syntax.py <file.rc>

# Check AIDL interface versions
python3 skills/L2-hal-vendor-interface-expert/scripts/check_aidl_version.py hardware/interfaces/

# Check API compatibility across Android versions
python3 skills/L2-version-migration-expert/scripts/check_api_compatibility.py <before.txt> <after.txt>
```

---

## Project Status

This is **Beta v0.5** — Phase 4 is complete. All automation scripts are delivered and skills are validated against Android 15.

| Capability | Status |
|-----------|--------|
| 13 skills (L1 + 12 L2) with full SKILL.md, scripts, and references | ✅ Complete |
| Git-diff dirty page detection (`scripts/detect_dirty_pages.py`) | ✅ Complete |
| Automated migration impact reports (`scripts/migration_impact.py`) | ✅ Complete |
| SKILL.md schema linting (`scripts/skill_lint.py`) | ✅ Complete |
| Layer 3 OEM/SoC extension framework (template + guide) | ✅ Complete |
| Android 15 validation pass (all skills updated, delta summary) | ✅ Complete |
| 36 hindsight notes (HS-001–HS-036) including A16 forward intelligence | ✅ Complete |
| 100-case routing test suite (30 multi-skill scenarios) | ✅ Complete |

### Active Work (Phase 5)

| Goal | Plan |
|------|------|
| Android 16 validation pass | Update all skills for A16 deltas (GBL, kernel 6.12, APV codec, build changes) |
| GBL bootloader skill refresh | Expand bootloader skill for Generic Bootloader alongside LK |
| 16KB page size deep-dive | Migration guide with concrete audit steps |
| Live routing benchmark | Exit stub mode in test suite; target ≥95% accuracy |

See [ROADMAP.md](ROADMAP.md) for Phase 5 details.

---

## Reporting Gaps and Feedback

Found a wrong path? A missing forbidden action? A gap in a skill's coverage?

**Open a GitHub Issue** with:
- The task you gave the agent
- What path or skill it suggested
- What the correct answer should be
- Your Android version and SoC (if relevant)

For recurring insights from real BSP work, consider submitting a **pull request** with a new `memory/hindsight_notes/HS-NNN_your_insight.md`. See [CONTRIBUTING.md](CONTRIBUTING.md) for the format.

---

## Repository Layout

```
Android-Software/
├── AGENTS.md                          # Agent entry point — load this first
├── CLAUDE.md                          # Development standards (for contributors)
├── ANDROID_SW_OWNER_DEV_PLAN.md       # Architecture blueprint v1.4
├── ROADMAP.md                         # Phase roadmap v1.3
├── skills/
│   ├── L1-aosp-root-router/           # Intent-to-path router (40 mappings)
│   ├── L2-*/                          # 12 subsystem expert skills
│   │   ├── SKILL.md                   # Knowledge, triggers, forbidden actions
│   │   ├── scripts/                   # Automation tools (Bash/Python)
│   │   └── references/                # Deep-dive architecture docs
│   └── L3-TEMPLATE/                   # OEM/SoC extension template
├── memory/
│   ├── hindsight_notes/               # 36 persistent insights (HS-001–HS-036)
│   ├── cross_skill_triggers.md        # 12 multi-skill task patterns
│   └── dirty_pages.json               # Skill freshness tracking
├── scripts/
│   ├── validate_dirty_pages.py        # dirty_pages.json schema validator
│   ├── detect_dirty_pages.py          # Git-diff dirty page detection
│   ├── migration_impact.py            # Per-skill migration impact report
│   └── skill_lint.py                  # SKILL.md schema linter
├── tests/
│   └── routing_accuracy/
│       └── test_router.py             # 100-case ground-truth routing spec
└── references/
    ├── aosp_top_level_paths.md        # Canonical AOSP path → skill map
    ├── a14_to_a15_delta_summary.md    # A14→A15 per-skill impact summary
    └── l3_extension_guide.md          # Guide for adding OEM/SoC L3 skills
```

---

## Documentation

| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent routing entry point and global guardrails |
| `CLAUDE.md` | Coding standards for skill development and contribution |
| `CONTRIBUTING.md` | How to add hindsight notes, fix skills, and report gaps |
| `ANDROID_SW_OWNER_DEV_PLAN.md` | Full architecture blueprint and SKILL.md template |
| `ROADMAP.md` | Phased roadmap with deliverables, gate criteria, and milestone status |

---

*Beta v0.5 — Phase 4 complete (2026-04-08). Phase 5 active: A16 readiness & quality hardening. Built for Android SW Owners and BSP engineers.*

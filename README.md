# Android Software Owner — AI Agent Skill Set

> **Alpha v0.1** — Field-tested by BSP engineers. Gaps expected and welcomed.
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
python3 scripts/validate_dirty_pages.py
```

Then manually set `status: "dirty"` for affected skills in `memory/dirty_pages.json`. This flags the agent to treat those skills' content as potentially stale.

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

# Validate dirty_pages.json schema
python3 scripts/validate_dirty_pages.py

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

## Alpha Status

This is **Alpha v0.1**. The skill content is complete and usable today. Known limitations:

| Limitation | Plan |
|-----------|------|
| No automated routing engine — the AI agent does the routing using the SKILL.md spec | Phase 4: `detect_dirty_pages.py`, routing benchmark |
| Skills validated against Android 14; A15 delta not yet formalized | Phase 4: A15 validation pass |
| No OEM/SoC-specific Layer 3 skills (Qualcomm, MediaTek, etc.) | Phase 4: L3 extension framework |
| Routing accuracy formally unmeasured (stub router in test suite) | Phase 4: live router benchmark |

See [ROADMAP.md](ROADMAP.md) for the Phase 4 plan.

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
├── ROADMAP.md                         # Phase roadmap v1.2
├── skills/
│   ├── L1-aosp-root-router/           # Intent-to-path router (40 mappings)
│   └── L2-*/                          # 12 subsystem expert skills
│       ├── SKILL.md                   # Knowledge, triggers, forbidden actions
│       ├── scripts/                   # Automation tools (Bash/Python)
│       └── references/                # Deep-dive architecture docs
├── memory/
│   ├── hindsight_notes/               # 22 persistent insights (HS-001–HS-022)
│   ├── cross_skill_triggers.md        # 12 multi-skill task patterns
│   └── dirty_pages.json               # Skill freshness tracking
├── scripts/
│   └── validate_dirty_pages.py        # Schema validator
├── tests/
│   └── routing_accuracy/
│       └── test_router.py             # 100-case ground-truth routing spec
└── references/
    └── aosp_top_level_paths.md        # Canonical AOSP path → skill map
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

*Alpha v0.1 — Phase 3 complete. Built for Android SW Owners and BSP engineers.*

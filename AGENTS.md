# Android Software Owner — Agent Routing Entry Point

> **Version:** v1.4 (Alpha v0.1)
> Load this file first. It is the master entry point for the Android SW Owner Agent.

---

## Agent Roles

| Agent | Responsibility |
|-------|---------------|
| **Claude** | All implementation work, code execution, skill content authoring |
| **Gemini** | Monitoring, consults, patch review, architectural oversight |

---

## Master Routing Protocol

**Every task MUST pass through the Layer 1 router first. No exceptions.**

```
Step 1: Load  skills/L1-aosp-root-router/SKILL.md
Step 2: Parse user intent → identify AOSP path(s)
Step 3: Load the correct L2 skill(s) in priority order
Step 4: Emit [L1 ROUTING DECISION] block before answering
Step 5: Yield control to L2 expert(s)
```

Do **not** answer subsystem questions from L1. Route, then yield.

---

## L1 Entry Point

- **Skill:** `L1-aosp-root-router`
- **File:** `skills/L1-aosp-root-router/SKILL.md`
- **Covers:** All 40 AOSP root path mappings, 19 cross-domain forbidden actions

---

## L2 Expert Skills

| Skill | Path Scope | Load When |
|-------|-----------|-----------|
| `L2-build-system-expert` | `build/`, `Android.bp`, `*.mk` | Build errors, Soong, VNDK |
| `L2-security-selinux-expert` | `system/sepolicy/`, `*.te` | `avc: denied`, new domain, neverallow |
| `L2-hal-vendor-interface-expert` | `hardware/interfaces/`, `vendor/` | AIDL/HIDL, Treble, VNDK boundary |
| `L2-framework-services-expert` | `frameworks/base/`, `frameworks/native/` | SystemServer, @SystemApi, ANR, Binder |
| `L2-init-boot-sequence-expert` | `system/core/init/`, `*.rc` | Boot sequence, `.rc` syntax, ueventd |
| `L2-version-migration-expert` | Cross-cutting (diff analysis) | A14→A15, 16KB pages, API compat |
| `L2-multimedia-audio-expert` | `frameworks/av/`, `hardware/interfaces/audio/` | AudioFlinger, Camera, MediaCodec |
| `L2-connectivity-network-expert` | `packages/modules/Connectivity/`, `system/netd/` | netd, Wi-Fi, Bluetooth, eBPF |
| `L2-kernel-gki-expert` | `kernel/`, `drivers/` | GKI modules, symbol list, Kconfig |
| `L2-bootloader-lk-expert` | `bootloader/lk/`, `bootable/bootloader/` ¹ | LK/ABL, fastboot, A/B slots, AVB |
| `L2-trusted-firmware-atf-expert` | `atf/`, `trusty/` ¹ | ATF BL31, SMC, PSCI, Trusty TEE |
| `L2-virtualization-pkvm-expert` | `packages/modules/Virtualization/`, `external/crosvm/` | pKVM, AVF, Microdroid, vsock |

> ¹ Vendor-supplied paths — not in standard AOSP. Routing is by subsystem intent, not path presence.

---

## Routing Priority Order

When multiple skills are needed, load in this order:

```
Security > Build > HAL > Framework > Init > Bootloader > ATF > Virtualization > Migration > Media > Connectivity > Kernel
```

Exception: for boot failure diagnosis, use `Init > Kernel > Security > Bootloader`.

For common multi-skill task patterns, see: `memory/cross_skill_triggers.md`

---

## Global Guardrails

1. **Path Discipline** — Never assert an AOSP path without verifying it in the router or via `read_file`. Wrong paths are worse than no answer.
2. **Forbidden Actions** — Every SKILL.md contains a Forbidden Actions list. These are hard rules, not suggestions.
3. **Vendor Path Awareness** — `bootloader/lk/`, `atf/`, `trusty/` are not in standard AOSP. Confirm BSP layout before citing paths. See Forbidden Action #16 in L1 router.
4. **Hindsight Memory** — After solving a problem, check `memory/hindsight_notes/` for existing insights. After discovering something new, record it as `HS-NNN_description.md`.
5. **Dirty Pages** — Before using a skill on a new Android version, check `memory/dirty_pages.json`. A `dirty` status means the skill content may be stale.
6. **Handoff Protocol** — When handing off between skills, emit the skill's handoff marker (e.g., `[L2 SECURITY → HANDOFF]`) before loading the next skill.

---

## Memory System

| File / Directory | Purpose |
|-----------------|---------|
| `memory/hindsight_notes/` | 22 persistent insights from past tasks (HS-001–HS-022) |
| `memory/cross_skill_triggers.md` | 12 named multi-skill task patterns |
| `memory/dirty_pages.json` | Per-skill freshness tracking across Android versions |

---

## Validation Commands

```bash
# Validate dirty_pages.json schema (run after adding/removing skills)
python3 scripts/validate_dirty_pages.py

# Run 100-case routing accuracy test suite
python3 tests/routing_accuracy/test_router.py
```

---

*Agent entry point v1.4 — Alpha v0.1. Phase 3 complete: 12 L2 skills, 22 hindsight notes, 100-case test suite.*

# HS-004: init.rc Service Class Ordering Determines Boot Timing

**Category:** Init / Boot Sequence
**Skills involved:** L2-init-boot-sequence-expert
**Android versions:** All

## Insight

The `class` attribute in an `.rc` service definition determines **when** the service starts relative to boot phases. Common classes and their start trigger:

| Class | Started by | Typical use |
|-------|-----------|-------------|
| `core` | `class_start core` in `init.rc` | Critical early daemons (`logd`, `servicemanager`) |
| `main` | `class_start main` after `post-fs-data` | Most system daemons |
| `hal` | `class_start hal` | HAL servers |
| `late_start` | `class_start late_start` after `boot` | Non-critical services |

**Common mistake:** Using `class core` for a daemon that depends on `/data` being mounted. `core` services start before `post-fs-data`, so they cannot access `/data/`. Use `class main` instead and add `after post-fs-data` if timing matters.

## Why This Matters

Incorrect class assignment causes either:
- Service crash (trying to open `/data/...` before mount)
- Delayed startup (using `late_start` for a HAL that clients need at `boot`)

## Trigger

Always verify service class when a new `.rc` file is reviewed. Use `validate_rc_syntax.py` from `L2-init-boot-sequence-expert/scripts/`.

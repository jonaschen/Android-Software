---
name: <oem-or-soc>-<subsystem>-expert
layer: L3
path_scope: vendor/<oem>/, device/<oem>/
version: 1.0.0
android_version_tested: Android 15
parent_skill: <L2-parent-skill-name>
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `vendor/<oem>/` | OEM-proprietary code, BSP blobs, vendor HALs |
| `device/<oem>/<device>/` | Device-specific configuration, BoardConfig, overlays |
| <!-- Add OEM-specific paths below --> | |

### Inherited Paths (from parent L2 skill)

This L3 skill **extends** the parent L2 skill's path scope with OEM/SoC-specific paths.
The parent skill handles generic AOSP paths; this skill handles vendor-specific deviations.

| Parent L2 Path | L3 Override / Extension |
|----------------|------------------------|
| <!-- e.g. hardware/interfaces/ --> | <!-- e.g. vendor/<oem>/interfaces/ --> |

---

## Trigger Conditions

Load this skill when the task involves:
- OEM/SoC-specific behavior that the parent L2 skill cannot resolve
- Vendor-proprietary paths not present in standard AOSP
- BSP-specific build configurations or toolchain quirks
- Device-specific hardware enablement or board bringup
- Vendor HAL implementations that diverge from AOSP reference HALs

### Escalation from Parent L2

The parent L2 skill should hand off to this L3 skill when:
- The user's query references `vendor/<oem>/` or `device/<oem>/` paths
- The issue involves SoC-specific hardware (GPU, modem, DSP, ISP)
- Standard AOSP guidance does not apply due to vendor modifications

---

## Architecture Intelligence

<!-- Document OEM/SoC-specific architecture here. Examples:
     - SoC boot flow differences from standard AOSP
     - Proprietary HAL interface extensions
     - Vendor-specific build system overlays
     - Chipset-specific driver architecture
-->

### SoC / Platform Overview

```
<!-- Diagram showing the OEM/SoC-specific architecture layers -->
```

### Vendor Deviations from AOSP

| AOSP Component | Vendor Deviation | Impact |
|----------------|-----------------|--------|
| <!-- e.g. AudioFlinger --> | <!-- e.g. Custom DSP offload path --> | <!-- e.g. Different audio routing --> |

---

## Forbidden Actions

1. Do NOT modify files under the parent L2 skill's AOSP paths without consulting the parent skill first.
2. Do NOT assume vendor-specific paths exist in standard AOSP — always verify with the OEM BSP layout.
3. Do NOT bypass Treble/VNDK boundaries by linking vendor code directly against system-private libraries.
4. Do NOT commit OEM-proprietary source code, binary blobs, or NDA-covered material to public repositories.
5. Do NOT override AOSP SELinux policy with permissive vendor domains without explicit security review.
6. Do NOT assume SoC-specific kernel config applies to other SoC families — always scope advice to the target platform.
7. Do NOT modify GKI kernel vmlinux symbols from the vendor tree — symbol additions go through the upstream KMI process.

---

## Tool Calls

<!-- List any OEM/SoC-specific scripts or tools this skill provides -->

| Tool | Purpose | Example |
|------|---------|---------|
| <!-- e.g. scripts/check_vendor_hal.sh --> | <!-- e.g. Verify vendor HAL registration --> | <!-- e.g. bash scripts/check_vendor_hal.sh audio --> |

---

## Handoff Rules

| Condition | Emit | Target Skill |
|-----------|------|-------------|
| Task leaves OEM/SoC-specific scope, needs generic AOSP guidance | `[HANDOFF → <parent-L2-skill>]` | Parent L2 skill |
| Task requires routing to a different subsystem entirely | `[HANDOFF → aosp-root-router]` | `L1-aosp-root-router` |
| Task involves a different OEM/SoC platform | `[HANDOFF → L3-<other-oem>-*]` | Other L3 skill |

---

## References

| Document | Path | Description |
|----------|------|-------------|
| <!-- e.g. SoC Platform Guide --> | `references/<oem>_platform_guide.md` | <!-- e.g. SoC boot flow, memory map, peripheral list --> |
| Parent L2 Skill | `skills/<parent-L2-skill>/SKILL.md` | Generic AOSP guidance for this subsystem |

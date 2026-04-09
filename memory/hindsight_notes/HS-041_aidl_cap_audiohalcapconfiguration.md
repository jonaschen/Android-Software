---
id: HS-041
title: "AIDL CAP fully implemented in A16 via AudioHalCapConfiguration.aidl"
skill: L2-multimedia-audio-expert
date: 2026-04-10
source: research-session
---

## Insight

Android 16 closes the Configurable Audio Policy (CAP) AIDL gap that existed
since Android 14 (documented in HS-025, HS-032, HS-035). The specific new
AIDL interface is `AudioHalCapConfiguration.aidl`.

Key mechanism change:
- **Before A16**: Audio policy service parsed CAP engine configuration from XML
  files in the vendor partition.
- **A16+**: Audio policy service obtains CAP engine info directly via AIDL Audio
  HAL APIs (`AudioHalCapConfiguration.aidl`), eliminating the XML parsing path.

This means:
1. Vendor audio HALs targeting A16 must implement the new AIDL CAP interfaces.
2. Legacy XML-based CAP configuration is deprecated in favor of AIDL.
3. Cuttlefish Auto target has been migrated to CAP AIDL as reference.

## Lesson

The multimedia-audio skill's Architecture Intelligence section should document
the A16 CAP AIDL migration path:
- Path: `hardware/interfaces/audio/aidl/` (AudioHalCapConfiguration.aidl)
- The XML→AIDL migration is mandatory for vendors upgrading audio HALs to A16.
- Automotive audio configurations are the primary beneficiary.

## Cross-Skill Impact

- **L2-hal-vendor-interface-expert**: New AIDL interface must be in the HAL
  version tracking matrix.
- **L2-version-migration-expert**: CAP XML→AIDL is an A16 migration checklist item.

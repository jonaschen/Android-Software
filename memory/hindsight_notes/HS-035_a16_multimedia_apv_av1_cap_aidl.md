---
id: HS-035
title: "Android 16 multimedia: APV codec, AV1 transition, CAP AIDL fixed"
skill: L2-multimedia-audio-expert
date: 2026-04-08
source: research-session
---

## Insight

Android 16 brings several significant multimedia changes:

1. **Configurable Audio Policy (CAP) AIDL fixed**: The CAP AIDL gap that existed
   in Android 14 and 15 (documented in HS-025 and HS-032) is now resolved in
   Android 16. Missing AIDL definitions have been added and the CAP configuration
   loading mechanism has been changed. Cuttlefish Auto is now converted to CAP
   AIDL. This closes a long-standing gap for automotive audio routing.

2. **APV codec support**: Advanced Professional Video codec for high-bitrate
   intra-frame video. Targets professional video workflows.

3. **AV1 transition**: Platform is transitioning toward AV1 from VP8/VP9/H.264
   as the preferred codec. This affects MediaCodec defaults and codec selection
   heuristics.

4. **HDR enhancements**: SDR fallback capability via Media3 ExoPlayer, enhanced
   HDR screenshot support, HLG and DolbyVision capture support.

5. **Media Quality Framework**: Standardized API for Android TV picture/audio
   quality — per-stream, per-user, per-input-type settings.

## Lesson

The CAP AIDL fix in A16 is a critical update for the multimedia skill's
Architecture Intelligence section, which currently documents the A14/A15 gap.
The skill should be updated to note that CAP AIDL is fully functional starting
A16, and automotive audio policy can now use the AIDL backend.

## Cross-Skill Impact

- **L2-hal-vendor-interface-expert**: CAP AIDL completion means vendor HALs
  should implement the AIDL audio policy interfaces for A16 targets.
- **L2-version-migration-expert**: AV1 transition and CAP AIDL fix are A16 deltas.

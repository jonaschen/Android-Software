---
id: HS-039
title: "Android 16 connectivity: unified ranging module, AIS Bluetooth, IMS APIs"
skill: L2-connectivity-network-expert
date: 2026-04-11
source: research-session
---

## Insight

Android 16 introduces several connectivity changes beyond the A15 baseline
(APF v6, 802.11az RTT, proprietary NCI):

### 1. Unified Ranging Module

A new ranging module aggregates APIs for multiple ranging technologies:
- Ultra-wideband (UWB)
- Bluetooth Channel Sounding
- Bluetooth RSSI ranging
- Wi-Fi Round Trip Time (RTT)

This is a new mainline module that unifies previously separate ranging APIs.
Path: `packages/modules/Uwb/` (expanded to cover non-UWB ranging)

### 2. Android Information Service (AIS) — Bluetooth GATT

A new Bluetooth GATT characteristic that lets Bluetooth devices read the
Android API level. This enables Bluetooth peripherals to adapt behavior
based on the connected Android version.
Path: `packages/modules/Bluetooth/`

### 3. IMS Service API Expansion

Multiple new system APIs for privileged apps supporting IMS services:
- Traffic session management
- EPS fallback triggers
- EmergencyCallbackModeListener system API for IMS module to get emergency
  callback mode state through a callback

Path: `packages/services/Telephony/`, `frameworks/base/telephony/`

### 4. Wi-Fi Hotspot Disconnect Callback

New `SoftApCallback#onClientsDisconnected` method providing disconnect reasons.
Path: `packages/modules/Wifi/`

### 5. Bluetooth Bond Loss Handling

Two new Bluetooth intents for improved bond loss awareness:
- `ACTION_KEY_MISSING`: broadcast when remote bond loss is detected
- `ACTION_ENCRYPTION_CHANGE`: broadcast when encryption status, algorithm, or
  key size changes on the link

These give apps greater visibility into Bluetooth security state transitions.
Path: `packages/modules/Bluetooth/`

### 6. Bluetooth LE Audio Sharing

Bluetooth Audio Sharing allows connecting multiple LE Audio headphones
simultaneously. Requires Bluetooth LE-supported earbuds. This is a
framework-level multi-device audio routing change.
Path: `packages/modules/Bluetooth/`, `frameworks/av/`

### 7. CompanionDeviceManager removeBond API

New public `removeBond(int)` API in `CompanionDeviceManager` allows apps
targeting A16 to unpair Bluetooth devices programmatically via CDM
associations.
Path: `frameworks/base/core/`

## Lesson

The connectivity skill should be updated for A16 to document:
1. The unified ranging module as a new cross-technology API surface
2. AIS as a new Bluetooth GATT service that BSP teams need to support
3. IMS API expansion for telephony framework integrators
4. Bond loss intents (ACTION_KEY_MISSING, ACTION_ENCRYPTION_CHANGE)
5. LE Audio Sharing multi-device audio routing
6. CDM removeBond API for programmatic Bluetooth unpairing

The ranging module unification is particularly significant — it moves from
technology-specific APIs (UWB SDK, WiFi RTT API) to a single ranging
abstraction. This affects how BSP teams implement and test ranging HALs.

## Cross-Skill Impact

- **L2-hal-vendor-interface-expert**: Ranging HAL interfaces may be unified;
  UWB, BT, and WiFi HALs affected.
- **L2-framework-services-expert**: IMS APIs are new SystemApi surfaces;
  telephony service lifecycle changes.
- **L2-version-migration-expert**: Unified ranging and AIS are A16 delta items.

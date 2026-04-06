---
id: HS-029
title: "Android 16 connectivity: DHCPv6 PD and IPv6 local network permission"
skill: L2-connectivity-network-expert
date: 2026-04-07
source: research-session
---

## Insight

Android 16 introduces two significant connectivity changes:

1. **DHCPv6 Prefix Delegation (PD)**: Rolling out via Google Play System Update
   to Android 11+ devices. Allows tethered devices, wearables, and VMs to share
   a dedicated IPv6 prefix without NAT64 workarounds. This impacts AVF VMs
   running on the host device (cross-cuts with pKVM skill).

2. **IPv6 local network traffic classification**: Android 16 classifies IPv6
   link-local addresses, directly-connected routes, and multicast addresses as
   "local network" traffic. Access is gated by a **new runtime permission**,
   enhancing privacy for local network discovery.

3. **Adaptive Connectivity split** (QPR3): Wi-Fi stability and battery saving
   are split into separate controls, replacing the monolithic toggle.

## Lesson

For BSP engineers working on connectivity, the DHCPv6 PD change may interact
with vendor tethering offload implementations (offloadController). Verify
that hardware offload engines handle the new PD-derived prefixes correctly.

The new local network permission affects apps doing mDNS, UPnP, or any
link-local discovery — vendor apps (Cast, Wi-Fi Direct) need permission audit.

## Cross-Skill Impact

- **L2-virtualization-pkvm-expert**: AVF VMs can now get proper IPv6 via PD.
- **L2-framework-services-expert**: New runtime permission for local network.
- **L2-security-selinux-expert**: Permission enforcement may need policy rules.

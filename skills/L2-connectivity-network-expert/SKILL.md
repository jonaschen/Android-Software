---
name: connectivity-network-expert
layer: L2
path_scope: packages/modules/Connectivity/, system/netd/, system/bt/, packages/modules/Wifi/, hardware/interfaces/wifi/, hardware/interfaces/bluetooth/
version: 1.0.0
android_version_tested: Android 14
parent_skill: aosp-root-router
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `packages/modules/Connectivity/` | Network stack mainline module — ConnectivityService, VPN, DNS |
| `system/netd/` | Network daemon — routing, firewall, NAT, DNS resolver |
| `packages/modules/Wifi/` | Wi-Fi mainline module — WifiService, WifiManager |
| `packages/apps/Bluetooth/` | Bluetooth app and GattService |
| `system/bt/` | BlueDroid/Fluoride Bluetooth stack |
| `hardware/interfaces/wifi/` | Wi-Fi HAL AIDL interfaces |
| `hardware/interfaces/bluetooth/` | Bluetooth HAL AIDL interfaces |
| `frameworks/base/telecomm/` | Telephony — coordinate with framework skill |

---

## Trigger Conditions

Load this skill when the task involves:
- Network routing failures — missing routes, wrong interface
- `netd` errors — firewall rules, NAT, DNS resolution
- ConnectivityService — network selection, scoring, VPN
- Wi-Fi issues — association, DHCP, HAL errors
- Bluetooth pairing, GATT, A2DP, HFP failures
- `iptables` / `nftables` rules applied by netd
- DNS over HTTPS / Private DNS configuration
- Network namespace or VPN tunnel issues
- Wi-Fi HAL AIDL (`IWifi`, `IWifiChip`, `IWifiStaIface`)
- Bluetooth HAL (`IBluetoothHci`, `IBluetoothGatt`)
- `ConnectivityManager`, `NetworkRequest`, `NetworkCallback` API

---

## Architecture Intelligence

### Network Stack Architecture

```
App
 │  ConnectivityManager API
 ▼
ConnectivityService  (packages/modules/Connectivity/service/)
 │  Network scoring, selection, VPN management
 │  NetworkRequest matching
 ▼
netd  (system/netd/)
 │  Routing table management (/proc/net/route)
 │  Firewall (iptables / nftables)
 │  DNS resolver (DoH, DoT, plain DNS)
 │  Interface configuration (ip addr, ip link)
 ▼
Kernel network stack
 │  TCP/IP, UDP, netfilter
 ▼
Network interfaces (wlan0, rmnet0, eth0, ...)
 │
Wi-Fi HAL / Modem
```

### netd Architecture

```
netd exposes two interfaces:
  1. Binder: INetd AIDL  ← ConnectivityService calls this
  2. Netlink: kernel socket for interface/route events

Key netd subsystems:
  RouteController   → manages routing tables per network/UID
  BandwidthController → iptables quotas (data saver, metered)
  FirewallController  → per-UID firewall rules
  DnsResolver       → recursive DNS with DoH/DoT support
  TetherController  → NAT and tethering setup
```

**Route debugging:**
```bash
adb shell ip route show table all      # All routing tables
adb shell ip rule list                 # Policy routing rules (per-UID)
adb shell ndc network routes           # netd route dump
```

### ConnectivityService Network Selection

```
NetworkRequest (from app)
      │ criteria: WIFI, CELLULAR, VPN, ...
      ▼
ConnectivityService evaluates registered networks
      │
Network agents (WifiNetworkAgent, CellularNetworkAgent)
      │ report: validated, score, capabilities
      ▼
Best network selected → satisfies NetworkRequest
      │
Network becomes "default" → default route set by netd
```

**Network validation:** ConnectivityService checks reachability via HTTP probe to `connectivitycheck.gstatic.com`. Failure → network marked "not validated" → deprioritized.

### Wi-Fi Stack

```
WifiManager API (app)
      │
WifiService  (packages/modules/Wifi/service/)
      │  state machine: ScanMode, ConnectMode, SoftApMode
      ▼
Wi-Fi HAL (hardware/interfaces/wifi/)
      │  IWifi, IWifiChip, IWifiStaIface AIDL
      ▼
wpa_supplicant (external/wpa_supplicant_8/)
      │  802.11 association, WPA/WPA2/WPA3
      ▼
Kernel Wi-Fi driver (cfg80211, mac80211)
```

**Common Wi-Fi HAL failure modes:**
- `IWifiChip.createStaIface()` returns error → chip not in STA mode, or firmware not loaded.
- `IWifiStaIface.startBackgroundScan()` times out → driver scan state machine stuck.

### Bluetooth Stack

```
Bluetooth app (packages/apps/Bluetooth/)
      │  BluetoothAdapter, BluetoothDevice Java API
      ▼
GattService / AdapterService
      │
BlueDroid/Fluoride (system/bt/)
      │  HCI command handling, L2CAP, SDP, RFCOMM, GATT
      ▼
Bluetooth HAL (hardware/interfaces/bluetooth/)
      │  IBluetoothHci AIDL
      ▼
Kernel HCI driver (/dev/ttyHS*, /dev/btusb*)
```

---

## Forbidden Actions

1. **Forbidden:** Modifying iptables rules directly on device without going through `netd` — direct iptables manipulation bypasses netd's rule management and will be overwritten.
2. **Forbidden:** Editing Wi-Fi supplicant configuration outside of `WifiService` — `wpa_supplicant.conf` is managed by WifiService; direct edits are overwritten at next connection.
3. **Forbidden:** Routing Bluetooth kernel driver issues (`hci_uart`, `btusb`) to this skill — kernel driver changes belong to `L2-kernel-gki-expert`.
4. **Forbidden:** Adding new network capabilities to `NetworkCapabilities` without understanding backwards compatibility — capability changes can break existing `NetworkRequest` matching.
5. **Forbidden:** Treating `netd` and `ConnectivityService` as the same component — `netd` executes kernel-level network operations; `ConnectivityService` is the policy layer above it.
6. **Forbidden:** Making Wi-Fi or Bluetooth HAL AIDL changes without bumping the interface version — route to `L2-hal-vendor-interface-expert` for versioning procedure.

---

## Tool Calls

```bash
# Dump ConnectivityService state
adb shell dumpsys connectivity

# Dump Wi-Fi state
adb shell dumpsys wifi | head -100

# Dump Bluetooth state
adb shell dumpsys bluetooth_manager

# Check routing tables
adb shell ip route show table all

# Watch netd logs
adb logcat -s netd NetworkController

# Check DNS resolution
adb shell nslookup google.com

# Test network validation
adb shell curl -s "http://connectivitycheck.gstatic.com/generate_204" -o /dev/null -w "%{http_code}"

# List Wi-Fi HAL AIDL services
adb shell service list | grep wifi
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| Wi-Fi or Bluetooth HAL AIDL version bump | `L2-hal-vendor-interface-expert` |
| SELinux denial for netd or wpa_supplicant | `L2-security-selinux-expert` |
| Kernel Wi-Fi/BT driver issue | `L2-kernel-gki-expert` |
| Build failure in `packages/modules/Connectivity/` | `L2-build-system-expert` |
| ConnectivityService `.rc` startup issue | `L2-init-boot-sequence-expert` |

Emit `[L2 CONNECTIVITY → HANDOFF]` before transferring.

---

## References

- `references/netd_connectivity_architecture.md` — netd subsystem breakdown and ConnectivityService interaction.
- `packages/modules/Connectivity/README.md` — mainline module documentation.
- `system/netd/README.md` — netd design doc.
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

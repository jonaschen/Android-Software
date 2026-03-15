# netd and ConnectivityService Architecture

> Android 14 — `system/netd/`, `packages/modules/Connectivity/`

## Component Overview

```
App
 │  ConnectivityManager / NetworkCallback
 ▼
ConnectivityService  ← Java; runs in system_server
 │  INetd AIDL (Binder)
 ▼
netd  ← Native C++ daemon; PID outside system_server
 │  Netlink socket (kernel events)
 │  iptables/nftables
 ▼
Linux Kernel network stack
 ├── Routing subsystem (ip route)
 ├── Netfilter (iptables / nftables)
 ├── Network namespaces
 └── Network interfaces (wlan0, rmnet0, tun0, ...)
```

## ConnectivityService Responsibilities

- **Network selection:** Scores registered networks and selects the best one for each `NetworkRequest`.
- **Network agents:** Each network type (Wi-Fi, Cellular, VPN) registers a `NetworkAgent` that reports capabilities and linkProperties.
- **VPN management:** Establishes VPN tunnels, routes traffic through `tun0`.
- **Firewall policy:** Translates app-level policies (data saver, battery saver) to netd rules.
- **DNS resolver:** Delegates DNS configuration to `netd`'s resolver component.

## netd Subsystem Breakdown

### RouteController
Manages per-network routing tables and per-UID policy routing.

```
Android uses policy routing (ip rule) to implement per-UID network selection:

Table 1000 (main)      ← default gateway for "default network"
Table 1001..1xxx       ← per-network tables (one per network ID)
Table 97               ← per-UID explicit network selection
Table 98               ← per-UID VPN routing
Table 99               ← VPN fallthrough

ip rule:
  priority 0:   lookup local
  priority 10000: from all lookup <UID-specific table>
  priority 17000: from all lookup <VPN table>
  priority 22000: from all lookup <per-network table>
  priority 23000: from all lookup main (default)
```

### BandwidthController
Implements data quotas and metered network restrictions via iptables.

```
Chains:
  bw_INPUT           ← Counts incoming bytes per UID
  bw_OUTPUT          ← Counts outgoing bytes per UID
  bw_costly_shared   ← Blocks UID if over data limit
  bw_data_saver      ← Blocks background traffic when data saver active
```

### FirewallController
Per-UID network access control.

```
Modes:
  ALLOWLIST mode: Block all, allow listed UIDs
  DENYLIST mode:  Allow all, block listed UIDs

Chains:
  fw_INPUT, fw_OUTPUT, fw_FORWARD
  fw_dozable         ← Doze mode restrictions
  fw_powersave       ← Battery saver restrictions
  fw_standby         ← App standby restrictions
```

### DnsResolver
Full-featured recursive DNS resolver with Private DNS (DoT/DoH) support.

```
Configuration per network:
  - Plaintext DNS servers
  - Private DNS hostname (DoT)
  - DoH server template

Resolution order:
  1. /etc/hosts
  2. mDNS (if configured)
  3. DNS cache
  4. Recursive resolution (DoT/DoH/plaintext)
```

## Wi-Fi Stack Architecture

```
WifiManager (app API)
       │
WifiService (packages/modules/Wifi/service/)
       │ manages Wi-Fi state machine
       ├── ScanRequestProxy
       ├── WifiConnectivityManager
       └── ActiveModeManager
              │
       WifiNative (JNI bridge)
              │ AIDL
       Wi-Fi HAL (hardware/interfaces/wifi/)
       IWifi → IWifiChip → IWifiStaIface
              │
       wpa_supplicant (external/wpa_supplicant_8/)
              │ cfg80211 nl80211
       Kernel Wi-Fi driver
              │
       Wi-Fi chip firmware
```

**Key state: STA (Station) mode** = connected to AP. WifiService maintains a state machine (DisconnectedState, ConnectingState, ConnectedState, ...).

## Bluetooth Architecture

```
BluetoothAdapter (app API)
       │
GattService / AdapterService (packages/apps/Bluetooth/)
       │ JNI
BlueDroid/Fluoride (system/bt/)
  ├── GD (Gabeldorsche) — new modular stack
  ├── HCI layer — communicates with controller
  ├── L2CAP — logical link control
  ├── SDP — service discovery
  ├── RFCOMM — serial port emulation
  ├── GATT — BLE attribute protocol
  └── Profiles: A2DP, HFP, HID, ...
       │ AIDL
Bluetooth HAL (hardware/interfaces/bluetooth/)
IBluetoothHci — send/receive HCI packets
       │
Kernel HCI driver
  ├── UART: hci_uart (/dev/ttyHS*)
  ├── USB: btusb
  └── SDIO: hci_sdio
```

## Network Request Lifecycle

```java
// App registers a network request
ConnectivityManager cm = ...;
NetworkRequest request = new NetworkRequest.Builder()
    .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
    .build();

NetworkCallback callback = new NetworkCallback() {
    @Override public void onAvailable(Network network) { ... }
    @Override public void onLost(Network network) { ... }
};

cm.requestNetwork(request, callback);

// Internal flow:
// 1. ConnectivityService receives request
// 2. Scores all registered NetworkAgents against the request
// 3. Best matching network → callback.onAvailable()
// 4. netd sets routing so traffic from app goes through selected network
```

## Diagnostic Commands

```bash
# Full connectivity state
adb shell dumpsys connectivity

# Routing tables
adb shell ip route show table all | grep -v "^$"

# Policy routing rules
adb shell ip rule list

# Firewall chains
adb shell iptables -L -n -v | grep -A5 "bw_OUTPUT\|fw_OUTPUT"

# DNS configuration per network
adb shell dumpsys dnsresolver

# Wi-Fi connection details
adb shell dumpsys wifi | grep -A10 "mCurrentScanResult\|SSID\|BSSID"

# Bluetooth bonded devices
adb shell dumpsys bluetooth_manager | grep -A3 "Bonded"

# netd log (verbose)
adb logcat -s netd NetworkController RouteController
```

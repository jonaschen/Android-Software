#!/usr/bin/env bash
# dump_netd_rules.sh — netd and ConnectivityService diagnostic snapshot
#
# Captures network state from a connected Android device:
#   - Routing tables (all tables)
#   - Policy routing rules (per-UID)
#   - iptables/nftables chains managed by netd
#   - ConnectivityService network list and scoring
#   - DNS resolver configuration
#   - Wi-Fi and Bluetooth state summary
#
# Usage:
#   ./dump_netd_rules.sh [output_dir]
#   ./dump_netd_rules.sh /tmp/netd_dump/

set -euo pipefail

OUTPUT_DIR="${1:-/tmp/netd_dump_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$OUTPUT_DIR"

echo "=== dump_netd_rules.sh ==="
echo "Output: $OUTPUT_DIR"
echo ""

if ! adb devices | grep -q "device$"; then
    echo "ERROR: No ADB device connected."
    exit 1
fi

# ─── 1. Routing tables ───────────────────────────────────────────────────────
echo "[1] Routing tables (all)..."
adb shell ip route show table all > "$OUTPUT_DIR/routes_all.txt" 2>&1
echo "  Saved: routes_all.txt"

# ─── 2. Policy routing rules ─────────────────────────────────────────────────
echo "[2] Policy routing rules (ip rule)..."
adb shell ip rule list > "$OUTPUT_DIR/ip_rules.txt" 2>&1
echo "  Saved: ip_rules.txt"

# ─── 3. Network interfaces ───────────────────────────────────────────────────
echo "[3] Network interfaces..."
adb shell ip addr show > "$OUTPUT_DIR/ip_addr.txt" 2>&1
echo "  Saved: ip_addr.txt"

# ─── 4. ConnectivityService dump ─────────────────────────────────────────────
echo "[4] ConnectivityService state..."
adb shell dumpsys connectivity > "$OUTPUT_DIR/connectivity_dump.txt" 2>&1
echo "  Saved: connectivity_dump.txt"

# ─── 5. netd state via ndc ───────────────────────────────────────────────────
echo "[5] netd network list (ndc)..."
adb shell cmd netpolicy list wifi-networks > "$OUTPUT_DIR/netpolicy.txt" 2>&1 || true
adb shell dumpsys netd > "$OUTPUT_DIR/netd_dump.txt" 2>&1 || true
echo "  Saved: netd_dump.txt, netpolicy.txt"

# ─── 6. DNS resolver state ───────────────────────────────────────────────────
echo "[6] DNS resolver..."
adb shell dumpsys dnsresolver > "$OUTPUT_DIR/dns_resolver.txt" 2>&1 || true
adb shell getprop | grep -i "dns\|net.dns" > "$OUTPUT_DIR/dns_props.txt" 2>&1 || true
echo "  Saved: dns_resolver.txt, dns_props.txt"

# ─── 7. Wi-Fi state summary ──────────────────────────────────────────────────
echo "[7] Wi-Fi state summary..."
adb shell dumpsys wifi | head -80 > "$OUTPUT_DIR/wifi_summary.txt" 2>&1
echo "  Saved: wifi_summary.txt"

# ─── 8. Bluetooth state summary ──────────────────────────────────────────────
echo "[8] Bluetooth state summary..."
adb shell dumpsys bluetooth_manager | head -50 > "$OUTPUT_DIR/bt_summary.txt" 2>&1 || true
echo "  Saved: bt_summary.txt"

# ─── 9. Recent netd logcat ───────────────────────────────────────────────────
echo "[9] Capturing 5s netd logcat..."
timeout 5 adb logcat -s "netd:V" "NetworkController:V" "ConnectivityService:V" \
    > "$OUTPUT_DIR/netd_logcat.txt" 2>&1 || true
echo "  Saved: netd_logcat.txt"

# ─── 10. Quick summary ───────────────────────────────────────────────────────
echo ""
echo "[SUMMARY] Default network:"
adb shell dumpsys connectivity 2>/dev/null \
    | grep -A5 "default network\|CONNECTED" | head -15 | sed 's/^/  /'

echo ""
echo "=== Dump complete: $OUTPUT_DIR ==="
echo ""
echo "Key files to review:"
echo "  routes_all.txt   — check for missing or wrong default route"
echo "  ip_rules.txt     — per-UID routing policy"
echo "  netd_dump.txt    — firewall chains and netd internal state"
echo "  dns_resolver.txt — Private DNS, DoH configuration"

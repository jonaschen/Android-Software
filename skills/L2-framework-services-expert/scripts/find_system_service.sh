#!/usr/bin/env bash
# find_system_service.sh — Locate a system service across the framework tree
#
# Given a service name or interface name, finds:
#   - The AIDL interface definition
#   - The service implementation class
#   - Where it is registered in SystemServer
#   - Whether it appears in the API surface
#
# Usage:
#   ./find_system_service.sh <ServiceName>
#   ./find_system_service.sh ActivityManager
#   ./find_system_service.sh IWindowManager
#
# Run from AOSP root directory.

set -euo pipefail

NAME="${1:-}"
if [ -z "$NAME" ]; then
    echo "Usage: $0 <ServiceName or IInterfaceName>"
    echo "Example: $0 ActivityManager"
    exit 1
fi

FW_BASE="frameworks/base"
FW_NATIVE="frameworks/native"

echo "=== find_system_service.sh: $NAME ==="
echo ""

# ─── 1. Find AIDL interface definition ─────────────────────────────────────
echo "[1] AIDL interface definition:"
find "$FW_BASE" "$FW_NATIVE" -name "I${NAME}.aidl" -o -name "${NAME}.aidl" 2>/dev/null \
    | while read -r f; do echo "  $f"; done \
    || echo "  (none found)"
echo ""

# ─── 2. Find Java implementation class ─────────────────────────────────────
echo "[2] Java service implementation (extends SystemService or Stub):"
grep -rl "class ${NAME}Service\|class ${NAME}" \
    "$FW_BASE/services/" --include="*.java" 2>/dev/null \
    | while read -r f; do echo "  $f"; done \
    || echo "  (none found)"
echo ""

# ─── 3. Find SystemServer registration ─────────────────────────────────────
echo "[3] SystemServer registration:"
grep -n "${NAME}" \
    "$FW_BASE/services/java/com/android/server/SystemServer.java" 2>/dev/null \
    | while read -r line; do echo "  $line"; done \
    || echo "  (none found in SystemServer.java)"
echo ""

# ─── 4. Find ServiceManager.addService calls ───────────────────────────────
echo "[4] ServiceManager.addService registrations:"
grep -rn "addService.*${NAME}\|${NAME}.*addService" \
    "$FW_BASE" "$FW_NATIVE" --include="*.java" 2>/dev/null | head -10 \
    | while read -r line; do echo "  $line"; done \
    || echo "  (none found)"
echo ""

# ─── 5. API surface presence ───────────────────────────────────────────────
echo "[5] API surface (frameworks/base/api/):"
for api_file in "$FW_BASE/api/current.txt" "$FW_BASE/api/system-current.txt"; do
    if [ -f "$api_file" ]; then
        COUNT=$(grep -c "$NAME" "$api_file" 2>/dev/null || true)
        if [ "$COUNT" -gt 0 ]; then
            echo "  $api_file: $COUNT reference(s)"
            grep "$NAME" "$api_file" | head -5 | sed 's/^/    /'
        fi
    fi
done
echo ""

# ─── 6. Watchdog monitoring ────────────────────────────────────────────────
echo "[6] Watchdog registration:"
grep -rn "Watchdog.*${NAME}\|${NAME}.*Watchdog" \
    "$FW_BASE/services/" --include="*.java" 2>/dev/null | head -5 \
    | while read -r line; do echo "  $line"; done \
    || echo "  (none found)"
echo ""

echo "=== Done ==="

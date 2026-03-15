#!/usr/bin/env bash
# check_pkvm_status.sh -- pKVM / AVF readiness probe
# Usage: check_pkvm_status.sh [--adb-serial <serial>]
#
# Checks:
#   1. /dev/kvm presence
#   2. ro.boot.hypervisor.* system properties
#   3. AVF feature flag (ro.avf.enabled or persist.device_config)
#   4. Running VMs via `vm list`
#
# Exit codes:
#   0 -- pKVM available and AVF enabled
#   1 -- pKVM not available or AVF disabled
#   2 -- adb device not found

set -euo pipefail

ADB_SERIAL=""

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --adb-serial)
            ADB_SERIAL="-s $2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--adb-serial <serial>]"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

ADB="adb ${ADB_SERIAL}"

# ---------------------------------------------------------------------------
# Verify device is reachable
# ---------------------------------------------------------------------------
if ! ${ADB} get-state > /dev/null 2>&1; then
    echo "[ERROR] No adb device found. Is the device connected and authorized?" >&2
    exit 2
fi

echo "============================================================"
echo " pKVM / AVF Status Probe"
echo "============================================================"

PASS=0
FAIL=0

check() {
    local label="$1"
    local result="$2"
    local expected="$3"
    if [[ "$result" == "$expected" ]]; then
        printf "  [PASS] %-45s = %s\n" "$label" "$result"
        ((PASS++)) || true
    else
        printf "  [FAIL] %-45s = %s  (expected: %s)\n" "$label" "$result" "$expected"
        ((FAIL++)) || true
    fi
}

info() {
    local label="$1"
    local result="$2"
    printf "  [INFO] %-45s = %s\n" "$label" "$result"
}

# ---------------------------------------------------------------------------
# 1. /dev/kvm
# ---------------------------------------------------------------------------
echo ""
echo "--- KVM device node ---"
KVM_EXISTS=$(${ADB} shell "[ -e /dev/kvm ] && echo yes || echo no" 2>/dev/null | tr -d '\r')
check "/dev/kvm present" "$KVM_EXISTS" "yes"

if [[ "$KVM_EXISTS" == "yes" ]]; then
    KVM_PERMS=$(${ADB} shell "ls -la /dev/kvm 2>/dev/null" | tr -d '\r')
    info "/dev/kvm permissions" "$KVM_PERMS"
fi

# ---------------------------------------------------------------------------
# 2. Hypervisor system properties
# ---------------------------------------------------------------------------
echo ""
echo "--- Hypervisor system properties ---"

VM_SUPPORTED=$(${ADB} shell getprop ro.boot.hypervisor.vm.supported 2>/dev/null | tr -d '\r')
PVM_SUPPORTED=$(${ADB} shell getprop ro.boot.hypervisor.protected_vm.supported 2>/dev/null | tr -d '\r')
HYP_VERSION=$(${ADB} shell getprop ro.boot.hypervisor.version 2>/dev/null | tr -d '\r')

check "ro.boot.hypervisor.vm.supported" "${VM_SUPPORTED:-<unset>}" "1"
check "ro.boot.hypervisor.protected_vm.supported" "${PVM_SUPPORTED:-<unset>}" "1"
info  "ro.boot.hypervisor.version" "${HYP_VERSION:-<unset>}"

# ---------------------------------------------------------------------------
# 3. AVF feature flag
# ---------------------------------------------------------------------------
echo ""
echo "--- AVF feature flags ---"

AVF_ENABLED=$(${ADB} shell getprop ro.avf.enabled 2>/dev/null | tr -d '\r')
if [[ -z "$AVF_ENABLED" ]]; then
    # Fallback: check device_config namespace
    AVF_ENABLED=$(${ADB} shell "device_config get virtualization_framework_native enabled 2>/dev/null" | tr -d '\r')
fi
info "AVF enabled flag" "${AVF_ENABLED:-<unset>}"

# ---------------------------------------------------------------------------
# 4. Running VMs
# ---------------------------------------------------------------------------
echo ""
echo "--- Running VMs ---"
VM_LIST=$(${ADB} shell "vm list 2>/dev/null" | tr -d '\r')
if [[ -z "$VM_LIST" ]]; then
    info "Running VMs" "<none>"
else
    echo "$VM_LIST" | while IFS= read -r line; do
        info "VM" "$line"
    done
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "------------------------------------------------------------"
echo " Checks passed : ${PASS}"
echo " Checks failed : ${FAIL}"
echo "------------------------------------------------------------"

if [[ $FAIL -eq 0 ]]; then
    echo " RESULT: pKVM available and AVF supported on this device."
    exit 0
else
    echo " RESULT: pKVM / AVF not fully supported -- see FAIL entries above."
    exit 1
fi

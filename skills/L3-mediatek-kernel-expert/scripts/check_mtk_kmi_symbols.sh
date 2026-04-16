#!/usr/bin/env bash
# check_mtk_kmi_symbols.sh — Audit a MediaTek vendor kernel module for GKI KMI symbol compliance.
#
# Usage:
#   bash check_mtk_kmi_symbols.sh <path/to/module.ko> [--abi-xml <path/to/abi_gki_aarch64.xml>]
#
# What it does:
#   1. Extracts all undefined symbols from the module (nm + grep U)
#   2. Reads the GKI ABI allowlist XML (abi_gki_aarch64.xml)
#   3. Reports which symbols are on the allowlist and which are not
#   4. Exits non-zero if any non-allowlisted symbols are found
#
# Requirements: nm (binutils), python3 (for XML parsing)
#
# Example:
#   bash check_mtk_kmi_symbols.sh out/target/product/mt6989/vendor/lib/modules/wlan_drv_gen4m.ko
#   bash check_mtk_kmi_symbols.sh wmt_chrdev_wifi.ko --abi-xml kernel/common/android/abi_gki_aarch64.xml
#
# Exit codes:
#   0 — All symbols are KMI-allowlisted (module is GKI-compliant)
#   1 — One or more symbols are NOT on the allowlist (module will fail to load on GKI)
#   2 — Usage error or missing tool

set -euo pipefail

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
MODULE=""
ABI_XML=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --abi-xml)
            ABI_XML="$2"
            shift 2
            ;;
        --help|-h)
            sed -n '2,20p' "$0" | grep '^#' | sed 's/^# \?//'
            exit 0
            ;;
        -*)
            echo "ERROR: Unknown option: $1" >&2
            exit 2
            ;;
        *)
            MODULE="$1"
            shift
            ;;
    esac
done

if [[ -z "$MODULE" ]]; then
    echo "ERROR: No module path specified." >&2
    echo "Usage: $0 <path/to/module.ko> [--abi-xml <path>]" >&2
    exit 2
fi

if [[ ! -f "$MODULE" ]]; then
    echo "ERROR: Module file not found: $MODULE" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# Locate ABI XML if not specified
# ---------------------------------------------------------------------------
if [[ -z "$ABI_XML" ]]; then
    for candidate in \
        "kernel/common/android/abi_gki_aarch64.xml" \
        "common/android/abi_gki_aarch64.xml" \
        "android/abi_gki_aarch64.xml"; do
        if [[ -f "$candidate" ]]; then
            ABI_XML="$candidate"
            break
        fi
    done
fi

# ---------------------------------------------------------------------------
# Extract undefined symbols from the module
# ---------------------------------------------------------------------------
echo "============================================================"
echo "  MediaTek GKI KMI Symbol Auditor"
echo "  Module : $MODULE"
if [[ -n "$ABI_XML" ]]; then
    echo "  ABI XML: $ABI_XML"
else
    echo "  ABI XML: not found — reporting symbols only (no compliance check)"
fi
echo "============================================================"
echo ""

if ! command -v nm &>/dev/null; then
    echo "ERROR: 'nm' (binutils) not found. Install binutils to use this tool." >&2
    exit 2
fi

UNDEFINED=$(nm --undefined-only "$MODULE" 2>/dev/null | awk '{print $NF}' | sort -u)
TOTAL=$(echo "$UNDEFINED" | wc -l | tr -d ' ')

echo "Undefined symbols in $(basename "$MODULE"): $TOTAL"
echo ""

# ---------------------------------------------------------------------------
# MediaTek-specific problematic symbol patterns
# ---------------------------------------------------------------------------
# These are MTK-internal APIs commonly found in vendor kernel modules that are
# NOT on the GKI allowlist. Flag them early even before the XML comparison.
MTK_PROBLEMATIC_PATTERNS=(
    "^mtk_devinfo_"
    "^emi_mpu_"
    "^mtk_ccci_"
    "^mtk_ion_"
    "^scp_ipi_"
    "^sspm_"
    "^mtk_mapi_"
)

# ---------------------------------------------------------------------------
# If no ABI XML, just print symbols and exit
# ---------------------------------------------------------------------------
if [[ -z "$ABI_XML" || ! -f "$ABI_XML" ]]; then
    echo "Undefined symbols:"
    echo "$UNDEFINED" | sed 's/^/  /'
    echo ""
    echo "NOTE: ABI XML not found. Cannot check KMI compliance."
    echo "      Provide --abi-xml or run from the Android source root."

    # Still flag MTK-specific red flags even without the XML
    echo ""
    echo "--- MTK-specific symbol red flags (heuristic) ---"
    MTK_FLAGGED=0
    while IFS= read -r sym; do
        [[ -z "$sym" ]] && continue
        for pat in "${MTK_PROBLEMATIC_PATTERNS[@]}"; do
            if [[ "$sym" =~ $pat ]]; then
                echo "  [WARN] $sym — matches pattern '$pat' (typically non-KMI)"
                MTK_FLAGGED=$((MTK_FLAGGED + 1))
                break
            fi
        done
    done <<< "$UNDEFINED"
    if [[ $MTK_FLAGGED -eq 0 ]]; then
        echo "  (no MTK red-flag symbols detected)"
    fi
    exit 0
fi

# ---------------------------------------------------------------------------
# Parse ABI XML to extract allowlisted symbols
# ---------------------------------------------------------------------------
ALLOWLISTED=$(python3 - "$ABI_XML" <<'PYEOF'
import sys
import xml.etree.ElementTree as ET

xml_path = sys.argv[1]
try:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    symbols = set()
    for elem in root.iter('symbol'):
        if elem.text:
            symbols.add(elem.text.strip())
    for sym in sorted(symbols):
        print(sym)
except ET.ParseError as e:
    print(f"ERROR parsing XML: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
)

if [[ -z "$ALLOWLISTED" ]]; then
    echo "WARNING: ABI XML parsed but no symbols found. Check XML format." >&2
fi

# ---------------------------------------------------------------------------
# Cross-reference: allowed vs. not allowed
# ---------------------------------------------------------------------------
ALLOWED_LIST=()
BLOCKED_LIST=()
MTK_RED_FLAG=()

while IFS= read -r sym; do
    [[ -z "$sym" ]] && continue
    if echo "$ALLOWLISTED" | grep -qx "$sym"; then
        ALLOWED_LIST+=("$sym")
    else
        BLOCKED_LIST+=("$sym")
        # Classify MTK-specific red flags for targeted remediation advice
        for pat in "${MTK_PROBLEMATIC_PATTERNS[@]}"; do
            if [[ "$sym" =~ $pat ]]; then
                MTK_RED_FLAG+=("$sym")
                break
            fi
        done
    fi
done <<< "$UNDEFINED"

echo "--- KMI Compliance Report ---"
echo ""
echo "Allowlisted (safe to use): ${#ALLOWED_LIST[@]}"
for sym in "${ALLOWED_LIST[@]}"; do
    echo "  [OK] $sym"
done

echo ""
echo "NOT on allowlist (will fail on GKI): ${#BLOCKED_LIST[@]}"
for sym in "${BLOCKED_LIST[@]}"; do
    # Mark MTK red flags with an extra tag
    marked=""
    for flagged in "${MTK_RED_FLAG[@]:-}"; do
        if [[ "$sym" == "$flagged" ]]; then
            marked=" [MTK-RED-FLAG]"
            break
        fi
    done
    echo "  [FAIL] $sym$marked"
done

echo ""
if [[ ${#BLOCKED_LIST[@]} -eq 0 ]]; then
    echo "RESULT: PASS — all $TOTAL symbols are KMI-allowlisted."
    echo "        Module is GKI-compliant."
    exit 0
else
    echo "RESULT: FAIL — ${#BLOCKED_LIST[@]} symbol(s) not on KMI allowlist."
    echo "        Module will fail to load on GKI kernels."
    echo ""
    echo "Remediation:"
    echo "  1. Replace non-allowlisted symbols with allowlisted equivalents."
    echo "  2. If no equivalent exists, add the symbol to abi_gki_aarch64.xml"
    echo "     via the upstream GKI ABI review process."
    echo "  3. For MTK-specific APIs:"
    echo "     - mtk_devinfo_* → read from device tree via of_property_read_*"
    echo "     - emi_mpu_*     → use SMC call to ATF BL31 instead of direct MPU access"
    echo "     - mtk_ion_*     → migrate to DMA-BUF heaps (dma_heap_buffer_alloc)"
    echo "     - scp_ipi_*     → use allowlisted mailbox / remoteproc framework APIs"
    if [[ ${#MTK_RED_FLAG[@]} -gt 0 ]]; then
        echo ""
        echo "  MTK-RED-FLAG symbols detected (${#MTK_RED_FLAG[@]}):"
        for sym in "${MTK_RED_FLAG[@]}"; do
            echo "    - $sym"
        done
    fi
    exit 1
fi

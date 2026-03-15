#!/usr/bin/env bash
# check_gki_symbol_list.sh — GKI KMI symbol compliance checker
#
# Checks a vendor kernel module (.ko) against the GKI ABI symbol list to
# verify that it only uses KMI-stable symbols.
#
# Also checks for common GKI module issues:
#   - MODULE_LICENSE not set or not GPL-compatible
#   - Symbols not in abi_gki_aarch64.xml
#   - Module not signed
#
# Usage:
#   ./check_gki_symbol_list.sh <module.ko> [abi_xml_path]
#   ./check_gki_symbol_list.sh vendor/lib/modules/my_driver.ko
#   ./check_gki_symbol_list.sh my.ko kernel/android/abi_gki_aarch64.xml
#
# Requires: modinfo, nm (or llvm-nm), bash
# Optional: xmllint (for XML parsing)

set -euo pipefail

MODULE="${1:-}"
ABI_XML="${2:-kernel/android/abi_gki_aarch64.xml}"

if [ -z "$MODULE" ] || [ ! -f "$MODULE" ]; then
    echo "Usage: $0 <module.ko> [abi_gki_aarch64.xml]"
    exit 1
fi

echo "=== check_gki_symbol_list.sh ==="
echo "Module:  $MODULE"
echo "ABI XML: $ABI_XML"
echo ""

ERRORS=0
WARNINGS=0

# ─── 1. Module info ──────────────────────────────────────────────────────────
echo "[1] Module information:"
if command -v modinfo &>/dev/null; then
    modinfo "$MODULE" 2>/dev/null | grep -E "filename|license|author|description|version|vermagic|sig_key" \
        | sed 's/^/  /'
else
    echo "  WARNING: modinfo not available — install kmod package"
    ((WARNINGS++)) || true
fi

# ─── 2. License check ────────────────────────────────────────────────────────
echo ""
echo "[2] License check:"
if command -v modinfo &>/dev/null; then
    LICENSE=$(modinfo "$MODULE" 2>/dev/null | grep "^license:" | awk '{print $2}' || true)
    if [ -z "$LICENSE" ]; then
        echo "  ERROR: No MODULE_LICENSE defined — GKI requires explicit license"
        ((ERRORS++)) || true
    elif echo "$LICENSE" | grep -qiE "GPL|MIT|BSD|Apache"; then
        echo "  OK: License = $LICENSE"
    else
        echo "  WARNING: License '$LICENSE' may not be GKI-compatible — verify"
        ((WARNINGS++)) || true
    fi
fi

# ─── 3. Undefined symbol extraction ──────────────────────────────────────────
echo ""
echo "[3] Checking undefined symbols (required imports):"

NM_CMD=""
if command -v llvm-nm &>/dev/null; then
    NM_CMD="llvm-nm"
elif command -v nm &>/dev/null; then
    NM_CMD="nm"
else
    echo "  WARNING: nm/llvm-nm not found — skipping symbol check"
    ((WARNINGS++)) || true
fi

if [ -n "$NM_CMD" ]; then
    UNDEF_SYMBOLS=$("$NM_CMD" --undefined-only "$MODULE" 2>/dev/null \
        | awk '{print $NF}' | grep -v "^$" | sort -u || true)

    SYMBOL_COUNT=$(echo "$UNDEF_SYMBOLS" | grep -c "." || true)
    echo "  Found $SYMBOL_COUNT undefined symbol(s) required by module."

    # ─── 4. ABI XML check ────────────────────────────────────────────────────
    echo ""
    echo "[4] KMI symbol compliance:"
    if [ -f "$ABI_XML" ]; then
        NOT_IN_KMI=()
        while IFS= read -r sym; do
            [ -z "$sym" ] && continue
            if ! grep -q "\"$sym\"" "$ABI_XML" 2>/dev/null; then
                NOT_IN_KMI+=("$sym")
            fi
        done <<< "$UNDEF_SYMBOLS"

        if [ ${#NOT_IN_KMI[@]} -eq 0 ]; then
            echo "  OK: All symbols are in the KMI list."
        else
            echo "  ERROR: ${#NOT_IN_KMI[@]} symbol(s) NOT in KMI list:"
            for sym in "${NOT_IN_KMI[@]}"; do
                echo "    - $sym"
            done
            ((ERRORS++)) || true
            echo ""
            echo "  RESOLUTION:"
            echo "    Option A: Remove usage of non-KMI symbol from driver code."
            echo "    Option B: Submit symbol for addition to GKI KMI list via upstream kernel."
            echo "    Option C: If symbol is in GKI but not in XML: file GKI bug."
        fi
    else
        echo "  WARNING: ABI XML not found at '$ABI_XML' — skipping KMI check"
        echo "  Set ABI_XML path or clone android-mainline kernel."
        ((WARNINGS++)) || true
    fi
fi

# ─── 5. Signature check ──────────────────────────────────────────────────────
echo ""
echo "[5] Module signature:"
if command -v modinfo &>/dev/null; then
    SIG=$(modinfo "$MODULE" 2>/dev/null | grep "sig_key\|signature" | head -2 || true)
    if [ -n "$SIG" ]; then
        echo "  OK: Module has signature metadata:"
        echo "$SIG" | sed 's/^/    /'
    else
        echo "  WARNING: No signature detected — module may fail to load on production device with AVB"
        ((WARNINGS++)) || true
    fi
fi

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "=== SUMMARY ==="
echo "  Errors:   $ERRORS"
echo "  Warnings: $WARNINGS"
if [ "$ERRORS" -gt 0 ]; then
    echo "  RESULT: FAIL — fix errors before loading on GKI device"
    exit 1
else
    echo "  RESULT: PASS"
    exit 0
fi

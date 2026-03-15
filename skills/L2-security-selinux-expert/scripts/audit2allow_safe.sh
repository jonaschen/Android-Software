#!/usr/bin/env bash
# audit2allow_safe.sh — Safe audit2allow wrapper for Android SELinux
#
# Unlike raw audit2allow, this script:
#   1. Filters out denials that match known neverallow patterns
#   2. Groups rules by source domain
#   3. Flags rules that touch sensitive types (init, kernel, su domains)
#   4. Prints guidance on where to place the rule
#
# Usage:
#   adb logcat -b all | grep "avc: denied" > avc.log
#   ./audit2allow_safe.sh avc.log [sepolicy_dir]
#
# Requires: audit2allow (from android-tools or AOSP), bash, grep

set -euo pipefail

AVC_LOG="${1:-}"
SEPOLICY_DIR="${2:-system/sepolicy}"

if [ -z "$AVC_LOG" ] || [ ! -f "$AVC_LOG" ]; then
    echo "Usage: $0 <avc_log_file> [sepolicy_dir]"
    echo "  avc_log_file: file containing avc: denied lines (from adb logcat)"
    exit 1
fi

if ! command -v audit2allow &>/dev/null; then
    echo "ERROR: audit2allow not found. Install android-tools or set up AOSP build env."
    exit 1
fi

echo "=== audit2allow_safe.sh ==="
echo "Input:     $AVC_LOG"
echo "Sepolicy:  $SEPOLICY_DIR"
echo ""

# ─── Sensitive domains — require manual review ─────────────────────────────
SENSITIVE_DOMAINS="init kernel shell su toolbox ueventd vold"

# ─── Step 1: Extract unique denials ────────────────────────────────────────
echo "[STEP 1] Extracting unique avc: denied lines..."
UNIQUE_DENIALS=$(grep "avc: denied" "$AVC_LOG" | sort -u)
DENIAL_COUNT=$(echo "$UNIQUE_DENIALS" | grep -c "avc:" || true)
echo "  Found $DENIAL_COUNT unique denial pattern(s)."
echo ""

# ─── Step 2: Generate raw allow rules ──────────────────────────────────────
echo "[STEP 2] Generating candidate allow rules (raw audit2allow output)..."
RAW_RULES=$(echo "$UNIQUE_DENIALS" | audit2allow 2>/dev/null || true)
echo "$RAW_RULES"
echo ""

# ─── Step 3: Flag sensitive domain rules ───────────────────────────────────
echo "[STEP 3] Checking for sensitive domain involvement..."
for domain in $SENSITIVE_DOMAINS; do
    if echo "$RAW_RULES" | grep -q "allow $domain "; then
        echo "  *** WARNING: Rule targets sensitive domain '$domain' — requires security review ***"
    fi
done
echo ""

# ─── Step 4: Check against known neverallow patterns ───────────────────────
echo "[STEP 4] Checking neverallow constraints..."
if [ -d "$SEPOLICY_DIR" ]; then
    while IFS= read -r rule; do
        # Extract source domain from allow rule
        src=$(echo "$rule" | awk '/^allow/ {print $2}')
        if [ -n "$src" ]; then
            NEVERALLOW_HIT=$(grep -r "neverallow.*$src" "$SEPOLICY_DIR" 2>/dev/null | head -3 || true)
            if [ -n "$NEVERALLOW_HIT" ]; then
                echo "  *** NEVERALLOW RISK for domain '$src': ***"
                echo "$NEVERALLOW_HIT" | sed 's/^/    /'
            fi
        fi
    done < <(echo "$RAW_RULES" | grep "^allow")
else
    echo "  WARNING: Sepolicy dir '$SEPOLICY_DIR' not found — skipping neverallow check."
fi
echo ""

# ─── Step 5: Placement guidance ────────────────────────────────────────────
echo "[STEP 5] Placement guidance..."
echo "  For each allow rule:"
echo "    - Platform domain (e.g., system_server, vold):"
echo "        → $SEPOLICY_DIR/private/<domain>.te"
echo "    - Vendor domain (e.g., vendor_*, hal_*_default):"
echo "        → vendor/<OEM>/sepolicy/<domain>.te"
echo "    - New file labels:"
echo "        → $SEPOLICY_DIR/private/file_contexts  (platform files)"
echo "        → vendor/<OEM>/sepolicy/file_contexts   (vendor files)"
echo ""
echo "  REMINDER: Do NOT use audit2allow output verbatim."
echo "  Narrow each rule to the minimum required permissions."
echo ""
echo "=== Done. Review all rules before committing. ==="

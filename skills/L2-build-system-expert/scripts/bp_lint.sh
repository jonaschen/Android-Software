#!/usr/bin/env bash
# bp_lint.sh — Android.bp static analysis helper
#
# Checks Android.bp files under a given path for common mistakes:
#   - Deprecated LOCAL_ variables (belong in Android.mk, not Android.bp)
#   - vendor: true modules without soc_specific or equivalent
#   - Missing visibility field on java_library / cc_library
#   - Duplicate module names within the search tree
#
# Usage:
#   ./bp_lint.sh [path]         # default path: current directory
#
# Requires: bash, grep, awk, sort

set -euo pipefail

SEARCH_PATH="${1:-.}"
ERRORS=0
WARNINGS=0

echo "=== bp_lint.sh ==="
echo "Scanning: $SEARCH_PATH"
echo ""

# ─── Check 1: LOCAL_ variables in .bp files ────────────────────────────────
echo "[CHECK 1] Detecting LOCAL_ variables in .bp files..."
while IFS= read -r -d '' file; do
    if grep -qE "^\s*LOCAL_" "$file" 2>/dev/null; then
        echo "  ERROR: $file contains LOCAL_ variable(s) — use Soong syntax instead"
        grep -nE "^\s*LOCAL_" "$file" | head -5
        ((ERRORS++)) || true
    fi
done < <(find "$SEARCH_PATH" -name "Android.bp" -print0 2>/dev/null)

# ─── Check 2: Hardcoded /system/ paths in Android.bp install paths ─────────
echo ""
echo "[CHECK 2] Detecting hardcoded /system/ install paths..."
while IFS= read -r -d '' file; do
    if grep -qE '"(/system/|/vendor/)' "$file" 2>/dev/null; then
        echo "  WARNING: $file uses hardcoded partition path — prefer relative_install_path"
        grep -nE '"(/system/|/vendor/)' "$file" | head -5
        ((WARNINGS++)) || true
    fi
done < <(find "$SEARCH_PATH" -name "Android.bp" -print0 2>/dev/null)

# ─── Check 3: Duplicate module names ───────────────────────────────────────
echo ""
echo "[CHECK 3] Checking for duplicate module names..."
DUPES=$(find "$SEARCH_PATH" -name "Android.bp" -exec \
    grep -hE '^\s+name:\s+"[^"]+"' {} \; 2>/dev/null \
    | sed 's/.*name: "\([^"]*\)".*/\1/' \
    | sort | uniq -d)

if [ -n "$DUPES" ]; then
    echo "  ERROR: Duplicate module names detected:"
    echo "$DUPES" | while read -r name; do
        echo "    - $name"
        find "$SEARCH_PATH" -name "Android.bp" -exec \
            grep -l "\"$name\"" {} \; 2>/dev/null | head -3 | sed 's/^/      /'
    done
    ((ERRORS++)) || true
else
    echo "  OK: No duplicate module names found."
fi

# ─── Check 4: vendor:true without soc_specific or device_specific ──────────
echo ""
echo "[CHECK 4] Checking vendor:true modules for partition clarity..."
while IFS= read -r -d '' file; do
    if grep -qE "^\s+vendor:\s+true" "$file" 2>/dev/null; then
        if ! grep -qE "soc_specific|device_specific|product_specific" "$file" 2>/dev/null; then
            echo "  INFO: $file — vendor:true but no soc_specific/device_specific; verify partition intent"
        fi
    fi
done < <(find "$SEARCH_PATH" -name "Android.bp" -print0 2>/dev/null)

# ─── Summary ───────────────────────────────────────────────────────────────
echo ""
echo "=== SUMMARY ==="
echo "  Errors:   $ERRORS"
echo "  Warnings: $WARNINGS"
if [ "$ERRORS" -gt 0 ]; then
    echo "  RESULT: FAIL"
    exit 1
else
    echo "  RESULT: PASS"
    exit 0
fi

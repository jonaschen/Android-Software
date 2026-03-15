#!/usr/bin/env bash
# atf_image_verify.sh — ARM Trusted Firmware image and secure boot chain inspector
#
# Inspects ATF-related images and the secure boot chain:
#   - Parses a FIP (Firmware Image Package) to list contained BL stages
#   - Checks AVB root of trust chain (vbmeta → boot → kernel)
#   - Reports device secure boot state via fastboot/adb
#   - Checks Trusty TEE availability on a booted device
#
# Usage:
#   ./atf_image_verify.sh [--fip <fip.bin>] [--adb] [--fastboot]
#
# Requires: adb or fastboot (for device checks), fiptool (optional, from ATF tree)

set -euo pipefail

FIP_IMAGE=""
CHECK_MODE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fip) FIP_IMAGE="$2"; shift 2 ;;
        --adb) CHECK_MODE="adb"; shift ;;
        --fastboot) CHECK_MODE="fastboot"; shift ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

echo "=== atf_image_verify.sh ==="
echo ""

# ─── 1. FIP image inspection ─────────────────────────────────────────────────
if [[ -n "$FIP_IMAGE" ]]; then
    if [[ ! -f "$FIP_IMAGE" ]]; then
        echo "ERROR: FIP image not found: $FIP_IMAGE"
        exit 1
    fi

    echo "[FIP] Inspecting: $FIP_IMAGE"

    if command -v fiptool &>/dev/null; then
        echo ""
        echo "  FIP contents:"
        fiptool info "$FIP_IMAGE" 2>&1 | sed 's/^/    /'
    else
        echo "  WARNING: fiptool not found — install from ATF tree:"
        echo "    cd atf/ && make fiptool && cp tools/fiptool/fiptool /usr/local/bin/"
        echo ""
        echo "  Attempting raw UUIDs inspection (fallback):"
        # FIP header magic: 0xAAAAAAAA
        MAGIC=$(xxd -l4 -p "$FIP_IMAGE" 2>/dev/null | tr '[:lower:]' '[:upper:]' || true)
        if [[ "$MAGIC" == "AAAAAAAA" ]]; then
            echo "  OK: FIP magic header detected (0xAAAAAAAA)"
            echo "  File size: $(du -sh "$FIP_IMAGE" | cut -f1)"
        else
            echo "  WARNING: FIP magic not found (got: 0x$MAGIC) — may not be a FIP image"
        fi
    fi
    echo ""
fi

# ─── 2. AVB verified boot chain ──────────────────────────────────────────────
if command -v avbtool &>/dev/null && [[ -n "$FIP_IMAGE" ]]; then
    echo "[AVB] Checking vbmeta (if available alongside FIP)..."
    VBMETA_DIR=$(dirname "$FIP_IMAGE")
    for f in "$VBMETA_DIR"/vbmeta*.img; do
        [[ -f "$f" ]] || continue
        echo "  $f:"
        avbtool info_image --image "$f" 2>/dev/null \
            | grep -E "Algorithm|Public key|Rollback|Descriptor" \
            | sed 's/^/    /'
    done
    echo ""
fi

# ─── 3. Device checks via ADB ────────────────────────────────────────────────
if [[ "$CHECK_MODE" == "adb" ]]; then
    if ! adb devices | grep -q "device$"; then
        echo "ERROR: No ADB device connected."
        exit 1
    fi

    echo "[DEVICE — ADB] Secure boot and TEE state:"
    echo ""

    echo "  Verified boot state:"
    for prop in \
        ro.boot.verifiedbootstate \
        ro.boot.vbmeta.digest \
        ro.boot.vbmeta.avb_version; do
        val=$(adb shell getprop "$prop" 2>/dev/null || echo "(not set)")
        printf "    %-40s = %s\n" "$prop" "$val"
    done
    echo ""

    echo "  Trusty TEE availability:"
    for dev in /dev/trusty-ipc-dev0 /dev/tee0 /dev/teepriv0; do
        exists=$(adb shell "[ -e $dev ] && echo found || echo missing" 2>/dev/null || echo "unknown")
        printf "    %-30s %s\n" "$dev" "$exists"
    done
    echo ""

    echo "  KeyMint / Keystore TEE backing:"
    adb shell dumpsys keystore2 2>/dev/null \
        | grep -iE "strongbox|software|tee|implementation" \
        | head -10 | sed 's/^/    /' \
        || echo "    (keystore2 not available or requires root)"
    echo ""

    echo "  PSCI support (power management via EL3):"
    PSCI=$(adb shell "cat /proc/device-tree/psci/compatible 2>/dev/null | tr -d '\0'" || true)
    if [[ -n "$PSCI" ]]; then
        echo "    PSCI compatible: $PSCI"
    else
        echo "    PSCI DT node not found (may be using legacy PSCI)"
    fi
    echo ""

    echo "  CPU cores (PSCI hotplug):"
    adb shell "cat /sys/devices/system/cpu/online 2>/dev/null" | xargs printf "    Online CPUs: %s\n"
fi

# ─── 4. Device checks via fastboot ───────────────────────────────────────────
if [[ "$CHECK_MODE" == "fastboot" ]]; then
    if ! fastboot devices | grep -q "fastboot"; then
        echo "ERROR: No device in fastboot mode."
        exit 1
    fi

    echo "[DEVICE — FASTBOOT] Secure boot state:"
    echo ""

    for var in secure unlocked verified-boot-state version-bootloader; do
        result=$(fastboot getvar "$var" 2>&1 | grep "^$var:" | cut -d: -f2- | xargs)
        printf "  %-30s = %s\n" "$var" "${result:-(not supported)}"
    done
    echo ""
    echo "  Secure = 'yes' means device enforces verified boot (ATF RoT active)"
    echo "  Unlocked = 'yes' means bootloader is unlocked (AVB = ORANGE state)"
fi

# ─── 5. No mode selected ─────────────────────────────────────────────────────
if [[ -z "$FIP_IMAGE" && -z "$CHECK_MODE" ]]; then
    echo "Usage examples:"
    echo "  Inspect a FIP image:            $0 --fip path/to/fip.bin"
    echo "  Check booted device (adb):      $0 --adb"
    echo "  Check bootloader mode device:   $0 --fastboot"
    echo "  Inspect FIP + check device:     $0 --fip fip.bin --adb"
fi

echo ""
echo "=== Done ==="

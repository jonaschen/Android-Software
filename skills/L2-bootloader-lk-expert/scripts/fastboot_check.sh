#!/usr/bin/env bash
# fastboot_check.sh — Bootloader and partition health diagnostic
#
# Collects bootloader state, partition layout, A/B slot status, and AVB
# verification state from a connected device via fastboot or adb.
#
# Usage:
#   ./fastboot_check.sh [--adb | --fastboot]
#   --adb       Device is booted into Android (default)
#   --fastboot  Device is in fastboot mode

set -euo pipefail

MODE="adb"
if [[ "${1:-}" == "--fastboot" ]]; then
    MODE="fastboot"
fi

echo "=== fastboot_check.sh (mode: $MODE) ==="
echo ""

# ─── ADB mode (device booted) ───────────────────────────────────────────────
if [[ "$MODE" == "adb" ]]; then
    if ! adb devices | grep -q "device$"; then
        echo "ERROR: No ADB device connected."
        exit 1
    fi

    echo "[1] Bootloader / verified boot state:"
    for prop in \
        ro.boot.verifiedbootstate \
        ro.boot.vbmeta.digest \
        ro.boot.vbmeta.hash_alg \
        ro.boot.slot_suffix \
        ro.boot.bootdevice \
        ro.bootloader; do
        val=$(adb shell getprop "$prop" 2>/dev/null || echo "(not set)")
        printf "  %-40s = %s\n" "$prop" "$val"
    done

    echo ""
    echo "[2] A/B slot status:"
    for prop in \
        ro.boot.slot_suffix \
        ro.boot.slot_count \
        ro.boot.boottime; do
        val=$(adb shell getprop "$prop" 2>/dev/null || echo "(not set)")
        printf "  %-40s = %s\n" "$prop" "$val"
    done

    echo ""
    echo "[3] Partition layout (/dev/block/by-name):"
    adb shell ls -la /dev/block/by-name/ 2>/dev/null \
        | awk '{print "  " $NF " -> " $(NF-2)}' \
        | sort || echo "  (not accessible)"

    echo ""
    echo "[4] Block device sizes (key partitions):"
    for part in boot vendor_boot init_boot vbmeta vbmeta_system super; do
        for suffix in "" "_a" "_b"; do
            dev="/dev/block/by-name/${part}${suffix}"
            size=$(adb shell "blockdev --getsize64 $dev 2>/dev/null || echo '(not found)'" 2>/dev/null || true)
            if [[ "$size" != "(not found)" && -n "$size" ]]; then
                size_mb=$(( size / 1048576 ))
                echo "  ${part}${suffix}: ${size} bytes (${size_mb} MB)"
            fi
        done
    done

    echo ""
    echo "[5] Bootloader unlock state:"
    adb shell getprop ro.secure 2>/dev/null | xargs printf "  ro.secure = %s\n"
    adb shell getprop ro.debuggable 2>/dev/null | xargs printf "  ro.debuggable = %s\n"

# ─── Fastboot mode ───────────────────────────────────────────────────────────
else
    if ! fastboot devices | grep -q "fastboot"; then
        echo "ERROR: No device in fastboot mode. Run: adb reboot bootloader"
        exit 1
    fi

    echo "[1] All fastboot variables:"
    fastboot getvar all 2>&1 | grep -v "^<" | sed 's/^/  /'

    echo ""
    echo "[2] Key variables summary:"
    for var in \
        product \
        version-bootloader \
        version-baseband \
        current-slot \
        slot-count \
        slot-successful:a \
        slot-successful:b \
        slot-unbootable:a \
        slot-unbootable:b \
        slot-retry-count:a \
        slot-retry-count:b \
        secure \
        unlocked \
        verified-boot-state \
        max-download-size; do
        result=$(fastboot getvar "$var" 2>&1 | grep "^$var:" | cut -d: -f2- | xargs)
        printf "  %-35s = %s\n" "$var" "${result:-(not supported)}"
    done

    echo ""
    echo "[3] Partition sizes:"
    fastboot getvar all 2>&1 | grep "^partition-size:" | sed 's/^/  /' | sort
fi

echo ""
echo "=== Done ==="

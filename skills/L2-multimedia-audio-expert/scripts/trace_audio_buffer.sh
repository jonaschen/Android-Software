#!/usr/bin/env bash
# trace_audio_buffer.sh — AudioFlinger buffer and routing diagnostic
#
# Captures a snapshot of AudioFlinger state including:
#   - Active tracks and their buffer health
#   - Thread periods and underrun counts
#   - AudioPolicy output device routing
#   - Recent audio errors from logcat
#
# Requires: adb connected device, bash
#
# Usage:
#   ./trace_audio_buffer.sh [output_dir]
#   ./trace_audio_buffer.sh /tmp/audio_trace/

set -euo pipefail

OUTPUT_DIR="${1:-/tmp/audio_trace_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$OUTPUT_DIR"

echo "=== trace_audio_buffer.sh ==="
echo "Output: $OUTPUT_DIR"
echo ""

if ! adb devices | grep -q "device$"; then
    echo "ERROR: No ADB device connected."
    exit 1
fi

# ─── 1. AudioFlinger full dump ──────────────────────────────────────────────
echo "[1] Dumping AudioFlinger state..."
adb shell dumpsys media.audio_flinger > "$OUTPUT_DIR/audioflinger_dump.txt" 2>&1
echo "  Saved: audioflinger_dump.txt"

# ─── 2. AudioPolicy routing dump ────────────────────────────────────────────
echo "[2] Dumping AudioPolicy routing..."
adb shell dumpsys media.audio_policy > "$OUTPUT_DIR/audiopolicy_dump.txt" 2>&1
echo "  Saved: audiopolicy_dump.txt"

# ─── 3. Extract underrun / timeout summary ──────────────────────────────────
echo ""
echo "[3] Underrun and timeout summary:"
UNDERRUNS=$(grep -i "underrun\|BUFFER TIMEOUT\|write blocked\|timeout" \
    "$OUTPUT_DIR/audioflinger_dump.txt" 2>/dev/null || true)
if [ -n "$UNDERRUNS" ]; then
    echo "$UNDERRUNS" | tee "$OUTPUT_DIR/underrun_summary.txt" | head -20 | sed 's/^/  /'
else
    echo "  No underruns or timeouts found in AudioFlinger dump."
fi

# ─── 4. Extract active track list ───────────────────────────────────────────
echo ""
echo "[4] Active audio tracks:"
grep -A3 "AudioTrack\|FastTrack\|stream type" \
    "$OUTPUT_DIR/audioflinger_dump.txt" 2>/dev/null \
    | head -40 | sed 's/^/  /' \
    || echo "  (none found)"

# ─── 5. Capture recent audio logcat ─────────────────────────────────────────
echo ""
echo "[5] Capturing 5 seconds of audio logcat..."
timeout 5 adb logcat -s \
    "AudioFlinger:V" "AudioPolicyManager:V" "AudioHardware:V" \
    "AudioTrack:V" "AudioRecord:V" \
    > "$OUTPUT_DIR/audio_logcat.txt" 2>&1 || true
echo "  Saved: audio_logcat.txt"

# ─── 6. Check SurfaceFlinger jank (if display issue suspected) ──────────────
echo ""
echo "[6] SurfaceFlinger jank indicators:"
adb shell dumpsys SurfaceFlinger 2>/dev/null \
    | grep -i "jank\|dropped\|missed\|deadline\|skip" \
    | head -20 | tee "$OUTPUT_DIR/surfaceflinger_jank.txt" | sed 's/^/  /' \
    || echo "  (none found)"

# ─── 7. Audio HAL services ──────────────────────────────────────────────────
echo ""
echo "[7] Registered audio HAL services:"
adb shell service list 2>/dev/null \
    | grep -i "audio\|sound" \
    | sed 's/^/  /' \
    | tee "$OUTPUT_DIR/audio_services.txt" \
    || echo "  (none found)"

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "=== Trace complete ==="
echo "All files saved to: $OUTPUT_DIR"
echo ""
echo "Next steps:"
echo "  1. Review audioflinger_dump.txt for thread period mismatches"
echo "  2. Check underrun_summary.txt for HAL write() blocking"
echo "  3. Correlate audio_logcat.txt timestamps with underrun events"
echo "  4. If display-related: review surfaceflinger_jank.txt for missed VSync"

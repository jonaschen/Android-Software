"""
AOSP Root Router Accuracy Test Suite
=====================================
Tests the routing logic defined in skills/L1-aosp-root-router/SKILL.md.

Each test case represents a user task description and asserts:
  - The expected AOSP path(s) to be identified
  - The expected L2 skill to be loaded

Usage:
    python3 tests/routing_accuracy/test_router.py

When a real router implementation exists, replace `mock_router()` with the
actual routing function. Until then, this file serves as the ground-truth
specification and can be used for manual spot-check evaluation.
"""

import sys
import json
from dataclasses import dataclass
from typing import List, Optional

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class RoutingTestCase:
    id: str
    description: str                  # User's task as natural language
    expected_paths: List[str]         # One or more AOSP paths that must be identified
    expected_skill: str               # L2 skill that must be loaded
    notes: Optional[str] = None       # Rationale or tricky aspects


# ---------------------------------------------------------------------------
# Ground-truth test cases (20 cases covering all L2 skills)
# ---------------------------------------------------------------------------

TEST_CASES: List[RoutingTestCase] = [
    # --- Build System (2 cases) ---
    RoutingTestCase(
        id="TC-001",
        description="The build fails with 'module \"libfoo\" variant \"android_arm64_armv8-a_shared\": depends on disabled module'. How do I fix Android.bp?",
        expected_paths=["build/", "Android.bp"],
        expected_skill="L2-build-system-expert",
        notes="Clear Soong module dependency issue.",
    ),
    RoutingTestCase(
        id="TC-002",
        description="I need to add a new prebuilt .so to the system image using an Android.bp cc_prebuilt_library_shared module.",
        expected_paths=["Android.bp", "prebuilts/"],
        expected_skill="L2-build-system-expert",
    ),

    # --- Security / SELinux (2 cases) ---
    RoutingTestCase(
        id="TC-003",
        description="Logcat shows: avc: denied { read } for pid=1234 comm=\"my_daemon\" name=\"config\" dev=\"tmpfs\" scontext=u:r:my_daemon:s0 tcontext=u:object_r:config_prop:s0",
        expected_paths=["system/sepolicy/"],
        expected_skill="L2-security-selinux-expert",
        notes="Classic avc:denied — must never be routed elsewhere.",
    ),
    RoutingTestCase(
        id="TC-004",
        description="I'm adding a new vendor daemon that needs to communicate with hwservicemanager. What SELinux .te rules do I need?",
        expected_paths=["system/sepolicy/", "vendor/*/sepolicy/"],
        expected_skill="L2-security-selinux-expert",
    ),

    # --- HAL / Vendor Interface (2 cases) ---
    RoutingTestCase(
        id="TC-005",
        description="We need to bump our AIDL HAL interface from version 2 to version 3 for the sensor HAL at hardware/interfaces/sensors/.",
        expected_paths=["hardware/interfaces/sensors/"],
        expected_skill="L2-hal-vendor-interface-expert",
    ),
    RoutingTestCase(
        id="TC-006",
        description="How do I check if our vendor library is on the VNDK list and confirm Treble compliance?",
        expected_paths=["system/vndk/", "vendor/"],
        expected_skill="L2-hal-vendor-interface-expert",
        notes="VNDK boundary check is owned by HAL expert, not build expert.",
    ),

    # --- Framework Services (2 cases) ---
    RoutingTestCase(
        id="TC-007",
        description="ActivityManagerService is throwing a Watchdog ANR for my new system service. Where do I add the Watchdog handler?",
        expected_paths=["frameworks/base/services/core/java/com/android/server/"],
        expected_skill="L2-framework-services-expert",
    ),
    RoutingTestCase(
        id="TC-008",
        description="I need to add a new @SystemApi to expose a platform feature to privileged apps. Which files do I need to modify in frameworks/base?",
        expected_paths=["frameworks/base/api/", "frameworks/base/core/java/android/"],
        expected_skill="L2-framework-services-expert",
    ),

    # --- Init / Boot Sequence (2 cases) ---
    RoutingTestCase(
        id="TC-009",
        description="My vendor daemon defined in vendor/my_oem/init/my_daemon.rc fails to start because it can't find its socket. How do I debug init.rc socket definitions?",
        expected_paths=["system/core/init/", "*.rc"],
        expected_skill="L2-init-boot-sequence-expert",
    ),
    RoutingTestCase(
        id="TC-010",
        description="I need to set a system property during early init before post-fs-data. Which init stage and which .rc trigger should I use?",
        expected_paths=["system/core/init/", "*.rc"],
        expected_skill="L2-init-boot-sequence-expert",
    ),

    # --- Version Migration (2 cases) ---
    RoutingTestCase(
        id="TC-011",
        description="We are migrating from Android 14 to Android 15. What are the breaking changes in the boot image format I need to be aware of?",
        expected_paths=["bootable/", "build/"],
        expected_skill="L2-version-migration-expert",
        notes="Cross-cutting migration task — migration expert owns the impact analysis.",
    ),
    RoutingTestCase(
        id="TC-012",
        description="Our device doesn't pass CTS on the 16KB page alignment tests after upgrading to Android 15. What needs to change?",
        expected_paths=["bionic/", "build/soong/"],
        expected_skill="L2-version-migration-expert",
        notes="16KB page migration is explicitly owned by version-migration-expert.",
    ),

    # --- Multimedia / Audio (2 cases) ---
    RoutingTestCase(
        id="TC-013",
        description="AudioFlinger is logging 'BUFFER TIMEOUT' for our DSP audio HAL. I need to trace the audio buffer path from AudioFlinger to the HAL.",
        expected_paths=["frameworks/av/services/audioflinger/", "hardware/interfaces/audio/"],
        expected_skill="L2-multimedia-audio-expert",
    ),
    RoutingTestCase(
        id="TC-014",
        description="SurfaceFlinger is dropping frames on our display. I need to understand how HWC composition layers are scheduled.",
        expected_paths=["frameworks/native/services/surfaceflinger/", "hardware/interfaces/graphics/"],
        expected_skill="L2-multimedia-audio-expert",
    ),

    # --- Connectivity / Network (2 cases) ---
    RoutingTestCase(
        id="TC-015",
        description="netd is rejecting network routes for our custom VPN interface. Where is the routing table management code in netd?",
        expected_paths=["system/netd/"],
        expected_skill="L2-connectivity-network-expert",
    ),
    RoutingTestCase(
        id="TC-016",
        description="We're implementing a custom Wi-Fi HAL. Where are the AIDL interface definitions for IWifi and IWifiChip?",
        expected_paths=["hardware/interfaces/wifi/", "packages/modules/Wifi/"],
        expected_skill="L2-connectivity-network-expert",
    ),

    # --- Kernel / GKI (2 cases) ---
    RoutingTestCase(
        id="TC-017",
        description="I need to add a new GKI loadable kernel module for our sensor driver. What are the Kconfig and module signing requirements?",
        expected_paths=["kernel/", "drivers/"],
        expected_skill="L2-kernel-gki-expert",
    ),
    RoutingTestCase(
        id="TC-018",
        description="Our kernel driver is exporting a symbol that is not on the GKI ABI list. How do I add it to the symbol allowlist?",
        expected_paths=["kernel/", "kernel/configs/"],
        expected_skill="L2-kernel-gki-expert",
    ),

    # --- Cross-domain / Router guardrail cases (2 cases) ---
    RoutingTestCase(
        id="TC-019",
        description="There's an avc: denied for my new Java system service trying to write to /data/vendor/mydir. How do I fix this?",
        expected_paths=["system/sepolicy/", "vendor/*/sepolicy/"],
        expected_skill="L2-security-selinux-expert",
        notes="Even though it involves a Java service, the avc:denied ALWAYS routes to security first. "
              "L2-security-selinux-expert will hand off to L2-framework-services-expert if the service "
              "code itself needs changes.",
    ),
    RoutingTestCase(
        id="TC-020",
        description="I want to know where the Binder IPC code lives. Is it in system/core/ or somewhere else?",
        expected_paths=["frameworks/native/libs/binder/"],
        expected_skill="L2-hal-vendor-interface-expert",
        notes="Common confusion: Binder is in frameworks/native/libs/binder/, NOT system/core/. "
              "Routing to system/core/ for Binder is a forbidden action per L1 SKILL.md.",
    ),

    # --- little-kernel Bootloader (1 case) ---
    RoutingTestCase(
        id="TC-021",
        description="Our device is stuck in fastboot and the LK (little-kernel) bootloader is not reading the partition table correctly. Where is the partition parsing code in the LK source?",
        expected_paths=["bootloader/lk/"],
        expected_skill="L2-bootloader-lk-expert",
        notes="LK runs before the kernel; partition table parsing is in the LK bootloader, "
              "NOT in system/core/ or bootable/recovery/.",
    ),

    # --- ARM Trusted Firmware / ATF (1 case) ---
    RoutingTestCase(
        id="TC-022",
        description="I need to add a new SMC (Secure Monitor Call) handler in the ARM Trusted Firmware BL31 to expose a platform service to the non-secure world. Where do I make this change?",
        expected_paths=["atf/", "arm-trusted-firmware/"],
        expected_skill="L2-trusted-firmware-atf-expert",
        notes="SMC handlers are implemented in ATF BL31 (EL3 Secure Monitor). "
              "This is NOT a kernel or init task — route to L2-trusted-firmware-atf-expert.",
    ),
]


# ---------------------------------------------------------------------------
# Stub router (replace with real implementation when available)
# ---------------------------------------------------------------------------

def mock_router(task_description: str) -> dict:
    """
    Placeholder router. Returns None to indicate 'not yet implemented'.
    Replace this function body with a call to the actual routing logic.
    """
    return {"paths": None, "skill": None}


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_tests(use_mock: bool = True) -> None:
    passed = 0
    failed = 0
    skipped = 0
    results = []

    for tc in TEST_CASES:
        if use_mock:
            # In stub mode: print the expected answer and mark as SKIPPED
            result = {
                "id": tc.id,
                "status": "SKIPPED (router not implemented)",
                "description": tc.description,
                "expected_paths": tc.expected_paths,
                "expected_skill": tc.expected_skill,
                "notes": tc.notes,
            }
            skipped += 1
        else:
            routing = mock_router(tc.description)
            skill_match = routing["skill"] == tc.expected_skill
            paths_match = all(p in (routing["paths"] or []) for p in tc.expected_paths)
            status = "PASS" if (skill_match and paths_match) else "FAIL"
            if status == "PASS":
                passed += 1
            else:
                failed += 1
            result = {
                "id": tc.id,
                "status": status,
                "description": tc.description,
                "expected_skill": tc.expected_skill,
                "got_skill": routing["skill"],
                "expected_paths": tc.expected_paths,
                "got_paths": routing["paths"],
            }
        results.append(result)

    # Print summary
    print("\n" + "=" * 70)
    print("AOSP Root Router — Routing Accuracy Test Suite")
    print("=" * 70)
    for r in results:
        status_str = r["status"]
        print(f"  [{status_str:^8}] {r['id']}: {r['description'][:60]}...")
    print("-" * 70)
    total = len(TEST_CASES)
    print(f"Total: {total}  |  Passed: {passed}  |  Failed: {failed}  |  Skipped: {skipped}")
    if not use_mock and total > 0:
        accuracy = passed / total * 100
        print(f"Routing Accuracy: {accuracy:.1f}%  (target: ≥95%)")
    print("=" * 70 + "\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    # Set use_mock=False when a real router implementation is wired in.
    run_tests(use_mock=True)

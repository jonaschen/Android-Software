"""
AOSP Root Router Accuracy Test Suite
=====================================
Tests the routing logic defined in skills/L1-aosp-root-router/SKILL.md.

Each test case represents a user task description and asserts:
  - The expected AOSP path(s) to be identified
  - The expected L2 skill to be loaded

Usage:
    python3 tests/routing_accuracy/test_router.py

Test suite: 100 cases (TC-001 – TC-100)
  - TC-001 – TC-026: Original single-skill cases (2 per skill, all 12 L2 skills)
  - TC-027 – TC-070: Additional single-skill cases (3-4 per skill)
  - TC-071 – TC-100: Multi-skill cross-domain scenarios (30 cases, ≥3-skill coverage)

Phase 3 target: ≥95% routing accuracy on the full 100-case suite.

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

    # --- little-kernel Bootloader (2 cases) ---
    RoutingTestCase(
        id="TC-021",
        description="Our device is stuck in fastboot and the LK bootloader is not reading the GPT partition table correctly. Where is the partition parsing code in the LK source?",
        expected_paths=["bootloader/lk/"],
        expected_skill="L2-bootloader-lk-expert",
        notes="LK runs before the kernel; partition table parsing is in bootloader/lk/app/aboot/, "
              "NOT in system/core/ or bootable/recovery/. "
              "Note: bootloader/lk/ is vendor-supplied, not in vanilla AOSP.",
    ),
    RoutingTestCase(
        id="TC-022",
        description="I want to add a custom 'fastboot oem unlock-debug' command to the ABL bootloader. Which source file handles fastboot OEM commands in little-kernel?",
        expected_paths=["bootloader/lk/"],
        expected_skill="L2-bootloader-lk-expert",
        notes="fastboot OEM commands are registered in bootloader/lk/app/aboot/aboot.c. "
              "This is not an init, build, or kernel task.",
    ),

    # --- ARM Trusted Firmware / ATF (2 cases) ---
    RoutingTestCase(
        id="TC-023",
        description="I need to add a new SMC (Secure Monitor Call) handler in BL31 to expose a platform power-management service to the Linux kernel. Where do I make this change in the ATF source?",
        expected_paths=["atf/"],
        expected_skill="L2-trusted-firmware-atf-expert",
        notes="SMC handlers are implemented in ATF BL31 (EL3 Secure Monitor), "
              "typically in atf/plat/<vendor>/sip_svc.c. "
              "This is NOT a kernel, init, or HAL task. "
              "Note: atf/ is vendor-supplied, not in vanilla AOSP.",
    ),
    RoutingTestCase(
        id="TC-024",
        description="The Trusty KeyMint trusted application is failing to load on our device. The error appears during ATF BL32 initialization. Where do I debug this in the ATF/Trusty source?",
        expected_paths=["atf/", "trusty/"],
        expected_skill="L2-trusted-firmware-atf-expert",
        notes="BL32 is the Trusty TEE OS dispatched by ATF BL31. "
              "BL32 init failures route to L2-trusted-firmware-atf-expert, not L2-kernel-gki-expert. "
              "The non-secure side (tipc driver) would route to L2-kernel-gki-expert, "
              "but the BL32 initialization failure is squarely in ATF/Trusty territory.",
    ),

    # --- pKVM / Android Virtualization Framework (2 cases) ---
    RoutingTestCase(
        id="TC-025",
        description="I'm getting 'ro.boot.hypervisor.protected_vm.supported=0' on a device that should support pKVM. How do I enable protected VMs and verify that /dev/kvm is configured correctly for pKVM stage-2 isolation?",
        expected_paths=["packages/modules/Virtualization/", "kernel/"],
        expected_skill="L2-virtualization-pkvm-expert",
        notes="pKVM enablement spans the kernel (CONFIG_KVM, EL2 hyp init in arch/arm64/kvm/hyp/) "
              "and the AVF mainline module (VirtualizationService checks hypervisor props). "
              "This is NOT a kernel-only task (L2-kernel-gki-expert) nor a framework task "
              "(L2-framework-services-expert); pKVM-specific routing applies.",
    ),
    RoutingTestCase(
        id="TC-026",
        description="My Microdroid VM payload cannot connect to the host app via vsock. The host connects to port 5678 but the guest microdroid_manager never receives the connection. How do I debug vsock connectivity between host and guest?",
        expected_paths=["packages/modules/Virtualization/microdroid/", "external/crosvm/"],
        expected_skill="L2-virtualization-pkvm-expert",
        notes="vsock (AF_VSOCK) host↔guest IPC is implemented by the crosvm virtio-vsock backend "
              "(external/crosvm/devices/src/virtio/vsock/) and consumed by microdroid_manager. "
              "This is not a connectivity/netd task (L2-connectivity-network-expert) — vsock "
              "bypasses the network stack entirely. SELinux vsock denials would additionally "
              "involve L2-security-selinux-expert.",
    ),

    # =========================================================================
    # TC-027 – TC-070: Additional single-skill cases (44 cases, ~3-4 per skill)
    # =========================================================================

    # --- Build System (TC-027 – TC-030) ---
    RoutingTestCase(
        id="TC-027",
        description="I need to add a prebuilt .so from our SoC vendor into the system image. How do I write the cc_prebuilt_library_shared rule in Android.bp and set vendor_available correctly?",
        expected_paths=["build/soong/", "Android.bp"],
        expected_skill="L2-build-system-expert",
        notes="Prebuilt library packaging is a Soong/Android.bp task. "
              "The vendor_available flag has VNDK implications but the primary skill is build.",
    ),
    RoutingTestCase(
        id="TC-028",
        description="The `m` build command fails with 'out/soong/.bootstrap/build.ninja: error: unknown target'. How do I diagnose and fix a Soong bootstrap failure?",
        expected_paths=["build/soong/"],
        expected_skill="L2-build-system-expert",
        notes="Soong bootstrap failures are build system issues. "
              "Caused by Soong binary incompatibility or corrupted .bootstrap directory.",
    ),
    RoutingTestCase(
        id="TC-029",
        description="I want to create a new Soong module type in Go for packaging our custom binary. How do I register a new module factory in build/soong/?",
        expected_paths=["build/soong/"],
        expected_skill="L2-build-system-expert",
        notes="Custom Soong module type registration requires Go code in build/soong/. "
              "This is deep build system work, not a framework or HAL task.",
    ),
    RoutingTestCase(
        id="TC-030",
        description="Our Android.mk file uses LOCAL_CFLAGS += -DFOO but Soong Android.bp doesn't recognize LOCAL_ variables. How do I migrate this makefile flag to Android.bp?",
        expected_paths=["Android.bp", "build/make/"],
        expected_skill="L2-build-system-expert",
        notes="Android.mk to Android.bp migration is a build system task. "
              "LOCAL_CFLAGS maps to cflags in Android.bp cc_* rules.",
    ),

    # --- Security / SELinux (TC-031 – TC-034) ---
    RoutingTestCase(
        id="TC-031",
        description="I need to allow my new daemon to write to /data/vendor/foo/. What file_contexts entry and .te allow rule do I need?",
        expected_paths=["system/sepolicy/"],
        expected_skill="L2-security-selinux-expert",
        notes="File context labeling and allow rules for a vendor data directory "
              "are straightforward SELinux policy tasks.",
    ),
    RoutingTestCase(
        id="TC-032",
        description="The audit2allow output suggests adding 'allow foo_t shell_exec:file execute'. Should I add this rule? What are the security implications?",
        expected_paths=["system/sepolicy/"],
        expected_skill="L2-security-selinux-expert",
        notes="Evaluating audit2allow suggestions requires SELinux expertise. "
              "shell_exec execute is a red flag — may indicate a policy design problem.",
    ),
    RoutingTestCase(
        id="TC-033",
        description="I added a new system property 'ro.vendor.feature.enabled' but processes get avc:denied when reading it. How do I add a property_contexts entry?",
        expected_paths=["system/sepolicy/private/"],
        expected_skill="L2-security-selinux-expert",
        notes="New system properties need property_contexts entries (HS-021). "
              "This is a pure SELinux policy task.",
    ),
    RoutingTestCase(
        id="TC-034",
        description="I need to audit all neverallow rules that would affect my new HAL domain before submitting. How do I check for neverallow violations before building?",
        expected_paths=["system/sepolicy/"],
        expected_skill="L2-security-selinux-expert",
        notes="neverallow pre-validation is a SELinux task. "
              "Use `m sepolicy` or `m checkpolicy` to validate before full build.",
    ),

    # --- HAL / Vendor Interface (TC-035 – TC-038) ---
    RoutingTestCase(
        id="TC-035",
        description="I need to add a new method to an existing frozen AIDL HAL interface android.hardware.sensors@3.0. What is the correct procedure for bumping the version?",
        expected_paths=["hardware/interfaces/"],
        expected_skill="L2-hal-vendor-interface-expert",
        notes="Adding methods to a frozen interface requires creating version 3.1 or 4.0 "
              "with a new api/ freeze. Cannot modify a frozen interface in place.",
    ),
    RoutingTestCase(
        id="TC-036",
        description="What is the difference between cc_binary and cc_binary vendor:true when implementing a HAL server? How does it affect the install partition?",
        expected_paths=["hardware/interfaces/", "vendor/"],
        expected_skill="L2-hal-vendor-interface-expert",
        notes="HAL server partition placement is a HAL/Treble question with build implications. "
              "Primary skill is HAL; secondary is build.",
    ),
    RoutingTestCase(
        id="TC-037",
        description="How do I implement the IHealth AIDL HAL? Where do I find the interface definition and what methods are mandatory vs optional?",
        expected_paths=["hardware/interfaces/health/"],
        expected_skill="L2-hal-vendor-interface-expert",
        notes="IHealth is an AIDL HAL defined in hardware/interfaces/health/. "
              "This is a HAL implementation task.",
    ),
    RoutingTestCase(
        id="TC-038",
        description="Our HIDL HAL service is failing hwservicemanager registration with 'Transport not found'. How do I debug the manifest and compatibility matrix?",
        expected_paths=["hardware/interfaces/", "vendor/"],
        expected_skill="L2-hal-vendor-interface-expert",
        notes="hwservicemanager registration failures involve the vintf manifest "
              "and compatibility matrix in the HAL/Treble domain.",
    ),

    # --- Framework Services (TC-039 – TC-042) ---
    RoutingTestCase(
        id="TC-039",
        description="ActivityManagerService is killing my background service too aggressively. How do I understand the process importance scoring and adj levels?",
        expected_paths=["frameworks/base/services/core/java/com/android/server/am/"],
        expected_skill="L2-framework-services-expert",
        notes="AMS process importance (oom_adj) scoring is deep framework territory.",
    ),
    RoutingTestCase(
        id="TC-040",
        description="I need to add a new @SystemApi to expose a platform feature to privileged apps. What is the process for adding the API, updating current.txt, and passing API review?",
        expected_paths=["frameworks/base/api/", "frameworks/base/core/java/android/"],
        expected_skill="L2-framework-services-expert",
        notes="@SystemApi addition process is a framework task. "
              "Requires update-api, CTS test, and API council review.",
    ),
    RoutingTestCase(
        id="TC-041",
        description="PackageManagerService is throwing a TransactionTooLargeException when returning a large list of packages. How do I fix this?",
        expected_paths=["frameworks/base/services/core/java/com/android/server/pm/"],
        expected_skill="L2-framework-services-expert",
        notes="TransactionTooLargeException is a Binder IPC/framework issue in PMS. "
              "Solution involves batching or parceling changes.",
    ),
    RoutingTestCase(
        id="TC-042",
        description="How does SurfaceFlinger decide the display refresh rate and how do I request a specific refresh rate from my app?",
        expected_paths=["frameworks/native/services/surfaceflinger/"],
        expected_skill="L2-framework-services-expert",
        notes="SurfaceFlinger refresh rate policy is in frameworks/native. "
              "App-side rate requests go through DisplayManager → SurfaceFlinger.",
    ),

    # --- Init / Boot Sequence (TC-043 – TC-046) ---
    RoutingTestCase(
        id="TC-043",
        description="My .rc file triggers a service on 'on property:sys.boot_completed=1' but the service sometimes starts before the property is set. What is the correct trigger?",
        expected_paths=["system/core/init/"],
        expected_skill="L2-init-boot-sequence-expert",
        notes="Property trigger ordering in init.rc is an init sequence task. "
              "boot_completed is set by ActivityManagerService late in boot.",
    ),
    RoutingTestCase(
        id="TC-044",
        description="I need to mount an additional partition in early init before /data is available. How do I use 'mount' in an .rc file safely?",
        expected_paths=["system/core/init/"],
        expected_skill="L2-init-boot-sequence-expert",
        notes="Early init mount operations are handled by init before post-fs. "
              "Requires understanding of init boot phases.",
    ),
    RoutingTestCase(
        id="TC-045",
        description="The 'setprop' command in my .rc file fails with 'permission denied'. The property is set in property_contexts. What am I missing?",
        expected_paths=["system/core/init/", "system/sepolicy/"],
        expected_skill="L2-init-boot-sequence-expert",
        notes="init setprop failures involve both .rc syntax and SELinux property contexts. "
              "Primary routing is init; secondary is SELinux if the .rc is correct.",
    ),
    RoutingTestCase(
        id="TC-046",
        description="How does ueventd create /dev/ device nodes at boot? Where do I configure permissions for a new device node?",
        expected_paths=["system/core/init/", "system/core/"],
        expected_skill="L2-init-boot-sequence-expert",
        notes="ueventd device node creation is configured in ueventd.rc files. "
              "This is an init/boot sequence task.",
    ),

    # --- Version Migration (TC-047 – TC-050) ---
    RoutingTestCase(
        id="TC-047",
        description="We are upgrading from Android 14 to Android 15. What SELinux policy changes are mandatory and how do I identify which neverallow rules changed?",
        expected_paths=["system/sepolicy/"],
        expected_skill="L2-version-migration-expert",
        notes="Identifying mandatory SELinux changes in a version upgrade is a migration task. "
              "The migration expert compares policy across versions; SELinux expert implements fixes.",
    ),
    RoutingTestCase(
        id="TC-048",
        description="After upgrading to Android 15, our vendor module fails to load because a kernel symbol was removed from the GKI symbol list. How do I identify which symbols changed?",
        expected_paths=["kernel/"],
        expected_skill="L2-version-migration-expert",
        notes="GKI symbol list changes across Android versions are migration-scope. "
              "The migration expert identifies the delta; kernel expert fixes the driver.",
    ),
    RoutingTestCase(
        id="TC-049",
        description="How do I generate a diff of the public API surface between Android 14 and Android 15 to assess the impact on our OEM apps?",
        expected_paths=["frameworks/base/api/"],
        expected_skill="L2-version-migration-expert",
        notes="API surface diff generation is exactly what L2-version-migration-expert does. "
              "Use check_api_compatibility.py with the before/after api text files.",
    ),
    RoutingTestCase(
        id="TC-050",
        description="What does the 16KB page size migration require for our prebuilt vendor .so libraries? We cannot recompile them.",
        expected_paths=["bionic/", "build/soong/"],
        expected_skill="L2-version-migration-expert",
        notes="Prebuilt alignment for 16KB pages is a migration impact assessment task (HS-006). "
              "Prebuilts that cannot be recompiled require linker workarounds or replacement.",
    ),

    # --- Multimedia / Audio (TC-051 – TC-054) ---
    RoutingTestCase(
        id="TC-051",
        description="AudioFlinger is reporting 'underrun' on our device. How do I trace the audio buffer pipeline to find where frames are being dropped?",
        expected_paths=["frameworks/av/services/audioflinger/"],
        expected_skill="L2-multimedia-audio-expert",
        notes="Audio underrun diagnosis requires tracing AudioFlinger's buffer management. "
              "Use trace_audio_buffer.sh from L2-multimedia-audio-expert/scripts/.",
    ),
    RoutingTestCase(
        id="TC-052",
        description="How do I add support for a new audio format (e.g., MQA) to the audio HAL and AudioFlinger?",
        expected_paths=["frameworks/av/services/audioflinger/", "hardware/interfaces/audio/"],
        expected_skill="L2-multimedia-audio-expert",
        notes="New audio format support spans AudioFlinger (framework) and the audio HAL. "
              "Primary is multimedia expert; HAL expert handles the AIDL interface update.",
    ),
    RoutingTestCase(
        id="TC-053",
        description="CameraService is returning 'camera in use' even though no other app has the camera open. How do I debug camera session state in CameraService?",
        expected_paths=["frameworks/av/services/camera/"],
        expected_skill="L2-multimedia-audio-expert",
        notes="CameraService session management is in frameworks/av, owned by multimedia expert.",
    ),
    RoutingTestCase(
        id="TC-054",
        description="I need to implement a custom MediaCodec codec plugin. Where does codec registration happen and how does it interact with the media pipeline?",
        expected_paths=["frameworks/av/media/", "frameworks/av/services/mediacodec/"],
        expected_skill="L2-multimedia-audio-expert",
        notes="MediaCodec plugin registration is in frameworks/av/media/ and mediacodec service.",
    ),

    # --- Connectivity / Network (TC-055 – TC-058) ---
    RoutingTestCase(
        id="TC-055",
        description="How do I add a custom iptables rule that persists across network resets in Android? Where does netd manage firewall rules?",
        expected_paths=["system/netd/"],
        expected_skill="L2-connectivity-network-expert",
        notes="Persistent iptables/nftables rules are managed by netd. "
              "Custom rules require modifying netd's NatController or FirewallController.",
    ),
    RoutingTestCase(
        id="TC-056",
        description="Our app loses Wi-Fi connectivity when the screen turns off. How does WifiStateMachine handle power-save mode and how do I prevent disconnects?",
        expected_paths=["packages/modules/Wifi/"],
        expected_skill="L2-connectivity-network-expert",
        notes="WifiStateMachine power-save behavior is in packages/modules/Wifi/. "
              "This is a connectivity expert task.",
    ),
    RoutingTestCase(
        id="TC-057",
        description="I need to implement a custom VPN service in Android. Which framework APIs are involved and how does VpnService interact with netd?",
        expected_paths=["packages/modules/Connectivity/", "system/netd/"],
        expected_skill="L2-connectivity-network-expert",
        notes="VpnService implementation spans the connectivity module and netd for TUN interface management.",
    ),
    RoutingTestCase(
        id="TC-058",
        description="BluetoothGattServer callbacks are not firing after a connection is established. How do I debug GATT server state in the Fluoride/BlueDroid stack?",
        expected_paths=["packages/apps/Bluetooth/", "system/bt/"],
        expected_skill="L2-connectivity-network-expert",
        notes="GATT server debugging in Fluoride is a connectivity/Bluetooth task.",
    ),

    # --- Kernel / GKI (TC-059 – TC-062) ---
    RoutingTestCase(
        id="TC-059",
        description="How do I add a new sysfs attribute to an existing kernel driver while maintaining GKI compliance?",
        expected_paths=["kernel/", "drivers/"],
        expected_skill="L2-kernel-gki-expert",
        notes="Adding sysfs attributes to GKI-compliant drivers requires "
              "checking the GKI ABI and using only exported symbols.",
    ),
    RoutingTestCase(
        id="TC-060",
        description="The kernel crashes with 'BUG: scheduling while atomic' in our vendor module. How do I diagnose and fix this?",
        expected_paths=["kernel/", "drivers/"],
        expected_skill="L2-kernel-gki-expert",
        notes="'scheduling while atomic' is a kernel locking bug in a vendor driver. "
              "Requires understanding of spinlock vs mutex contexts.",
    ),
    RoutingTestCase(
        id="TC-061",
        description="I need to enable CONFIG_USB_GADGET in the GKI kernel configuration. How do I add a kernel config fragment for a GKI device?",
        expected_paths=["kernel/configs/"],
        expected_skill="L2-kernel-gki-expert",
        notes="GKI kernel config fragments are in kernel/configs/. "
              "Cannot modify the GKI defconfig directly; use a vendor fragment.",
    ),
    RoutingTestCase(
        id="TC-062",
        description="Our kernel module exports a symbol using EXPORT_SYMBOL_GPL but the GKI symbol list does not include it. How do I get it added?",
        expected_paths=["kernel/"],
        expected_skill="L2-kernel-gki-expert",
        notes="GKI symbol list additions require kernel team review. "
              "Use check_gki_symbol_list.sh to verify the current list (HS-013).",
    ),

    # --- Bootloader / LK (TC-063 – TC-066) ---
    RoutingTestCase(
        id="TC-063",
        description="Fastboot is not recognizing our custom partition when we run 'fastboot flash custom_part'. How does LK register custom partition names?",
        expected_paths=["bootloader/lk/"],
        expected_skill="L2-bootloader-lk-expert",
        notes="Custom partition registration in fastboot is in bootloader/lk/app/aboot/. "
              "Vendor-supplied path — not in vanilla AOSP.",
    ),
    RoutingTestCase(
        id="TC-064",
        description="A/B slot switching is failing silently after an OTA update. How does ABL mark the new slot bootable and where is this logic in LK?",
        expected_paths=["bootloader/lk/"],
        expected_skill="L2-bootloader-lk-expert",
        notes="A/B slot marking logic is in the ABL bootloader, not in init or recovery. "
              "Route to L2-bootloader-lk-expert.",
    ),
    RoutingTestCase(
        id="TC-065",
        description="AVB verification is failing with 'vbmeta: ERROR: invalid rollback index'. How does LK check the rollback index and where is it stored?",
        expected_paths=["bootloader/lk/"],
        expected_skill="L2-bootloader-lk-expert",
        notes="AVB rollback index verification is performed by ABL/LK in the bootloader. "
              "Rollback indices are stored in RPMB or fuse bits.",
    ),
    RoutingTestCase(
        id="TC-066",
        description="How do I add a new fastboot variable (e.g., 'fastboot getvar my-oem-version') to our LK bootloader?",
        expected_paths=["bootloader/lk/"],
        expected_skill="L2-bootloader-lk-expert",
        notes="Custom fastboot variables are registered in bootloader/lk/app/aboot/aboot.c "
              "via fastboot_register_var().",
    ),

    # --- ATF / Trusted Firmware (TC-067 – TC-070) ---
    RoutingTestCase(
        id="TC-067",
        description="How do I implement a new PSCI CPU_SUSPEND implementation in ATF BL31 for a custom power domain?",
        expected_paths=["atf/"],
        expected_skill="L2-trusted-firmware-atf-expert",
        notes="PSCI CPU_SUSPEND implementation is in ATF BL31 power management. "
              "Vendor-supplied path — not in vanilla AOSP.",
    ),
    RoutingTestCase(
        id="TC-068",
        description="The Trusty TA (trusted application) crashes during initialization. How do I get a crash dump from the TEE and where is the Trusty crash handler?",
        expected_paths=["trusty/"],
        expected_skill="L2-trusted-firmware-atf-expert",
        notes="Trusty TA crash debugging requires the Trusty TEE framework. "
              "Route to ATF expert who covers Trusty as BL32.",
    ),
    RoutingTestCase(
        id="TC-069",
        description="I need to add a new platform-specific SiP (Silicon Provider) SMC service in BL31. Where do I implement the handler?",
        expected_paths=["atf/"],
        expected_skill="L2-trusted-firmware-atf-expert",
        notes="SiP SMC service registration is in ATF BL31 at atf/plat/<vendor>/sip_svc.c. "
              "Vendor-supplied path.",
    ),
    RoutingTestCase(
        id="TC-070",
        description="How does ATF BL2 measure and verify BL31 before handoff? Where is the chain of trust implemented?",
        expected_paths=["atf/"],
        expected_skill="L2-trusted-firmware-atf-expert",
        notes="ATF chain of trust (CoT) is implemented in BL2's trusted board boot (TBB) module. "
              "This is ATF-specific — not a bootloader or kernel task.",
    ),

    # =========================================================================
    # TC-071 – TC-100: Multi-skill cross-domain scenarios (30 cases)
    # =========================================================================

    RoutingTestCase(
        id="TC-071",
        description="Add a new native system daemon 'foobar' that runs at boot in its own SELinux domain, exposes a Unix socket, and is built from C++ source in vendor/.",
        expected_paths=["system/core/init/", "system/sepolicy/", "vendor/"],
        expected_skill="L2-init-boot-sequence-expert",
        notes="MULTI-SKILL: init (rc file) + security (SELinux domain, socket label) + build (Android.bp). "
              "Primary: L2-init-boot-sequence-expert. See Pattern 1 in cross_skill_triggers.md.",
    ),
    RoutingTestCase(
        id="TC-072",
        description="Create a new AIDL HAL 'android.hardware.biometric.iris@1.0' end-to-end: interface definition, HAL server daemon, .rc file, SELinux policy, and hwservice_contexts.",
        expected_paths=["hardware/interfaces/", "system/sepolicy/", "system/core/init/"],
        expected_skill="L2-hal-vendor-interface-expert",
        notes="MULTI-SKILL: HAL (interface definition, AIDL freeze) + security (hwservice_contexts, .te) "
              "+ init (.rc with class hal) + build (aidl_interface, cc_binary). "
              "See Pattern 2 in cross_skill_triggers.md.",
    ),
    RoutingTestCase(
        id="TC-073",
        description="Our device migration from Android 14 to 15 is failing at build time. The sepolicy build fails with a neverallow violation, and several HAL interface versions need bumping.",
        expected_paths=["system/sepolicy/", "hardware/interfaces/"],
        expected_skill="L2-version-migration-expert",
        notes="MULTI-SKILL: migration (impact assessment) + security (neverallow fix) + HAL (version bump). "
              "Primary: migration expert for planning, then security and HAL for execution.",
    ),
    RoutingTestCase(
        id="TC-074",
        description="Add a new kernel driver for a custom sensor chip, package it as a GKI module, create the /dev node, and expose it via an AIDL sensor HAL.",
        expected_paths=["kernel/", "drivers/", "hardware/interfaces/sensors/", "system/sepolicy/"],
        expected_skill="L2-kernel-gki-expert",
        notes="MULTI-SKILL: kernel (driver + GKI module) + HAL (AIDL sensor interface) "
              "+ security (device node label) + init (ueventd.rc for permissions). "
              "See Pattern 4 in cross_skill_triggers.md.",
    ),
    RoutingTestCase(
        id="TC-075",
        description="Device is stuck in a boot loop. Logcat shows init restarting 'vendor.foo' 4 times, then an avc:denied for the foo executable, then a kernel panic.",
        expected_paths=["system/core/init/", "system/sepolicy/", "kernel/"],
        expected_skill="L2-init-boot-sequence-expert",
        notes="MULTI-SKILL: init (restart loop) + security (avc:denied) + kernel (panic). "
              "Load in order: init → security → kernel. See Pattern 5 in cross_skill_triggers.md.",
    ),
    RoutingTestCase(
        id="TC-076",
        description="Add FooService to SystemServer: implement the Java service, register with ServiceManager, add a @SystemApi, and write the SELinux binder_call allow rule.",
        expected_paths=["frameworks/base/services/", "frameworks/base/api/", "system/sepolicy/"],
        expected_skill="L2-framework-services-expert",
        notes="MULTI-SKILL: framework (service + @SystemApi) + security (binder_call allow rule) "
              "+ build (api update). See Pattern 6 in cross_skill_triggers.md.",
    ),
    RoutingTestCase(
        id="TC-077",
        description="Upgrade the audio HAL from AIDL v2 to v3. Update AudioFlinger to use the new IModule interface, update the HAL server, and update the SELinux audioserver domain.",
        expected_paths=["frameworks/av/services/audioflinger/", "hardware/interfaces/audio/", "system/sepolicy/"],
        expected_skill="L2-multimedia-audio-expert",
        notes="MULTI-SKILL: multimedia (AudioFlinger) + HAL (AIDL version bump, IModule) "
              "+ security (audioserver .te update). See Pattern 7 in cross_skill_triggers.md.",
    ),
    RoutingTestCase(
        id="TC-078",
        description="Add an eBPF-based per-UID traffic classifier to netd that reads per-socket stats from the kernel and exposes them via ConnectivityService.",
        expected_paths=["system/netd/", "packages/modules/Connectivity/", "kernel/"],
        expected_skill="L2-connectivity-network-expert",
        notes="MULTI-SKILL: connectivity (netd, ConnectivityService) + kernel (eBPF program, socket stats). "
              "See Pattern 8 in cross_skill_triggers.md.",
    ),
    RoutingTestCase(
        id="TC-079",
        description="Enable a Microdroid-based isolated computation environment in our app: write the VM config, implement the VM payload, add vsock IPC to the host, and set SELinux policy.",
        expected_paths=["packages/modules/Virtualization/", "system/sepolicy/"],
        expected_skill="L2-virtualization-pkvm-expert",
        notes="MULTI-SKILL: virtualization (AVF, Microdroid, vsock) + security (guest + host policy). "
              "See Pattern 9 in cross_skill_triggers.md.",
    ),
    RoutingTestCase(
        id="TC-080",
        description="Implement an OEM secure boot key enrollment that adds a new key to the ATF BL2 chain of trust and verifies it through the LK AVB boot flow.",
        expected_paths=["atf/", "bootloader/lk/"],
        expected_skill="L2-trusted-firmware-atf-expert",
        notes="MULTI-SKILL: ATF (BL2 chain of trust, key enrollment) + bootloader (AVB verification in LK). "
              "See Pattern 10 in cross_skill_triggers.md.",
    ),
    RoutingTestCase(
        id="TC-081",
        description="Our new HAL server runs with 'user nobody' but needs to access /dev/sensor0. The build works but the daemon crashes at runtime with EACCES. Diagnose and fix.",
        expected_paths=["system/sepolicy/", "system/core/init/"],
        expected_skill="L2-security-selinux-expert",
        notes="MULTI-SKILL: security (device node access — SELinux and Unix permissions) "
              "+ init (rc user/group and supplemental groups). "
              "Primary: security expert to audit access path.",
    ),
    RoutingTestCase(
        id="TC-082",
        description="After an A14→A15 upgrade our Bluetooth HAL registration fails at boot. The vintf manifest says version 2 but the new platform requires version 3. Fix the full upgrade path.",
        expected_paths=["packages/apps/Bluetooth/", "hardware/interfaces/bluetooth/"],
        expected_skill="L2-version-migration-expert",
        notes="MULTI-SKILL: migration (version impact assessment) + connectivity (BluetoothService) "
              "+ HAL (BT HAL AIDL version bump to v3).",
    ),
    RoutingTestCase(
        id="TC-083",
        description="Add a new Wi-Fi feature requiring both a new Wi-Fi HAL AIDL method and a ConnectivityService API change. Include tests for both layers.",
        expected_paths=["packages/modules/Wifi/", "packages/modules/Connectivity/", "hardware/interfaces/wifi/"],
        expected_skill="L2-connectivity-network-expert",
        notes="MULTI-SKILL: connectivity (WifiManager, ConnectivityService) + HAL (Wi-Fi AIDL interface). "
              "Requires L2-connectivity-network-expert and L2-hal-vendor-interface-expert.",
    ),
    RoutingTestCase(
        id="TC-084",
        description="A new vendor kernel driver needs to communicate with a Trusty TA via the tipc kernel driver. Describe the full integration path from the vendor driver to the TA.",
        expected_paths=["kernel/", "drivers/trusty/", "trusty/"],
        expected_skill="L2-kernel-gki-expert",
        notes="MULTI-SKILL: kernel (vendor driver, tipc kernel interface) + ATF (Trusty TA on BL32). "
              "Primary: kernel expert for the driver side; ATF expert for Trusty TA.",
    ),
    RoutingTestCase(
        id="TC-085",
        description="SurfaceFlinger is dropping frames when our new Camera HAL delivers frames faster than 60fps. Trace the bottleneck across CameraService, BufferQueue, and SurfaceFlinger.",
        expected_paths=["frameworks/av/services/camera/", "frameworks/native/services/surfaceflinger/"],
        expected_skill="L2-multimedia-audio-expert",
        notes="MULTI-SKILL: multimedia (CameraService, SurfaceFlinger, BufferQueue). "
              "Both components are owned by L2-multimedia-audio-expert.",
    ),
    RoutingTestCase(
        id="TC-086",
        description="Our device boots into recovery instead of normal boot after OTA. The ABL is marking the new slot unbootable. Debug from the LK/ABL side through to the kernel boot.",
        expected_paths=["bootloader/lk/", "kernel/", "bootable/recovery/"],
        expected_skill="L2-bootloader-lk-expert",
        notes="MULTI-SKILL: bootloader (ABL slot marking, A/B slot) + kernel (boot failure) "
              "+ init (recovery mode detection). Primary: bootloader expert.",
    ),
    RoutingTestCase(
        id="TC-087",
        description="Add a new @SystemApi to read pKVM hypervisor capabilities from Java. Implement the Binder interface, register it in SystemServer, and add SELinux binder_call rules.",
        expected_paths=["frameworks/base/services/", "packages/modules/Virtualization/", "system/sepolicy/"],
        expected_skill="L2-framework-services-expert",
        notes="MULTI-SKILL: framework (@SystemApi, SystemServer, Binder) + virtualization (pKVM caps) "
              "+ security (binder_call SELinux rules).",
    ),
    RoutingTestCase(
        id="TC-088",
        description="Add a GKI kernel module that creates a new netlink socket for vendor-to-kernel communication, with SELinux netlink socket labeling and an init .rc to start the userspace side.",
        expected_paths=["kernel/", "drivers/", "system/sepolicy/", "system/core/init/"],
        expected_skill="L2-kernel-gki-expert",
        notes="MULTI-SKILL: kernel (GKI module, netlink socket) + security (netlink label) "
              "+ init (.rc for userspace daemon). "
              "Primary: kernel expert for module; secondary: security and init.",
    ),
    RoutingTestCase(
        id="TC-089",
        description="Build a Rust-based Microdroid VM payload that performs attestation using the DICE chain and communicates results back to the host app via vsock.",
        expected_paths=["packages/modules/Virtualization/microdroid/", "packages/modules/Virtualization/libs/"],
        expected_skill="L2-virtualization-pkvm-expert",
        notes="MULTI-SKILL: virtualization (Microdroid payload, DICE attestation, vsock) "
              "+ build (rust_binary for payload). Single primary: L2-virtualization-pkvm-expert.",
    ),
    RoutingTestCase(
        id="TC-090",
        description="Debug a PSCI suspend failure: after ATF BL31 returns from CPU_SUSPEND, the Linux kernel panics in the wakeup path. Identify the boundary between ATF and kernel.",
        expected_paths=["atf/", "kernel/"],
        expected_skill="L2-trusted-firmware-atf-expert",
        notes="MULTI-SKILL: ATF (PSCI CPU_SUSPEND in BL31) + kernel (wakeup path panic). "
              "ATF is the primary for the PSCI implementation; kernel expert for the wakeup handler.",
    ),
    RoutingTestCase(
        id="TC-091",
        description="After enabling enforcing mode for SELinux, our audio daemon gets 'avc: denied { ioctl }' on /dev/snd/. Add the minimal allow rule without breaking neverallow.",
        expected_paths=["system/sepolicy/", "frameworks/av/services/audioflinger/"],
        expected_skill="L2-security-selinux-expert",
        notes="MULTI-SKILL: security (ioctl allowlist for /dev/snd) + multimedia (audioserver domain). "
              "Primary: security expert to check neverallow and write the allowlist.",
    ),
    RoutingTestCase(
        id="TC-092",
        description="Our VNDK library 'libvndk_foo' is linking against libicuuc which is not in the VNDK. The build fails. How do I resolve the dependency while maintaining Treble compliance?",
        expected_paths=["system/vndk/", "vendor/", "build/"],
        expected_skill="L2-hal-vendor-interface-expert",
        notes="MULTI-SKILL: HAL/Treble (VNDK dependency resolution) + build (Android.bp fix). "
              "Primary: HAL expert for the Treble boundary analysis.",
    ),
    RoutingTestCase(
        id="TC-093",
        description="We need to pass a custom bootargs parameter from the LK bootloader into the Android init environment. How does LK set androidboot.* properties and how does init read them?",
        expected_paths=["bootloader/lk/", "system/core/init/"],
        expected_skill="L2-bootloader-lk-expert",
        notes="MULTI-SKILL: bootloader (androidboot.* kernel cmdline in LK) + init (property import from cmdline). "
              "Primary: bootloader expert for the LK side.",
    ),
    RoutingTestCase(
        id="TC-094",
        description="Add Bluetooth LE audio support: requires new BT HAL AIDL methods, BluetoothService changes, audio HAL profile integration, and SELinux updates.",
        expected_paths=["packages/apps/Bluetooth/", "hardware/interfaces/bluetooth/", "frameworks/av/services/audioflinger/"],
        expected_skill="L2-connectivity-network-expert",
        notes="MULTI-SKILL: connectivity (BT stack, BluetoothService) + HAL (BT AIDL) "
              "+ multimedia (audio HAL profile) + security (SELinux for new BT audio domain). "
              "3-skill scenario — primary: connectivity expert.",
    ),
    RoutingTestCase(
        id="TC-095",
        description="Our device's recovery partition needs to verify a vendor-specific signature before applying OTA. How do I integrate a new verification plugin into recovery and the secure boot chain?",
        expected_paths=["bootable/recovery/", "atf/", "bootloader/lk/"],
        expected_skill="L2-init-boot-sequence-expert",
        notes="MULTI-SKILL: init/recovery (recovery partition, OTA verification) "
              "+ bootloader (LK handoff to recovery) + ATF (secure boot chain). "
              "Primary: init expert for recovery; ATF expert for chain of trust.",
    ),
    RoutingTestCase(
        id="TC-096",
        description="Implement a new pKVM-based secure enclave service: Microdroid VM hosts a key derivation TA, host app connects via vsock, add SELinux policy for host and guest.",
        expected_paths=["packages/modules/Virtualization/", "system/sepolicy/"],
        expected_skill="L2-virtualization-pkvm-expert",
        notes="MULTI-SKILL: virtualization (pKVM, Microdroid, vsock) + security (host + guest SELinux). "
              "3-skill scenario: virtualization primary, security secondary, framework for API.",
    ),
    RoutingTestCase(
        id="TC-097",
        description="Build a full-stack feature for Android 15: new AIDL HAL for a thermal sensor, GKI kernel driver, SELinux policy, init .rc, and ConnectivityService integration for thermal throttling.",
        expected_paths=["hardware/interfaces/thermal/", "kernel/", "system/sepolicy/", "system/core/init/", "packages/modules/Connectivity/"],
        expected_skill="L2-hal-vendor-interface-expert",
        notes="MULTI-SKILL: HAL (thermal AIDL) + kernel (GKI driver) + security (SELinux) "
              "+ init (.rc) + connectivity (thermal throttling in framework). "
              "Full-stack 5-skill scenario. Route in priority order.",
    ),
    RoutingTestCase(
        id="TC-098",
        description="After Android 15 upgrade, our device fails vintf compatibility check: the audio HAL version in the manifest doesn't match the framework matrix. SELinux also has new neverallow violations.",
        expected_paths=["hardware/interfaces/audio/", "system/sepolicy/"],
        expected_skill="L2-version-migration-expert",
        notes="MULTI-SKILL: migration (vintf compatibility, version planning) "
              "+ HAL (audio HAL version bump) + security (neverallow fixes). "
              "Primary: migration expert for assessment.",
    ),
    RoutingTestCase(
        id="TC-099",
        description="Create a new AOSP platform test for pKVM isolation: the test launches a Microdroid VM, injects a payload, verifies the host cannot read guest memory, and validates vsock IPC.",
        expected_paths=["packages/modules/Virtualization/", "kernel/"],
        expected_skill="L2-virtualization-pkvm-expert",
        notes="MULTI-SKILL: virtualization (Microdroid test, vsock, pKVM isolation assertion) "
              "+ kernel (stage-2 page table verification). "
              "This is VirtualizationTestCases territory.",
    ),
    RoutingTestCase(
        id="TC-100",
        description="Full integration: add a new HAL-backed system service with @SystemApi, secure the IPC with SELinux, launch a Microdroid VM to perform isolated computation, and expose results via the new @SystemApi.",
        expected_paths=["frameworks/base/services/", "hardware/interfaces/", "packages/modules/Virtualization/", "system/sepolicy/"],
        expected_skill="L2-framework-services-expert",
        notes="MULTI-SKILL: framework (@SystemApi, SystemServer) + HAL (new interface) "
              "+ virtualization (Microdroid isolated compute) + security (full SELinux stack). "
              "Maximum complexity scenario — tests all 4 top priority skills simultaneously.",
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

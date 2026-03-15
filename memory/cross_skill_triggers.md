# Cross-Skill Trigger Patterns

> **Version:** 1.0
> **Date:** 2026-03-15
> **Purpose:** Documents task types that activate two or more L2 skills simultaneously.
> Used by the L1 router to plan multi-skill execution order.

---

## Overview

Most AOSP tasks cross subsystem boundaries. When the L1 router detects a multi-skill task, it loads skills in **priority order** and emits a `[MULTI-SKILL]` routing header listing all skills to activate.

```
[L1 ROUTING DECISION — MULTI-SKILL]
Intent: <task>
Skills: L2-security-selinux-expert → L2-init-boot-sequence-expert → L2-hal-vendor-interface-expert
Reason: New HAL daemon requires domain, rc file, and hwservice_contexts
[END ROUTING → loading L2 skills in order]
```

---

## Pattern Catalogue

### Pattern 1: Add a New System Daemon

**Trigger keywords:** new daemon, new service, `init.rc`, SELinux domain

**Skills activated (in order):**
1. `L2-init-boot-sequence-expert` — `.rc` service definition, socket, file descriptor
2. `L2-security-selinux-expert` — new domain type, `file_contexts`, `property_contexts`
3. `L2-build-system-expert` — `cc_binary` / `rust_binary` in `Android.bp`, install path

**Example task:** *"Add a new native daemon `foobar` that starts at boot, exposes a socket, and runs in its own SELinux domain."*

---

### Pattern 2: Add a New HAL Interface

**Trigger keywords:** new HAL, AIDL interface, HIDL, `hardware/interfaces/`, vendor service

**Skills activated (in order):**
1. `L2-hal-vendor-interface-expert` — AIDL definition, versioning, `android.hardware.*` package
2. `L2-security-selinux-expert` — `hwservice_contexts`, `vndservice_contexts`, HAL domain `.te`
3. `L2-init-boot-sequence-expert` — HAL server `.rc` file, `class hal`
4. `L2-build-system-expert` — `aidl_interface`, `cc_binary` for HAL server

**Example task:** *"Create a new `android.hardware.sensor.fusion@1.0` AIDL HAL and wire it up end-to-end."*

---

### Pattern 3: Android OS Version Upgrade (A14 → A15)

**Trigger keywords:** version upgrade, A14→A15, migration, API level bump, 16KB page

**Skills activated (in order):**
1. `L2-version-migration-expert` — diff analysis, impact checklist, deprecated APIs
2. `L2-hal-vendor-interface-expert` — HAL interface version freeze / bump
3. `L2-security-selinux-expert` — neverallow changes, new policy requirements
4. `L2-build-system-expert` — build flag changes, soong config variables
5. `L2-kernel-gki-expert` — GKI ABI changes, symbol list updates

**Example task:** *"Plan the migration of our device from Android 14 to Android 15."*

---

### Pattern 4: Add a New Kernel Driver with Userspace Interface

**Trigger keywords:** new driver, `drivers/`, sysfs, device node, kernel module, userspace access

**Skills activated (in order):**
1. `L2-kernel-gki-expert` — driver implementation, GKI module interface, symbol list
2. `L2-security-selinux-expert` — device node label (`file_contexts`), `chr_file` or `blk_file` access
3. `L2-hal-vendor-interface-expert` — if userspace accesses driver via HAL AIDL interface
4. `L2-init-boot-sequence-expert` — `ueventd.rc` for device node permissions, `insmod` in `.rc`

**Example task:** *"Add a new character device driver for a custom sensor and expose it to the sensor HAL."*

---

### Pattern 5: Boot Failure Diagnosis

**Trigger keywords:** device doesn't boot, stuck at boot, `init` crash, panic, early boot

**Skills activated (in order):**
1. `L2-init-boot-sequence-expert` — `.rc` parsing errors, service crash loops, property triggers
2. `L2-security-selinux-expert` — SELinux `enforcing` mode blocking early services
3. `L2-kernel-gki-expert` — kernel panic, early `printk`, device tree issues
4. `L2-bootloader-lk-expert` — if boot fails before kernel loads (fastboot, ABL issue)

**Example task:** *"Device is stuck in a boot loop — the logs show `init` restarting repeatedly."*

---

### Pattern 6: New System Service with @SystemApi

**Trigger keywords:** `@SystemApi`, `SystemServer`, new system service, Java framework, binder

**Skills activated (in order):**
1. `L2-framework-services-expert` — service lifecycle, `SystemServer` registration, Binder interface
2. `L2-security-selinux-expert` — service type, `service_contexts`, `binder_call` allow rules
3. `L2-build-system-expert` — `java_library`, API file update, `api/current.txt`
4. `L2-hal-vendor-interface-expert` — if service wraps a vendor HAL via Binder/AIDL

**Example task:** *"Add a new Java system service `FooBarService` with a `@SystemApi` and register it in `SystemServer`."*

---

### Pattern 7: Audio/Media HAL Update

**Trigger keywords:** AudioFlinger, audio HAL, `hardware/interfaces/audio/`, media pipeline

**Skills activated (in order):**
1. `L2-multimedia-audio-expert` — AudioFlinger thread model, HAL integration, buffer flow
2. `L2-hal-vendor-interface-expert` — audio HAL AIDL version bump, `IModule`, `IStreamOut`
3. `L2-security-selinux-expert` — `mediaserver` or `audioserver` domain changes

**Example task:** *"Upgrade the audio HAL from AIDL v2 to v3 and integrate the new `IModule` interface into AudioFlinger."*

---

### Pattern 8: Network Stack Change with Kernel Impact

**Trigger keywords:** netd, eBPF, firewall, routing, `tc`, network driver, socket

**Skills activated (in order):**
1. `L2-connectivity-network-expert` — netd rules, ConnectivityService, `iptables`/`nftables`, eBPF
2. `L2-kernel-gki-expert` — kernel networking subsystem, eBPF program loading, socket buffer
3. `L2-security-selinux-expert` — netd domain, socket labeling, `netdomain` macro

**Example task:** *"Add an eBPF program to netd for per-app traffic metering that reads kernel socket stats."*

---

### Pattern 9: Protected VM (pKVM) Feature Integration

**Trigger keywords:** pKVM, Microdroid, AVF, `VirtualMachineManager`, virtual machine, crosvm, vsock

**Skills activated (in order):**
1. `L2-virtualization-pkvm-expert` — AVF stack, crosvm, Microdroid config, vsock IPC
2. `L2-security-selinux-expert` — `virtualizationservice.te`, Microdroid guest policy, `/dev/kvm` access
3. `L2-kernel-gki-expert` — pKVM EL2 config (`CONFIG_KVM`), `arch/arm64/kvm/hyp/` changes
4. `L2-framework-services-expert` — `VirtualMachineManager` Java API, binder service wiring

**Example task:** *"Integrate a Microdroid-based isolated compute environment into our app, with vsock IPC to the host."*

---

### Pattern 10: Secure Boot Chain Modification

**Trigger keywords:** AVB, secure boot, key enrollment, `vbmeta`, BL31, TrustZone, signing

**Skills activated (in order):**
1. `L2-bootloader-lk-expert` — AVB verification in ABL, `vbmeta` partition, key rollback index
2. `L2-trusted-firmware-atf-expert` — BL1/BL2 chain of trust, secure boot root key, BL31 handoff
3. `L2-security-selinux-expert` — `verified_boot` property, `avc: denied` for bootloader-written props
4. `L2-init-boot-sequence-expert` — `init` reads `ro.boot.*` properties from bootloader

**Example task:** *"Add a new OEM-signed key to our secure boot chain and enforce rollback protection."*

---

### Pattern 11: Bluetooth Feature Addition

**Trigger keywords:** Bluetooth, `system/bt/`, BluetoothService, BT HAL, GATT, `android.hardware.bluetooth`

**Skills activated (in order):**
1. `L2-connectivity-network-expert` — BluetoothService, Fluoride stack, BT profiles
2. `L2-hal-vendor-interface-expert` — `android.hardware.bluetooth` AIDL HAL version
3. `L2-security-selinux-expert` — `bluetooth` domain, socket access, HCI device node label

**Example task:** *"Add BLE scanning throttling in BluetoothService and update the Bluetooth HAL to expose scan parameters."*

---

### Pattern 12: GKI Module with SELinux and Init

**Trigger keywords:** GKI module, `insmod`, `modprobe`, early-init, kernel module, device tree

**Skills activated (in order):**
1. `L2-kernel-gki-expert` — module build (`android_kernel_module`), GKI symbol list, `Module.symvers`
2. `L2-init-boot-sequence-expert` — `insmod`/`modprobe` in `.rc`, `exec_start` triggers
3. `L2-security-selinux-expert` — module device node label, `vendor_file` contexts

**Example task:** *"Package our new sensor driver as a GKI module, load it at early-init, and create the device node."*

---

## Priority Order Reference

When multiple skills are needed, load in this order (matches L1 router priority):

```
Security > Build > HAL > Framework > Init > Bootloader > ATF > Virtualization > Migration > Media > Connectivity > Kernel
```

Exception: for boot failure diagnosis, reverse to `Init > Kernel > Security > Bootloader`.

---

*Document v1.0 — Phase 3 deliverable 3.2. Update when new multi-skill patterns are identified.*

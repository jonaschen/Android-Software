---
name: L2-virtualization-pkvm-expert
layer: L2
path_scope: packages/modules/Virtualization/, external/crosvm/, frameworks/libs/vmbase/
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

# L2 Expert: pKVM / Android Virtualization Framework

## Path Scope

| Path | Description |
|------|-------------|
| `packages/modules/Virtualization/` | AVF mainline module — VirtualizationService, Microdroid, VmPayloadService, vmbase |
| `packages/modules/Virtualization/microdroid/` | Microdroid minimal guest OS, init, microdroid_manager |
| `packages/modules/Virtualization/javalib/` | VirtualMachineManager Java API surface |
| `packages/modules/Virtualization/libs/` | Rust guest libraries (libvm_payload, libvmbase) |
| `external/crosvm/` | Rust Virtual Machine Monitor (VMM) — virtio backends, vhost, device emulation |
| `frameworks/libs/vmbase/` | Bare-metal Rust framework for early-boot VM stages |
| `kernel/` | pKVM EL2 hypervisor code (`arch/arm64/kvm/`) — handled jointly with L2-kernel-gki-expert |
| `system/sepolicy/` | Guest + host SELinux policy for AVF — handled jointly with L2-security-selinux-expert |
| `hardware/interfaces/virtualization/` | AVF AIDL HAL definitions (if present — vendor extension point) |

---

## Trigger Conditions

Load this skill when the user's task involves any of the following:

- **pKVM / KVM**: `pKVM`, `Protected KVM`, `/dev/kvm`, EL2 hypervisor, stage-2 page tables, VMID, IPA space, memory protection, `KVM_CREATE_VM`, hypervisor capabilities
- **Android Virtualization Framework (AVF)**: `VirtualMachineManager`, `VirtualizationService`, `VmPayloadService`, AVF, `android.system.virtualization`
- **Microdroid**: Microdroid, `microdroid_manager`, pVM, protected VM, guest OS boot, `microdroid_kernel`, DT overlay, guest SELinux policy
- **crosvm**: crosvm, Rust VMM, virtio-blk, virtio-net, virtio-console, virtio-vsock, vhost-user, device backend
- **vsock**: `AF_VSOCK`, vsock, host-to-guest IPC, `VMADDR_CID_HOST`, `VMADDR_CID_LOCAL`
- **vmbase**: vmbase, bare-metal Rust, early-boot VM, EL1 VM init
- **VM configuration**: `VirtualMachineConfig`, `VirtualMachineRawConfig`, Companion Device Manager, VM disk image, `vm` CLI tool

---

## Architecture Intelligence

### ARM Exception Level Model

```
EL3  -- ATF BL31 (Secure Monitor, SMC dispatcher)          [L2-trusted-firmware-atf-expert]
EL2  -- pKVM Hypervisor (stage-2 isolation, VMID mgmt)     [THIS SKILL]
EL1  -- Linux kernel (host) / Microdroid kernel (guest)    [L2-kernel-gki-expert for GKI]
EL0  -- Apps, crosvm VMM (host) / VM payload (guest)       [L2-framework-services-expert]
```

### Android Virtualization Framework (AVF) Stack

```
+--------------------------------------------+
|  App / System Service                      |  EL0 (host)
|  VirtualMachineManager Java API            |
+--------------------------------------------+
|  VirtualizationService (Rust, AIDL)        |  EL0 (host)
|  vm CLI tool                               |
+--------------------------------------------+
|  crosvm (Rust VMM)                         |  EL0 (host)
|  virtio-blk, virtio-net, vsock, console    |
+--------------------------------------------+
|  Linux kernel (host, GKI)                  |  EL1/EL2 (host)
|  KVM subsystem -- /dev/kvm                 |
+============================================+
|  pKVM Hypervisor (arch/arm64/kvm/hyp/)     |  EL2
|  Stage-2 page table isolation              |
|  VMID namespace management                 |
+============================================+
|  Microdroid kernel + init                  |  EL1 (guest)
|  microdroid_manager                        |
|  VM payload (APK / native)                 |  EL0 (guest)
+--------------------------------------------+
```

### pKVM Core Concepts

| Concept | Detail |
|---------|--------|
| **Stage-2 page tables** | EL2-controlled IPA->PA mapping; host kernel cannot access guest memory once protected |
| **VMID** | 16-bit hardware namespace; pKVM assigns and rotates VMIDs |
| **Protected VM (pVM)** | Guest whose memory is inaccessible to host kernel -- enforced in EL2 |
| **Non-Protected VM** | Regular KVM VM; host retains full memory access |
| **`/dev/kvm`** | Character device gating all KVM/pKVM access; SELinux-controlled |
| **`KVM_CREATE_VM`** | ioctl to instantiate a VM; triggers EL2 VMID allocation |
| **MMIO emulation** | crosvm handles MMIO exits from the guest via the KVM ioctl interface |

### Microdroid Boot Flow

```
1. VirtualizationService -> crosvm launch (host EL0)
2. crosvm -> KVM_CREATE_VM ioctl -> pKVM EL2 setup stage-2 tables
3. Microdroid kernel boots at EL1 (guest)
4. microdroid_manager starts (PID 1 equivalent in guest)
5. microdroid_manager mounts APK/payload disk (virtio-blk)
6. VM payload executes in guest EL0
7. vsock (AF_VSOCK) available for host<->guest IPC
```

### crosvm Architecture

```
crosvm process (host EL0)
+-- main thread: VM lifecycle, KVM fd management
+-- vcpu threads: one per vCPU, runs KVM_RUN ioctl
+-- virtio-blk: serves guest disk I/O via KVM mmio exit
+-- virtio-net: TAP/virtio network backend
+-- virtio-vsock: AF_VSOCK host<->guest socket relay
+-- virtio-console: serial console, adb logcat
+-- vhost-user: optional out-of-process device backends
```

### Key Source Locations

| Component | Path |
|-----------|------|
| VirtualizationService | `packages/modules/Virtualization/virtualizationservice/` |
| VirtualMachineManager API | `packages/modules/Virtualization/javalib/` |
| microdroid_manager | `packages/modules/Virtualization/microdroid/` |
| vmbase | `packages/modules/Virtualization/libs/vmbase/` |
| crosvm | `external/crosvm/` |
| pKVM EL2 code | `arch/arm64/kvm/hyp/` (in kernel tree) |
| AVF SELinux policy | `system/sepolicy/private/virtualizationservice.te`, `microdroid_manager.te` |
| AVF AIDL | `packages/modules/Virtualization/virtualizationservice/aidl/` |
| `vm` CLI tool | `packages/modules/Virtualization/vm/` |

---

## Forbidden Actions

1. **Never route pKVM EL2 bugs to L2-trusted-firmware-atf-expert.** EL2 is pKVM/KVM territory; EL3 is ATF/BL31. They are distinct exception levels. Escalate to L2-kernel-gki-expert for kernel-side KVM changes.
2. **Never modify guest SELinux policy without consulting L2-security-selinux-expert.** Guest policy lives in `microdroid/` subdirs but must be consistent with `system/sepolicy/` conventions.
3. **Never assume `/dev/kvm` is present.** pKVM requires `CONFIG_KVM=y` and hypervisor support enabled at boot. Always check `ro.boot.hypervisor.protected_vm.supported` before assuming pVM capability.
4. **Never use vsock CID 0 or 1.** CID 0 is reserved; CID 1 is hypervisor-reserved. Host uses `VMADDR_CID_HOST` (2); guests use dynamically assigned CIDs. Hardcoding CIDs causes silent connectivity failures.
5. **Never add virtio device backends inside the guest kernel.** Virtio backends live in crosvm (host EL0). The guest kernel only contains the virtio frontend (virtio_blk, virtio_net, etc.).
6. **Never route VirtualizationService AIDL changes to L2-hal-vendor-interface-expert.** AVF AIDL is a mainline module interface (`android.system.virtualmachine`), not a vendor HAL. Use L2-framework-services-expert for API surface questions.
7. **Never assume crosvm has a C/C++ implementation.** crosvm is written entirely in Rust. Do not suggest C++ refactors or apply C++ build patterns (`cc_binary`); use `rust_binary` in `Android.bp`.

---

## Tool Calls

### check_pkvm_status.sh
```
scripts/check_pkvm_status.sh [--adb-serial <serial>]
```
Checks: `/dev/kvm` presence, `ro.boot.hypervisor.*` props, AVF feature flag, running VMs via `vm list`.

### Useful `adb` commands

```bash
# Check pKVM support
adb shell getprop ro.boot.hypervisor.protected_vm.supported
adb shell getprop ro.boot.hypervisor.vm.supported
adb shell ls -la /dev/kvm

# List running VMs
adb shell vm list

# Run a Microdroid test VM
adb shell vm run-microdroid --mem-mib 512

# Inspect crosvm logs
adb logcat -s crosvm VirtualizationService

# Inspect guest console output
adb shell vm console <cid>
```

### Build targets

```bash
# Build AVF mainline module
m VirtualizationService microdroid

# Build crosvm
m crosvm

# Run AVF integration tests
atest VirtualizationTestCases
atest MicrodroidTests
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| pKVM EL2 code change in `arch/arm64/kvm/hyp/` | `L2-kernel-gki-expert` |
| Guest or host SELinux avc:denied involving `/dev/kvm` or Microdroid policy | `L2-security-selinux-expert` |
| SMC call interaction between pKVM and ATF BL31 | `L2-trusted-firmware-atf-expert` |
| `VirtualMachineManager` API surface change | `L2-framework-services-expert` |
| `Android.bp` build issues for `rust_binary` AVF targets | `L2-build-system-expert` |
| Android version migration (AVF API compat) | `L2-version-migration-expert` |

Emit `[L2 VIRT → HANDOFF]` before transferring.

---

## References

- `references/pkvm_microdroid_architecture.md` -- Deep dive: pKVM EL2 isolation, crosvm VMM, Microdroid boot flow, vsock IPC
- `packages/modules/Virtualization/README.md` -- Official AVF module documentation
- Android Security Bulletin: pKVM protection guarantees

# pKVM, Microdroid, and crosvm Architecture Reference

> **Version:** 1.0
> **Android Version:** Android 15 (AVF mainline module)
> **Skill:** L2-virtualization-pkvm-expert
> **Purpose:** Deep-dive architectural reference for pKVM EL2 isolation, the Android Virtualization Framework (AVF) stack, crosvm VMM design, Microdroid guest OS boot flow, and vsock host↔guest IPC.

---

## 1. ARM Exception Level Recap

```
┌──────────────────────────────────────────────────────────────┐
│ EL3  Secure Monitor (ATF BL31)                               │
│      SMC dispatcher, PSCI, platform power management         │
│      [L2-trusted-firmware-atf-expert]                        │
├──────────────────────────────────────────────────────────────┤
│ EL2  pKVM Hypervisor  (arch/arm64/kvm/hyp/)                  │
│      Stage-2 page table isolation, VMID management           │
│      [THIS SKILL]                                            │
├──────────────────────────────────────────────────────────────┤
│ EL1  Linux host kernel (GKI)  /  Microdroid kernel (guest)   │
│      [L2-kernel-gki-expert for GKI changes]                  │
├──────────────────────────────────────────────────────────────┤
│ EL0  Host userspace: crosvm, VirtualizationService, apps     │
│      Guest userspace: VM payload, microdroid_manager         │
└──────────────────────────────────────────────────────────────┘
```

**Key boundary:** pKVM lives exclusively at EL2. Once the host kernel boots and pKVM takes control of EL2, the host kernel is demoted to EL1. The host kernel can no longer read or write guest physical memory in a protected VM — this is enforced by the EL2 stage-2 page tables, not by software policy.

---

## 2. pKVM Core Architecture

### 2.1 Stage-2 Page Table Isolation

ARM's virtualization support provides two levels of address translation for VMs:

```
Guest Virtual Address (VA)
    │  (stage-1, managed by guest kernel at EL1)
    ▼
Guest Physical Address (IPA — Intermediate Physical Address)
    │  (stage-2, managed by pKVM at EL2)
    ▼
Host Physical Address (PA)
```

In **non-protected VMs** (regular KVM), the host kernel retains a mapping to all guest physical memory — the host can inspect or modify the guest at any time.

In **protected VMs (pVMs)**, pKVM removes the host kernel's stage-2 mapping to guest pages once they are donated to the guest. The host kernel has no path to read guest memory, even in kernel mode.

### 2.2 VMID Namespace

Each VM is assigned a **VMID (Virtual Machine ID)** — a 16-bit ARM hardware namespace that tags TLB entries. pKVM manages VMID allocation and rotation to prevent TLB aliasing between VMs. This is transparent to the host kernel.

### 2.3 Key Kernel Interfaces

| Interface | Location | Purpose |
|-----------|----------|---------|
| `/dev/kvm` | `drivers/virt/kvm/` | Character device; gate for all VM operations |
| `KVM_CREATE_VM` | `arch/arm64/kvm/` | ioctl to create a VM; triggers EL2 VMID allocation |
| `KVM_CREATE_VCPU` | `arch/arm64/kvm/` | ioctl to create a virtual CPU |
| `KVM_RUN` | `arch/arm64/kvm/` | ioctl to run a vCPU until an exit condition |
| `KVM_SET_USER_MEMORY_REGION` | `arch/arm64/kvm/` | Map host memory into guest IPA space |
| `KVM_ARM_VCPU_INIT` | `arch/arm64/kvm/` | ARM-specific vCPU initialization |

### 2.4 pKVM EL2 Entry Points

The pKVM EL2 code lives in `arch/arm64/kvm/hyp/`. Key files:

| File | Role |
|------|------|
| `nvhe/host.S` | EL2 entry/exit for host hypercalls |
| `nvhe/mem_protect.c` | Stage-2 memory protection, page donation |
| `nvhe/pkvm.c` | pKVM initialization, VMID management |
| `nvhe/switch.c` | Host↔guest world switch |
| `nvhe/tlb.c` | TLB invalidation at EL2 |

---

## 3. Android Virtualization Framework (AVF) Stack

### 3.1 Full Component Stack

```
┌─────────────────────────────────────────────────────────────┐
│  Java Application Layer                                     │
│  VirtualMachineManager  (packages/modules/Virtualization/   │
│                          javalib/)                          │
│  android.system.virtualmachine.*                            │
├─────────────────────────────────────────────────────────────┤
│  VirtualizationService  (Rust, AIDL server)                 │
│  packages/modules/Virtualization/virtualizationservice/     │
│  Manages VM lifecycle, disk images, CID assignment          │
├─────────────────────────────────────────────────────────────┤
│  crosvm  (Rust VMM)                                         │
│  external/crosvm/                                           │
│  virtio device backends, vCPU threads, KVM fd management    │
├─────────────────────────────────────────────────────────────┤
│  Linux host kernel + KVM subsystem                          │
│  /dev/kvm, arch/arm64/kvm/                                  │
│════════════════════════════════════════════════════════════ │
│  pKVM hypervisor (EL2)                                      │
│  arch/arm64/kvm/hyp/nvhe/                                   │
╞═════════════════════════════════════════════════════════════╡
│  Microdroid (guest)                                         │
│  packages/modules/Virtualization/microdroid/                │
│  Microdroid kernel → init → microdroid_manager → payload    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 VirtualMachineManager Java API

Key classes in `packages/modules/Virtualization/javalib/`:

| Class | Purpose |
|-------|---------|
| `VirtualMachineManager` | Entry point; `create()`, `get()`, `getOrCreate()` |
| `VirtualMachine` | Represents a VM instance; `run()`, `stop()`, `connectToVsockServer()` |
| `VirtualMachineConfig` | High-level VM config (APK path, memory, CPU count) |
| `VirtualMachineRawConfig` | Low-level config (disk images, kernel, initrd) |
| `VirtualMachineCallback` | Callbacks for VM lifecycle events (started, stopped, error) |

### 3.3 VirtualizationService (Rust AIDL Server)

- AIDL interface: `packages/modules/Virtualization/virtualizationservice/aidl/android/system/virtualmachine/IVirtualizationService.aidl`
- Responsibilities:
  - Launch/stop crosvm processes
  - Manage disk image composition (APK + extra APKs + instance disk)
  - Assign vsock CIDs
  - Enforce `android.permission.MANAGE_VIRTUAL_MACHINE`
- Communicates with `microdroid_manager` via vsock after VM boot

### 3.4 `vm` CLI Tool

Located in `packages/modules/Virtualization/vm/`. Useful for development:

```bash
# List running VMs
adb shell vm list

# Run a raw VM with a custom kernel
adb shell vm run --kernel <path> --mem-mib 512

# Run a Microdroid VM
adb shell vm run-microdroid --mem-mib 512

# Show console output from a running VM
adb shell vm console <cid>
```

---

## 4. crosvm VMM Architecture

### 4.1 Process Structure

```
crosvm (main process)
│
├── main thread
│   ├── Parses VM config (from VirtualizationService via flags)
│   ├── Opens /dev/kvm, calls KVM_CREATE_VM
│   ├── Sets up memory regions (KVM_SET_USER_MEMORY_REGION)
│   ├── Creates and configures virtio devices
│   └── Spawns vCPU threads and device threads
│
├── vCPU thread(s)  [one per virtual CPU]
│   └── Loops: KVM_RUN → handle VM exit → KVM_RUN
│       Exits handled: MMIO, I/O port, hypercall, shutdown
│
└── device threads (virtio backends)
    ├── virtio-blk:     serves guest disk I/O via MMIO exits
    ├── virtio-net:     TAP or slirp network backend
    ├── virtio-console: serial console, guest log output
    ├── virtio-vsock:   AF_VSOCK relay (host ↔ guest IPC)
    └── virtio-rng:     entropy injection for guest
```

### 4.2 Virtio Device Communication

Virtio devices use **split queues**: a descriptor ring in shared memory between guest and host.

```
Guest driver (EL1)              Host backend (crosvm, EL0)
      │                                │
      │  1. Fill descriptor ring       │
      │  2. Write avail ring index     │
      │  3. Kick via MMIO write ──────►│
      │                                │  4. Process descriptor
      │                                │  5. Write used ring
      │  6. IRQ (virtio interrupt) ◄───│
      │  7. Read used ring             │
```

pKVM MMIO exit path: Guest MMIO write → EL2 MMIO exit trap → KVM delivers to crosvm vCPU thread → crosvm backend processes → response.

### 4.3 Key crosvm Source Locations

| Component | Path |
|-----------|------|
| Main entry point | `external/crosvm/src/main.rs` |
| VM configuration | `external/crosvm/src/crosvm/config.rs` |
| KVM bindings | `external/crosvm/hypervisor/src/kvm/` |
| virtio device backends | `external/crosvm/devices/src/virtio/` |
| virtio-blk | `external/crosvm/devices/src/virtio/block/` |
| virtio-vsock | `external/crosvm/devices/src/virtio/vsock/` |
| virtio-net | `external/crosvm/devices/src/virtio/net.rs` |

---

## 5. Microdroid Guest OS

### 5.1 Boot Flow

```
Step 1: crosvm launches, loads microdroid_kernel + initrd into guest memory
        pKVM allocates VMID, sets up stage-2 page tables

Step 2: Microdroid kernel boots at EL1 (guest)
        - ARM64 boot protocol: kernel at 0x80000, DTB at 0x40000000
        - Kernel command line from VM config (via device tree)

Step 3: init starts (PID 1)
        - Reads /init.rc and device-specific .rc files
        - Starts microdroid_manager (via init.rc service definition)

Step 4: microdroid_manager (Rust, PID > 1)
        - Connects to VirtualizationService on host via vsock
        - Receives VM configuration (APK path, payload config)
        - Mounts the APK disk image (virtio-blk)
        - Extracts and verifies the native payload library
        - Sets up guest SELinux policy and transitions context
        - Executes the VM payload (JNI library or native binary)

Step 5: VM payload runs in guest EL0
        - Communicates with host app via vsock
        - Can use libvm_payload APIs for attestation, secrets
```

### 5.2 Disk Image Composition

A Microdroid VM uses multiple virtio-blk disk images:

| Disk | Contents | Writable? |
|------|----------|-----------|
| `microdroid.img` | Microdroid OS rootfs (read-only, dm-verity) | No |
| APK disk | The host APK containing the VM payload | No |
| Instance disk | Per-VM persistent state, sealed secrets (DICE) | Yes |
| Extra APKs | Additional APKs for the payload (optional) | No |

### 5.3 DICE and VM Identity

Each Microdroid VM gets a unique cryptographic identity via **DICE (Device Identifier Composition Engine)**:

```
ATF BL1/BL2
    └── DICE measurement chain
         └── Microdroid kernel hash
              └── microdroid_manager config hash
                   └── Payload APK hash
                        └── → Unique VM CDI (Compound Device Identifier)
                             └── → VM can derive attestation keys, sealed secrets
```

This chain means that any change in the boot configuration invalidates previously sealed secrets — a key security property of pVMs.

---

## 6. vsock Host↔Guest IPC

### 6.1 AF_VSOCK Overview

vsock is a socket family designed for host↔guest communication without requiring a network stack:

```
Host (CID=2)              Guest (CID=assigned by VirtualizationService)
     │                           │
     │  connect(VMADDR_CID_GUEST, port=5678)
     │ ─────────────────────────►│
     │                           │
     │◄─────────────────────────►│  bidirectional byte stream
```

Key CID constants:

| CID | Value | Meaning |
|-----|-------|---------|
| `VMADDR_CID_HYPERVISOR` | 0 | Reserved (do not use) |
| `VMADDR_CID_RESERVED` | 1 | Reserved (do not use) |
| `VMADDR_CID_HOST` | 2 | The host kernel/userspace |
| `VMADDR_CID_LOCAL` | 3 | Loopback (same context) |
| Guest CIDs | 4+ | Assigned dynamically by VirtualizationService |

### 6.2 vsock in AVF

```
VirtualizationService (host)
    │  assigns CID N to the new VM
    │  crosvm starts with --cid N
    │
crosvm virtio-vsock backend
    │  relays vsock frames between host socket and guest kernel
    │
Microdroid kernel virtio-vsock driver
    │  exposes AF_VSOCK to guest userspace
    │
microdroid_manager / VM payload
    └── can bind vsock server ports or connect to host ports
```

### 6.3 Connecting from Host App

```java
// Java API — connect to a vsock server running inside the VM
VirtualMachine vm = vmManager.getOrCreate("myVm", config);
vm.run();
// Wait for VM to boot, then:
ParcelFileDescriptor fd = vm.connectToVsockServer(5678); // port 5678
// fd wraps a connected AF_VSOCK socket
```

### 6.4 Common vsock Pitfalls

| Pitfall | Explanation |
|---------|-------------|
| **CID 0 or 1** | Reserved by the protocol; using them silently fails or panics |
| **Race on boot** | The guest vsock server is not available until after `microdroid_manager` completes initialization; retry with backoff |
| **Port conflicts** | Ports below 1024 require `CAP_NET_BIND_SERVICE` in the guest |
| **SELinux** | Both the host service and guest service need vsock `{ bind connect }` permissions in their respective SELinux policies |

---

## 7. SELinux for AVF

### 7.1 Host Policy

Key types in `system/sepolicy/private/`:

| Type | Description |
|------|-------------|
| `virtualizationservice` | VirtualizationService process |
| `crosvm` | crosvm VMM process |
| `kvm_device` | `/dev/kvm` device node |

VirtualizationService and crosvm must have `{ read write ioctl }` to `kvm_device`.

### 7.2 Guest Policy

Microdroid ships its own SELinux policy inside `packages/modules/Virtualization/microdroid/`:

- Guest policy is separate from and independent of host policy.
- `microdroid_manager` starts in `microdroid_manager` domain and transitions the payload to `microdroid_app` domain.
- Never copy host `.te` rules directly into the guest policy — the type namespaces are independent.

---

## 8. Build Targets and Testing

### 8.1 Build

```bash
# Full AVF mainline module
m VirtualizationService microdroid crosvm

# Individual components
m VirtualizationService      # host AIDL server
m crosvm                     # Rust VMM
m microdroid_kernel          # guest kernel image
m microdroid_manager         # guest init agent
```

### 8.2 Test

```bash
# Integration tests (require a pKVM-capable device)
atest VirtualizationTestCases
atest MicrodroidTests
atest MicrodroidHostTestCases    # host-side test orchestration

# Unit tests (can run on host)
atest crosvm_tests
```

### 8.3 Debugging

```bash
# Check pKVM support
adb shell getprop ro.boot.hypervisor.protected_vm.supported

# List running VMs
adb shell vm list

# Attach console to running VM (CID from vm list)
adb shell vm console <cid>

# Filter AVF logs
adb logcat -s VirtualizationService crosvm microdroid_manager

# Dump KVM stats (host kernel)
adb shell cat /sys/kernel/debug/kvm/stat
```

---

*Reference document v1.0 (2026-03-15) — pKVM, crosvm, Microdroid, AVF, vsock IPC.*

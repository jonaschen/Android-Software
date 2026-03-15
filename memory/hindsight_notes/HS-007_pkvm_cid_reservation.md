# HS-007: vsock CID 0 and 1 Are Reserved — Never Hardcode Them

**Category:** Virtualization / pKVM
**Skills involved:** L2-virtualization-pkvm-expert
**Android versions:** Android 13+ (AVF)

## Insight

The AF_VSOCK address family reserves CIDs 0 and 1:
- CID 0: Hypervisor-reserved (do not use)
- CID 1: Loopback to the hypervisor (do not use)
- CID 2: `VMADDR_CID_HOST` — the host kernel/userspace
- CID 3: `VMADDR_CID_LOCAL` — loopback within the same context
- CID 4+: Dynamically assigned to VMs by `VirtualizationService`

**The silent failure mode:** Connecting to CID 0 or 1 either silently fails or returns `ENODEV` depending on kernel version. There is no runtime warning — the socket just never connects.

**Correct pattern:**
```java
// Host side: get CID from the VirtualMachine object
int guestCid = vm.getCid();
ParcelFileDescriptor fd = vm.connectToVsockServer(PORT);

// Guest side: bind to VMADDR_CID_ANY and accept
int sock = socket(AF_VSOCK, SOCK_STREAM, 0);
struct sockaddr_vm addr = { .svm_cid = VMADDR_CID_ANY, .svm_port = PORT };
bind(sock, &addr, sizeof(addr));
```

## Why This Matters

This trap is not caught by compile-time checks. CID hardcoding produces intermittent failures that are difficult to diagnose because they look like network timeouts.

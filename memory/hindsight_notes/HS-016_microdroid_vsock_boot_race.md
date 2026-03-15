# HS-016: Microdroid vsock Server Not Ready at VM Start — Must Retry

**Category:** Virtualization / pKVM
**Skills involved:** L2-virtualization-pkvm-expert
**Android versions:** Android 13+ (AVF)

## Insight

When a host app starts a Microdroid VM and immediately tries to connect via vsock, the connection will fail with `ECONNREFUSED` or `ETIMEDOUT`. The vsock server inside the guest is not available until `microdroid_manager` has completed initialization (typically 2–5 seconds after the VM starts, depending on device speed and APK size).

**Wrong pattern:**
```java
vm.run();
ParcelFileDescriptor fd = vm.connectToVsockServer(PORT); // fails immediately
```

**Correct pattern:**
```java
vm.run();
// Register VirtualMachineCallback.onPayloadReady()
// Only attempt vsock connection from within onPayloadReady()
```

The `onPayloadReady()` callback fires after `microdroid_manager` signals readiness via the hypervisor channel — this is the correct gate.

## Why This Matters

This race is never caught by unit tests (which mock the VM) and only manifests on real hardware. The fix is a one-line change but requires understanding the AVF boot lifecycle.

## Trigger

Every AVF integration that uses vsock should include the `onPayloadReady` gate as a code review checklist item.

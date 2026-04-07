---
id: HS-033
title: "GKI 6.12 kernel internals: EEVDF scheduler, per-VMA locks, proxy execution"
skill: L2-kernel-gki-expert
date: 2026-04-08
source: research-session
---

## Insight

The android16-6.12 kernel introduces major subsystem changes beyond the KMI
baseline shift documented in HS-023:

1. **EEVDF replaces CFS**: The Earliest Eligible Virtual Deadline First scheduler
   replaces the Completely Fair Scheduler. This changes scheduling latency
   characteristics and may affect real-time audio/media workloads.

2. **Per-VMA locks**: Addresses `mmap_lock` contention by using finer-grained
   locking at the VMA level. Reduces lock contention in multi-threaded workloads
   (important for camera/media pipelines).

3. **Proxy Execution**: New scheduling feature that borrows CPU cycles from
   high-priority processes to help lower-priority processes release held locks.
   Mitigates priority inversion without traditional PI mutexes.

4. **RCU_LAZY**: Reduces power consumption by deferring RCU callbacks. Relevant
   for battery-sensitive use cases.

5. **CONFIG_ZRAM_MULTI_COMP**: Improved memory compression with multiple
   compression algorithms for ZRAM. Benefits low-RAM devices.

6. **Memory allocation profiling** (`CONFIG_MEM_ALLOC_PROFILING`): Attributes
   each allocation to its source line. Enable via `sysctl.vm.mem_profiling`.

7. **Clang 19.0.1 stricter bounds checking**: The `__counted_by` attribute now
   enforces runtime bounds. Vendor modules using dynamically-sized arrays must
   set the size field immediately after allocation or risk kernel panics.
   `CONFIG_UBSAN_SIGNED_WRAP` disabled to prevent false positives.

8. **CONFIG_OF_DYNAMIC**: Now exposed by default, revealing driver bugs in device
   tree node reference counting (use-after-free, memory leaks). Vendor drivers
   must audit OF API usage patterns.

## Lesson

When migrating BSP kernel modules to android16-6.12:
- Audit scheduler-sensitive code (RT priorities, SCHED_FIFO) for EEVDF behavior.
- Audit `mmap_lock` usage in drivers for per-VMA lock compatibility.
- Audit all `__counted_by` annotated arrays — set size before any access.
- Audit all OF/device-tree API usage for proper `of_node_put()` calls.

## Cross-Skill Impact

- **L2-multimedia-audio-expert**: EEVDF may change audio thread scheduling latency.
- **L2-version-migration-expert**: Add EEVDF + Clang 19 to A15→A16 kernel checklist.
- **L2-hal-vendor-interface-expert**: Vendor .ko modules need Clang 19 bounds audit.
- **L2-virtualization-pkvm-expert**: pKVM EL2 code runs in kernel 6.12 context.

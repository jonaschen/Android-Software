# HS-017: Binder Thread Pool Exhaustion Causes ANR in System Server

**Category:** Framework Services
**Skills involved:** L2-framework-services-expert
**Android versions:** All

## Insight

Each process has a fixed-size Binder thread pool (default: 15 threads in `system_server`). If all threads are blocked waiting for remote calls, new incoming Binder calls queue up and eventually cause ANR.

**Signature in traces:**
```
"Binder:1234_N" tid=X BLOCKED
  waiting on <0x...> (a android.os.BinderProxy)
```

All N Binder threads blocked simultaneously = thread pool exhaustion.

**Root causes:**
1. Synchronous Binder call from a Binder thread back into another service that calls back (potential deadlock cycle).
2. A downstream service is slow/hung — backpressure propagates to `system_server`.
3. Thread pool size too small for the number of concurrent clients.

**Fixes:**
- Break synchronous chains: make downstream calls `oneway` where possible.
- Increase thread pool: `ProcessState::self()->setThreadPoolMaxThreadCount(N)` (use sparingly).
- Add timeouts to outbound Binder calls using `IBinder::pingBinder()` before making blocking calls.

## Why This Matters

Binder thread exhaustion is a top-3 cause of `system_server` ANR in production. It requires tracing the full call chain, not just the symptom.

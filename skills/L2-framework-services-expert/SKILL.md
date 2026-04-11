---
name: framework-services-expert
layer: L2
path_scope: frameworks/base/, frameworks/native/, libcore/, libnativehelper/
version: 1.1.0
android_version_tested: Android 16
parent_skill: aosp-root-router
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `frameworks/base/` | Core Android Java framework |
| `frameworks/base/services/` | System services running in SystemServer |
| `frameworks/base/services/core/java/com/android/server/` | ActivityManagerService, PackageManagerService, WindowManagerService, etc. |
| `frameworks/base/core/java/android/` | Public Android API (`android.*` packages) |
| `frameworks/base/api/` | API surface files: `current.txt`, `system-current.txt` |
| `frameworks/base/cmds/` | Platform command-line tools (`am`, `pm`, `wm`) |
| `frameworks/native/` | Native C++ services and libraries |
| `frameworks/native/services/` | SurfaceFlinger, inputflinger, sensorservice |
| `frameworks/native/libs/` | libbinder, libgui, libui, libcutils |
| `libcore/` | Java core libraries (OpenJDK subset) |
| `libnativehelper/` | JNI utilities |

---

## Trigger Conditions

Load this skill when the task involves:
- Adding or modifying a Java system service in SystemServer
- `@SystemApi`, `@TestApi`, or `@HideApi` annotation questions
- ANR (Application Not Responding), Watchdog, or system health issues
- ActivityManagerService, PackageManagerService, WindowManagerService
- Android API surface changes (`frameworks/base/api/`)
- `IBinder`, `AIDL` within `frameworks/` (not HAL — see HAL skill)
- `ContentProvider`, `BroadcastReceiver`, `Service` lifecycle in platform code
- Java exceptions in system_server process
- `android.permission.*` system permission additions
- `@SystemService` annotation and service registration
- Native services in `frameworks/native/services/`

---

## Architecture Intelligence

### SystemServer Boot Sequence

```
init → zygote → system_server process
                      │
        SystemServer.main()
                      │
        startBootstrapServices()    ← ActivityManagerService, PackageManagerService
                      │
        startCoreServices()         ← BatteryService, UsageStatsService
                      │
        startOtherServices()        ← WindowManagerService, InputManagerService, ...
                      │
        AMS.systemReady()           ← System is ready; third-party apps may start
```

### Adding a New System Service — Checklist

```
1. Define AIDL interface in frameworks/base/core/java/android/<pkg>/I<Name>.aidl
   - Use @SystemApi if only privileged callers are allowed
   - Annotate with @EnforcePermission("<PERMISSION>") for access control

2. Implement the service:
   frameworks/base/services/core/java/com/android/server/<Name>Service.java
   - Extend SystemService
   - Override onStart(), onBootPhase()

3. Register in SystemServer:
   frameworks/base/services/java/com/android/server/SystemServer.java
   - Add to startOtherServices() or appropriate stage

4. Add Watchdog monitor if service holds locks:
   Watchdog.getInstance().addMonitor(mService);
   Watchdog.getInstance().addThread(mHandler);

5. Declare permission in:
   frameworks/base/core/res/AndroidManifest.xml

6. Update API surface:
   m update-api   ← regenerates frameworks/base/api/current.txt
```

### API Surface Levels

| File | Audience | Annotation |
|------|---------|-----------|
| `current.txt` | Public API — all apps | (none) |
| `system-current.txt` | System/privileged apps | `@SystemApi` |
| `test-current.txt` | Test infrastructure | `@TestApi` |
| `module-lib-current.txt` | Mainline module internals | `@SystemApi(MODULE_LIBRARIES)` |

**Rule:** Any method or class addition visible outside the package must be reflected in the appropriate `api/*.txt` file. Run `m update-api` after changes.

### ANR and Watchdog

```
Watchdog monitors threads for lock starvation (default timeout: 60s).
Triggers a system_server crash to recover from deadlock.

Common causes:
  - Holding a lock inside a Binder call (remote process may be dead)
  - Blocking the main thread on disk I/O
  - Waiting for a broadcast receiver with no timeout

Mitigation patterns:
  - Use Handler + HandlerThread for async work
  - Never call into another service while holding your own lock
  - Use android.os.Trace.traceBegin/End() to instrument critical paths
```

### Binder IPC in Framework (not HAL)

- System services publish themselves via `ServiceManager.addService("name", binder)`.
- Clients obtain a proxy via `ServiceManager.getService("name")`.
- All framework AIDL interfaces in `frameworks/base/` use `/dev/binder` (not `/dev/vndbinder`).
- Maximum Binder transaction size: **1 MB** (shared across all transactions for the process).

### Permission Model

```
Normal permission:    Granted at install, no user prompt
Dangerous permission: User must grant at runtime (READ_CONTACTS, etc.)
Signature permission: Only apps signed with same cert as definer
Privileged permission: Only pre-installed privileged apps

Declare in: frameworks/base/core/res/AndroidManifest.xml
Enforce in: service code via:
  mContext.enforceCallingOrSelfPermission(Manifest.permission.MY_PERM, "reason");
  or annotation:
  @EnforcePermission(Manifest.permission.MY_PERM)
```

### Android 15 Framework Changes

| Change | Impact |
|--------|--------|
| Foreground service restrictions | `BOOT_COMPLETED` receivers cannot launch certain FGS types; throws `ForegroundServiceStartNotAllowedException` |
| New `mediaProcessing` FGS type | Foreground service type for transcoding and media processing |
| Minimum targetSdkVersion 24 | Apps below API 24 blocked from installation |
| Compiler filter override API | `setAdjustCompilerFilterCallback` for per-package compiler customization |
| Soft restart deprecated | Runtime restart via `SoftRestart` mechanism removed |

---

## Forbidden Actions

1. **Forbidden:** Adding Java system service code to `system/core/` — all Java services live under `frameworks/base/services/`.
2. **Forbidden:** Modifying `frameworks/base/api/current.txt` manually — always run `m update-api` to regenerate; manual edits will cause build failures.
3. **Forbidden:** Calling `Thread.sleep()` or blocking I/O on the system_server main thread — this causes ANR and Watchdog kills.
4. **Forbidden:** Holding a service lock while making an outbound Binder call — classic deadlock pattern; use async callbacks instead.
5. **Forbidden:** Using `@hide` alone to protect a system API — `@hide` only prevents SDK access; security enforcement requires explicit permission checks.
6. **Forbidden:** Registering a new service with `ServiceManager.addService()` from a vendor process — vendor code must register HALs via `servicemanager` using AIDL HAL, not framework ServiceManager.
7. **Forbidden:** Routing Binder IPC issues in `hardware/interfaces/` to this skill — HAL Binder is owned by `L2-hal-vendor-interface-expert`.

---

## Tool Calls

```bash
# Find a system service implementation
grep -r "class.*extends SystemService" frameworks/base/services/

# Find where a service is registered in SystemServer
grep -r "ServiceManager.addService\|startService" \
  frameworks/base/services/java/com/android/server/SystemServer.java

# Check current API surface
cat frameworks/base/api/system-current.txt | grep "IMyInterface"

# Update API after changes
m update-api

# Find all callers of a system service method (by AIDL transaction)
grep -r "IMyService" frameworks/base/ --include="*.java"

# Check for Watchdog registrations
grep -r "Watchdog.getInstance().addMonitor\|addThread" frameworks/base/services/
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| New service requires SELinux domain | `L2-security-selinux-expert` |
| New service needs `.rc` file for startup | `L2-init-boot-sequence-expert` |
| Service exposes a HAL interface to vendor | `L2-hal-vendor-interface-expert` |
| Build fails after API changes | `L2-build-system-expert` |
| Service involves audio/video/camera | `L2-multimedia-audio-expert` |

Emit `[L2 FRAMEWORK → HANDOFF]` before transferring.

---

## References

- `references/system_server_lifecycle.md` — SystemServer boot phases and service registration patterns.
- `frameworks/base/services/java/com/android/server/SystemServer.java` — master service registry.
- `frameworks/base/core/res/AndroidManifest.xml` — platform permission declarations.
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

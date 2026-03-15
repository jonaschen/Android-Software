# SystemServer Lifecycle and Service Registration

> Android 14 — `frameworks/base/services/`

## Boot Phases

SystemServer uses `SystemService.PHASE_*` constants to sequence service startup. Services declare dependencies by overriding `onBootPhase()`.

| Phase Constant | Value | When | What's Available |
|---------------|-------|------|-----------------|
| `PHASE_WAIT_FOR_DEFAULT_DISPLAY` | 100 | Before display ready | Almost nothing |
| `PHASE_LOCK_SETTINGS_READY` | 480 | Lock settings loaded | Settings storage |
| `PHASE_SYSTEM_SERVICES_READY` | 500 | Core services up | AMS, WMS, PMS |
| `PHASE_DEVICE_SPECIFIC_SERVICES_READY` | 520 | Device services up | HAL-backed services |
| `PHASE_ACTIVITY_MANAGER_READY` | 550 | AMS ready | Can start activities |
| `PHASE_THIRD_PARTY_APPS_CAN_START` | 600 | Full boot | All services ready |

## Service Registration Pattern

```java
// Step 1: Implement the service
public class MyService extends SystemService {
    private final MyServiceImpl mImpl;

    public MyService(Context context) {
        super(context);
        mImpl = new MyServiceImpl(context);
    }

    @Override
    public void onStart() {
        // Register Binder interface
        publishBinderService(Context.MY_SERVICE, mImpl);
        // Or for LocalService (same process):
        publishLocalService(MyServiceInternal.class, mImpl.getLocalService());
    }

    @Override
    public void onBootPhase(int phase) {
        if (phase == PHASE_SYSTEM_SERVICES_READY) {
            // Safe to call other system services now
            mImpl.onSystemServicesReady();
        }
        if (phase == PHASE_THIRD_PARTY_APPS_CAN_START) {
            // System fully booted
            mImpl.onBootComplete();
        }
    }
}
```

## SystemServer.java — Service Start Sequence

```java
// frameworks/base/services/java/com/android/server/SystemServer.java

private void startBootstrapServices(@NonNull TimingsTraceAndSlog t) {
    // Must start first — many services depend on these
    mActivityManagerService = ActivityManagerService.Lifecycle.startService(...);
    mPackageManagerService = PackageManagerService.main(...);
    mDisplayManagerService = mSystemServiceManager.startService(DisplayManagerService.class);
    // ...
}

private void startCoreServices(@NonNull TimingsTraceAndSlog t) {
    mSystemServiceManager.startService(BatteryService.class);
    mSystemServiceManager.startService(UsageStatsService.class);
    // ...
}

private void startOtherServices(@NonNull TimingsTraceAndSlog t) {
    // Most services registered here
    mSystemServiceManager.startService(WindowManagerService.Lifecycle.class);
    mSystemServiceManager.startService(InputManagerService.class);
    // ... hundreds more ...

    // Boot complete signal
    mActivityManagerService.systemReady(() -> {
        mSystemServiceManager.startBootPhase(
            t, SystemService.PHASE_ACTIVITY_MANAGER_READY);
        // ...
    }, t);
}
```

## Watchdog Integration

```java
// Register a thread with Watchdog (in onStart())
// If the thread doesn't respond within 60s → system_server is killed and restarted

private final HandlerThread mHandlerThread =
    new HandlerThread("MyServiceHandler", THREAD_PRIORITY_BACKGROUND);

@Override
public void onStart() {
    mHandlerThread.start();
    mHandler = new Handler(mHandlerThread.getLooper());

    Watchdog.getInstance().addThread(mHandler, "MyServiceHandler");
    // Optional: implement Watchdog.Monitor for finer-grained monitoring
    Watchdog.getInstance().addMonitor(this);  // if implements Monitor

    publishBinderService(Context.MY_SERVICE, mImpl);
}

// Implement Monitor interface to report health
@Override
public void monitor() {
    // This is called from the Watchdog thread.
    // Acquire and immediately release your main lock to prove no deadlock.
    synchronized (mLock) { }
}
```

## Binder Interface Best Practices

```java
// AIDL interface in frameworks/base/core/java/android/myservice/IMyService.aidl
interface IMyService {
    @EnforcePermission("android.permission.MY_PERMISSION")
    void doProtectedOperation(in Bundle data);

    @JavaPassthrough(annotation="@android.annotation.RequiresPermission(android.Manifest.permission.MY_PERMISSION)")
    void doSomethingElse();
}

// Implementation — permission is auto-enforced by @EnforcePermission
public class MyServiceImpl extends IMyService.Stub {
    @Override
    public void doProtectedOperation(Bundle data) {
        // Called only if caller has MY_PERMISSION (enforced by generated code)
        // Never call enforceCallingPermission() manually when using @EnforcePermission
    }
}
```

## Common ANR Patterns and Fixes

| Pattern | Symptom | Fix |
|---------|---------|-----|
| Blocking Binder call while holding lock | ANR → Watchdog kill | Use async Binder, release lock before calling |
| Disk I/O on main thread | StrictMode violation + ANR | Use background HandlerThread |
| Broadcast timeout | `BroadcastReceiver ANR` in log | Return quickly from `onReceive()`; use `goAsync()` for slow work |
| Lock acquisition failure | Watchdog sees thread stuck | Add timeout to lock acquisition; audit lock hierarchy |
| `ContentProvider` query on UI thread | ANR | Move to background thread |

## API Surface Management

```bash
# After adding a @SystemApi method:
m update-api

# This updates:
#   frameworks/base/api/current.txt          (if @PublicApi)
#   frameworks/base/api/system-current.txt   (if @SystemApi)
#   frameworks/base/api/test-current.txt     (if @TestApi)

# Presubmit check (run before committing):
m api-stubs-docs-non-updatable-api-incompatibilities-known-differences
```

## Permission Declaration (AndroidManifest.xml)

```xml
<!-- frameworks/base/core/res/AndroidManifest.xml -->
<permission
    android:name="android.permission.MY_NEW_PERMISSION"
    android:protectionLevel="signature|privileged"
    android:label="@string/permlab_myPermission"
    android:description="@string/permdesc_myPermission" />
```

Protection levels:
- `normal` — auto-granted, low risk
- `dangerous` — user runtime grant required
- `signature` — only apps signed with same cert
- `privileged` — only pre-installed privileged apps
- `signature|privileged` — either of the above

# HS-018: HAL Servers Must Use class hal in .rc Files

**Category:** HAL / Init
**Skills involved:** L2-hal-vendor-interface-expert, L2-init-boot-sequence-expert
**Android versions:** Android 8+ (Treble)

## Insight

HAL server daemons must use `class hal` in their `.rc` service definition, not `class main` or `class core`. The `hal` class was introduced with Treble to:

1. Allow the system to restart HAL servers independently of main services.
2. Enable hardware-specific HAL restart without triggering a full `class main` restart.
3. Signal to `vintf` that this service implements a HAL interface.

**Wrong:**
```rc
service android.hardware.foo@1.0-service /vendor/bin/hw/android.hardware.foo@1.0-service
    class main          # WRONG — use 'hal'
    user system
    group system
```

**Correct:**
```rc
service android.hardware.foo@1.0-service /vendor/bin/hw/android.hardware.foo@1.0-service
    class hal
    user system
    group system
    interface android.hardware.foo@1.0::IFoo default
```

The `interface` declaration is also required — it registers the HAL with `hwservicemanager`.

## Why This Matters

A HAL using `class main` gets restarted whenever the system restarts `main` services (e.g., after user unlock). This causes HAL clients to get `DEAD_OBJECT` exceptions unexpectedly.

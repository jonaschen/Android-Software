---
name: init-boot-sequence-expert
layer: L2
path_scope: system/core/init/, system/core/, bootable/, *.rc
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `system/core/init/` | `init` process source code, `.rc` parser, service manager |
| `system/core/` | Core OS utilities: `adb`, `logd`, `ueventd`, `fastboot` |
| `system/core/rootdir/` | Root filesystem `.rc` files: `init.rc`, `ueventd.rc` |
| `bootable/recovery/` | Recovery mode image |
| `bootable/bootloader/` | Bootloader support code |
| `vendor/<OEM>/etc/init/` | Vendor daemon `.rc` files |
| `device/<OEM>/<product>/` | Device-specific `.rc` overlays and board init |
| `*.rc` (any path) | init service/action definitions |

---

## Trigger Conditions

Load this skill when the task involves:
- A daemon failing to start (check `adb logcat -b main -s init`)
- Writing or debugging `.rc` files
- `init.rc` triggers, actions, or service definitions
- `property_service` — setting or reading properties at boot
- `ueventd` — device node creation, permissions
- Socket creation for system services
- Boot phase ordering (`on early-init`, `on init`, `on post-fs-data`, `on boot`)
- SELinux context labeling for executables and sockets (coordinate with security skill)
- Recovery mode modifications
- `oneshot` vs persistent service behavior
- `setprop`, `getprop` in init context

---

## Architecture Intelligence

### Android Boot Sequence

```
Power On
  │
  ▼
Bootloader (fastboot / ABL)
  │  loads boot.img
  ▼
Kernel
  │  mounts rootfs, starts PID 1
  ▼
/init  (system/core/init/)
  │
  ├── early-init phase       ← ueventd, selinux setup, /dev mount
  │
  ├── init phase             ← Mount /proc, /sys, set properties
  │
  ├── charger (if needed)    ← Battery charging UI
  │
  ├── post-fs phase          ← /system mounted (read-only)
  │
  ├── post-fs-data phase     ← /data mounted (read-write), vold
  │
  ├── zygote-start           ← Start zygote (Java runtime)
  │
  └── boot phase             ← All core services up; network, BT, etc.
```

### .rc File Syntax Reference

```ini
# Service definition
service <name> <executable> [<args>]
    class <class_name>         # main | core | late_start | default
    user <username>            # e.g., system, root, nobody
    group <groups>             # e.g., system inet
    capabilities <caps>        # Linux capabilities (e.g., NET_ADMIN)
    seclabel u:r:<domain>:s0   # SELinux domain (must match file_contexts)
    socket <name> <type> <perm> [<user> [<group>]]
    onrestart restart <other_service>
    disabled                   # Don't start automatically
    oneshot                    # Don't restart on exit
    critical                   # Reboot if it exits too many times

# Action / trigger
on <trigger>
    <command>
    <command>

# Common triggers (in order)
on early-init
on init
on post-fs
on post-fs-data
on zygote-started
on boot
on property:<prop>=<value>     # React to property change
```

### Common init Commands

| Command | Effect |
|---------|--------|
| `start <service>` | Start a service |
| `stop <service>` | Stop a service |
| `restart <service>` | Stop then start |
| `setprop <key> <value>` | Set a system property |
| `mkdir <path> <mode> <user> <group>` | Create directory with permissions |
| `chown <user> <group> <path>` | Change ownership |
| `chmod <mode> <path>` | Change permissions |
| `symlink <target> <link>` | Create symlink |
| `mount <type> <src> <dst> <options>` | Mount a filesystem |
| `write <file> <value>` | Write value to file (sysfs, etc.) |
| `exec <seclabel> <user> <group> -- <cmd>` | Run a one-shot command |

### Property Service

```
Properties are key-value pairs read/written via:
  getprop <key>          (shell)
  setprop <key> <value>  (shell — respects property_contexts)

Namespaces:
  ro.*          Read-only, set once at boot
  persist.*     Survives reboot (stored in /data/property/)
  ctl.*         Control commands (ctl.start, ctl.stop)
  vendor.*      Vendor-owned properties

Setting a property from .rc:
  setprop ro.myproduct.version 1.0

Reacting to a property:
  on property:sys.boot_completed=1
      start my_post_boot_daemon
```

### Socket Types

| Type | Use Case |
|------|---------|
| `stream` | TCP-like, connection-oriented (most services) |
| `dgram` | UDP-like, connectionless |
| `seqpacket` | Stream with message boundaries |

Socket is created by init at `/dev/socket/<name>`, owned by specified user/group.

### .rc File Placement Rules

| Partition | .rc Location | Load Order |
|-----------|-------------|-----------|
| System | `system/core/rootdir/init.rc` | First |
| System services | `system/etc/init/*.rc` | After system init.rc |
| Vendor | `vendor/etc/init/*.rc` | After system |
| ODM | `odm/etc/init/*.rc` | After vendor |
| Product | `product/etc/init/*.rc` | After ODM |

**Rule:** Never edit `init.rc` directly for vendor/OEM daemons. Place `.rc` files in `vendor/etc/init/` and they are automatically imported.

### Android 15 Init / Boot Changes

| Change | Impact |
|--------|--------|
| Virtual A/B v3 | Faster, smaller OTA updates; new update mechanism affects boot slot selection flow |
| 16KB page size boot support | Bootloader must determine page size from kernel header; dual OTA images (4K + 16K) |
| Soft restart deprecated | `SoftRestart` mechanism removed; full reboots required for scenarios that previously used soft restart |

---

## Forbidden Actions

1. **Forbidden:** Editing `system/core/rootdir/init.rc` for vendor or OEM daemon definitions — use `vendor/etc/init/<daemon>.rc` instead.
2. **Forbidden:** Running a daemon as `user root` without explicit security justification — prefer a dedicated system user with minimum capabilities.
3. **Forbidden:** Using `seclabel u:r:init:s0` for a new daemon — each daemon must have its own dedicated SELinux domain defined in the sepolicy.
4. **Forbidden:** Setting `persist.*` properties from a `.rc` file triggered before `/data` is mounted — `/data` is not available until `post-fs-data`.
5. **Forbidden:** Using `disabled` and then manually calling `start` without understanding class ordering — service class ordering controls startup dependency; verify class before disabling.
6. **Forbidden:** Setting `critical` on a service that may legitimately exit on low-battery or thermal events — `critical` will trigger a reboot loop.
7. **Forbidden:** Routing init boot failures caused by SELinux `avc: denied` to this skill — those always go to `L2-security-selinux-expert` first.

---

## Tool Calls

```bash
# Watch init log during boot (via adb)
adb logcat -b main -s init

# Check if a service is running
adb shell getprop init.svc.<service_name>

# List all init services and their state
adb shell service list | head -30

# Check property values
adb shell getprop | grep <keyword>

# Validate .rc syntax (manual check — no automated linter yet)
# Read the file and cross-reference with init parser:
cat system/core/init/readme.txt

# Find all .rc files defining a specific service
grep -r "service <name>" system/ vendor/ device/ --include="*.rc"
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| SELinux `avc: denied` for daemon executable or socket | `L2-security-selinux-expert` |
| New daemon is a HAL service needing AIDL/HIDL registration | `L2-hal-vendor-interface-expert` |
| Daemon is a Java process (SystemServer component) | `L2-framework-services-expert` |
| Boot failure caused by a build issue (missing binary) | `L2-build-system-expert` |
| Kernel module not loading at early-init | `L2-kernel-gki-expert` |

Emit `[L2 INIT → HANDOFF]` before transferring.

---

## References

- `references/init_rc_reference.md` — complete `.rc` syntax, trigger order, and command reference.
- `system/core/init/README.md` — official init documentation.
- `system/core/rootdir/init.rc` — platform root init file (reference only; do not modify for vendor use).
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

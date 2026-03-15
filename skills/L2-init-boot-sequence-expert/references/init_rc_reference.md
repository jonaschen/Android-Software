# Android init .rc File Reference

> Android 14 — `system/core/init/`

## .rc File Import and Load Order

init automatically imports `.rc` files from these directories (in order):

```
/system/etc/init/           ← Platform init scripts
/system_ext/etc/init/       ← System extension
/vendor/etc/init/           ← Vendor/OEM daemons   ← Put vendor daemons here
/odm/etc/init/              ← ODM layer
/product/etc/init/          ← Product-specific
```

Files within each directory are loaded in lexicographic order. Prefix with a number to control order: `10_early.rc`, `50_myservice.rc`.

## Full Service Syntax

```ini
service <name> <executable_path> [<arg1> <arg2> ...]
    # --- Identity ---
    user <username>              # Run as this user (default: root — avoid)
    group <group> [<group2>...]  # Supplementary groups
    capabilities <cap_list>      # Linux capabilities (e.g., NET_ADMIN SETUID)
    rlimit <resource> <cur> <max> # Resource limits (e.g., rlimit nofile 1024 1024)

    # --- SELinux ---
    seclabel u:r:<domain>:s0     # Explicit SELinux domain (required for Treble)

    # --- Lifecycle ---
    class <class_name>           # Service class: main | core | late_start | default
    disabled                     # Don't start automatically with class
    oneshot                      # Don't restart after exit
    critical                     # If exits >4 times in 4 min → reboot device
    shutdown critical            # Kill last on shutdown
    priority <-20..19>           # Nice priority
    oom_score_adjust <-1000..1000>

    # --- Restart ---
    restart_period <seconds>     # Minimum time between restarts (default: 5)
    timeout_period <seconds>     # Kill if not started within this time

    # --- IPC ---
    socket <name> <type> <perm> [<user> [<group> [<seclabel>]]]
    # type: stream | dgram | seqpacket
    # Creates /dev/socket/<name>

    # --- Filesystem ---
    writepid /dev/cpuset/...     # Write PID to file on start
    enter_namespace <type> <path> # Enter a Linux namespace

    # --- Triggers ---
    onrestart restart <other_service>
    onrestart setprop <key> <value>
```

## Full Action Syntax

```ini
on <trigger>
    <command>
    <command>

# Trigger forms:
on early-init           # Very early, before /dev populated
on init                 # Basic init, /dev and /proc mounted
on late-init            # After early services, before mounting /data
on fs                   # Filesystems being mounted
on post-fs              # /system mounted (read-only)
on late-fs              # Late filesystem events
on post-fs-data         # /data mounted (read-write)  ← persist.* safe here
on zygote-started       # Zygote process has started
on boot                 # Core services up
on property:<k>=<v>     # When property k becomes value v
on property:<k>=*       # When property k changes to any value
```

## Available init Commands

```ini
# Process management
start <service>
stop <service>
restart <service>
class_start <class>
class_stop <class>
class_restart <class>

# Filesystem
mkdir <path> [<mode> [<owner> [<group>]]]
chmod <mode> <path>
chown <owner> <group> <path>
symlink <target> <name>
copy <src> <dst>
write <path> <content>
rm <path>
rmdir <path>
mount <type> <device> <path> [<options>]
mount_all <fstab_file> [--early|--late]

# Properties
setprop <name> <value>
getprop <name>           # Only valid in exec context

# Logging
loglevel <level>         # 0=KERN_EMERG ... 7=KERN_DEBUG

# Conditional execution
exec [<seclabel> [<user> [<group>...]]] -- <command> [<args>]
exec_start <service>
```

## Service Classes

| Class | Started by | Typical members |
|-------|-----------|----------------|
| `core` | `class_start core` (very early) | `logd`, `vold`, `ueventd` |
| `main` | `class_start main` | Most system services |
| `late_start` | After boot complete | Non-critical services |
| `default` | Explicit `start` only | On-demand services |

## Property Namespace Conventions

| Prefix | Usage |
|--------|-------|
| `ro.*` | Read-only, set once at boot |
| `persist.*` | Survives reboot (stored in `/data/property/`) |
| `ctl.*` | Control commands (`ctl.start.<name>`, `ctl.stop.<name>`) |
| `sys.*` | System state (e.g., `sys.boot_completed`) |
| `vendor.*` | Vendor-owned, all vendor properties should use this |
| `debug.*` | Debug-only, should not be set in production |

## Socket Reference

```ini
# Most common pattern — stream socket
service my_daemon /vendor/bin/my_daemon
    socket my_daemon stream 0660 system system u:object_r:my_daemon_socket:s0
    user system
    group system
    seclabel u:r:my_daemon:s0
```

Socket appears at `/dev/socket/my_daemon`. Client connects via:
```cpp
int fd = socket_local_client("my_daemon", ANDROID_SOCKET_NAMESPACE_RESERVED, SOCK_STREAM);
```

## Minimal Vendor Daemon Template

```ini
# vendor/etc/init/my_daemon.rc

service my_daemon /vendor/bin/my_daemon
    class main
    user my_daemon_user
    group my_daemon_group
    capabilities NET_ADMIN
    seclabel u:r:my_daemon:s0
    socket my_daemon stream 0660 system my_daemon_group
    oneshot

on property:sys.boot_completed=1
    start my_daemon
```

## Debugging init

```bash
# Watch init logs (includes service start/stop and property changes)
adb logcat -b main -s init

# Check service status
adb shell getprop init.svc.my_daemon
# Returns: running | stopped | restarting | crashed

# Force start a service (as root)
adb shell start my_daemon

# Check all socket files
adb shell ls -la /dev/socket/

# Trace property changes
adb shell setprop log.tag.PropertyService V
adb logcat -s PropertyService
```

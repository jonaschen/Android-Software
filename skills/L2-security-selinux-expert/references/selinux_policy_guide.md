# Android SELinux Policy Authoring Guide

> Android 14 — `system/sepolicy/`

## Policy File Types

| File | Purpose | Location |
|------|---------|---------|
| `<domain>.te` | Type Enforcement rules — allow/deny | `system/sepolicy/private/` or `vendor/sepolicy/` |
| `file_contexts` | Labels for filesystem paths | `system/sepolicy/private/` |
| `property_contexts` | Labels for system properties | `system/sepolicy/private/` |
| `service_contexts` | Labels for Binder services | `system/sepolicy/private/` |
| `hwservice_contexts` | Labels for HIDL services | `system/sepolicy/private/` |
| `mac_permissions.xml` | Maps APK signing cert to seinfo | `system/sepolicy/private/` |

## Type Declaration

```te
# Declare a new type for a daemon executable
type my_daemon, domain;
type my_daemon_exec, exec_type, file_type, vendor_file_type;

# Declare a data directory type
type my_daemon_data_file, file_type, data_file_type;
```

## Domain Transition

```te
# Auto-transition: when init executes my_daemon_exec, enter my_daemon domain
init_daemon_domain(my_daemon)

# For vendor daemons:
vendor_init_daemon_domain(my_daemon)
```

## Allow Rule Syntax

```te
# allow <source_domain> <target_type>:<object_class> { <permissions> };

# Allow my_daemon to read its config file
allow my_daemon my_daemon_data_file:file { open read getattr };

# Allow my_daemon to create its socket in /dev/socket/
allow my_daemon my_daemon_socket:sock_file { create unlink };

# Allow my_daemon to use its socket
allow my_daemon my_daemon_socket:unix_stream_socket { listen accept };
```

## Common Object Classes and Permissions

| Class | Common Permissions |
|-------|-------------------|
| `file` | `open read write create unlink rename getattr setattr` |
| `dir` | `open read write add_name remove_name search getattr` |
| `sock_file` | `open read write create unlink` |
| `unix_stream_socket` | `create listen accept connect read write` |
| `binder` | `call transfer` |
| `property_service` | `set` |
| `service_manager` | `add find list` |
| `process` | `fork execve signal ptrace` |

## Macros (Common Patterns)

```te
# Full file read (open + read + getattr)
r_file_perms            → { open read getattr }
# Full file read/write
rw_file_perms           → { open read write getattr setattr }
# Execute a binary
execute_no_trans(my_daemon, shell_exec)     # Execute without domain transition
domain_auto_trans(init, my_daemon_exec, my_daemon)  # Explicit transition

# Net access
internet               → { tcp_socket udp_socket netlink_route_socket ... }
net_domain(my_daemon)  # Grant full network access (use sparingly)

# Allow to use binder
binder_use(my_daemon)
binder_call(my_daemon, system_server)
binder_service(my_daemon)        # Allow service registration
```

## file_contexts Syntax

```
# <path_regex>    <label>
/vendor/bin/my_daemon               u:object_r:my_daemon_exec:s0
/data/vendor/my_daemon(/.*)?        u:object_r:my_daemon_data_file:s0
/dev/socket/my_daemon               u:object_r:my_daemon_socket:s0
/dev/my_hw_device                   u:object_r:my_hw_dev:s0
```

Apply labels after adding file_contexts:
```bash
# On device (development only):
adb shell restorecon -R /vendor/bin/my_daemon
adb shell restorecon /data/vendor/my_daemon
```

## property_contexts Syntax

```
# <property_prefix>    u:object_r:<type>:s0
vendor.my_daemon.       u:object_r:vendor_my_daemon_prop:s0
ro.my_daemon.version    u:object_r:vendor_my_daemon_prop:s0
```

Allow rule for property access:
```te
# Allow my_daemon to set vendor.my_daemon.* properties
set_prop(my_daemon, vendor_my_daemon_prop)

# Allow my_daemon to read a property
get_prop(my_daemon, vendor_my_daemon_prop)
```

## service_contexts (AIDL services)

```
# <service_name>    u:object_r:<type>:s0
my_daemon_service   u:object_r:my_daemon_service:s0
```

Allow rule:
```te
type my_daemon_service, service_manager_type;
allow my_daemon my_daemon_service:service_manager { add find };
allow system_server my_daemon_service:service_manager { find };
```

## Neverallow — Key Platform Rules

```te
# These MUST NOT be violated:

# Vendor code cannot call framework's non-public services
neverallow vendor_domain { system_server_service -vendor_accessible_services }:service_manager find;

# No domain except init can write to /system
neverallow { domain -init -kernel } system_file:dir write;

# Untrusted apps cannot use binder to system services directly (must go through APIs)
neverallow untrusted_app system_server:binder call;
```

## Build and Test

```bash
# Build sepolicy only
m sepolicy

# Run SELinux unit tests
m sepolicy_tests

# Check for neverallow violations
m checkpolicy

# Run CTS SELinux tests (on device)
atest CtsSecurityHostTestCases#android.security.cts.SELinuxHostTest
```

## Treble Policy Split Rules

| Type | Where to Define | Who Can Use |
|------|----------------|-------------|
| Platform types | `system/sepolicy/public/` | Platform AND vendor |
| Platform-internal types | `system/sepolicy/private/` | Platform only |
| Vendor types | `vendor/<OEM>/sepolicy/` | Vendor only |

**Key rule:** If a vendor `.te` file needs to `allow` against a platform type, that type must be in `public/`. If it's only in `private/`, the build will fail with a Treble policy violation.

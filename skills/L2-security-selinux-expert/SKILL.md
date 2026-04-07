---
name: security-selinux-expert
layer: L2
path_scope: system/sepolicy/, vendor/*/sepolicy/, device/*/sepolicy/, *.te, file_contexts, property_contexts, service_contexts
version: 1.0.0
android_version_tested: Android 15
parent_skill: aosp-root-router
---

## Path Scope

| Path | Responsibility |
|------|---------------|
| `system/sepolicy/` | Platform SELinux policy — canonical source of truth |
| `system/sepolicy/public/` | Policy exported to vendor (stable API) |
| `system/sepolicy/private/` | Internal platform policy, not visible to vendor |
| `system/sepolicy/vendor/` | Policy for generic vendor domains |
| `system/sepolicy/prebuilts/` | Versioned policy snapshots for Treble compatibility |
| `vendor/<OEM>/sepolicy/` | OEM-specific policy extensions |
| `device/<OEM>/<product>/sepolicy/` | Device-specific policy |
| `*.te` (any path) | Type Enforcement rules |
| `file_contexts` | File label assignments |
| `property_contexts` | System property label assignments |
| `service_contexts` | Binder service label assignments |
| `hwservice_contexts` | HIDL service label assignments |

---

## Trigger Conditions

Load this skill when the task involves:
- Any `avc: denied` log line — **always routed here exclusively**
- Adding a new vendor daemon or system service requiring SELinux domain
- Writing or modifying `.te` files
- `audit2allow` output interpretation
- `neverallow` rule violations in build
- CTS SELinux tests failing
- File labeling: `restorecon`, `chcon`, `file_contexts`
- Property access denials (`property_contexts`)
- Binder/HIDL service registration failures (`service_contexts`, `hwservice_contexts`)
- Security audit or policy review

---

## Architecture Intelligence

### SELinux Policy Layers (Android)

```
Compile-time merge:
  system/sepolicy/public/      ← Stable; exported to vendor
  system/sepolicy/private/     ← Internal; NOT exported
  system/sepolicy/vendor/      ← Generic vendor types
  vendor/*/sepolicy/           ← OEM additions
  device/*/sepolicy/           ← Device-specific additions
         │
         ▼
  Compiled into: system/sepolicy.cil  +  vendor/sepolicy.cil
```

### avc: denied Anatomy

```
avc: denied { <permission> } for pid=<N> comm="<process>"
  path="<file>" dev="<device>" ino=<N>
  scontext=u:r:<source_domain>:s0
  tcontext=u:object_r:<target_type>:s0
  tclass=<object_class>

Key fields:
  permission    → what was attempted (read, write, open, ioctl, …)
  source_domain → the process's SELinux type (the subject)
  target_type   → the object's SELinux type (the resource)
  tclass        → the object class (file, dir, property_file, binder, …)
```

### Resolution Workflow

```
1. Capture full avc: denied log
2. Identify source_domain → is it a platform or vendor domain?
3. Check if a broader allow rule already exists (policy may just be missing on device)
4. Draft minimum allow rule:
     allow <source_domain> <target_type>:<tclass> { <permission> };
5. Check against neverallow rules:
     grep -r "neverallow.*<source_domain>" system/sepolicy/
6. Place rule in correct file:
     - Platform domain → system/sepolicy/private/<domain>.te
     - Vendor domain   → vendor/<OEM>/sepolicy/<domain>.te
7. Label any new files in file_contexts
8. Build and verify: atest CtsSecurityHostTestCases
```

### Neverallow Rules — Critical Boundaries

| Rule | Meaning |
|------|---------|
| `neverallow * system_data_file:file write` | No domain may write to `/data/system/` directly |
| `neverallow { domain -init } init:process *` | Only init may control the init domain |
| `neverallow vendor_domain platform_app:binder call` | Vendor domains cannot call platform app binder |
| `neverallow * untrusted_app:binder call` | No domain may call an untrusted app over binder |

### Treble Policy Split

- **Public policy** (`system/sepolicy/public/`) is versioned. Vendor policy extends it but cannot modify it.
- When adding a new type that vendor modules must reference, it **must** go in `public/`, not `private/`.
- `vendor_domain` attribute marks a type as vendor-owned — it cannot call non-VNDK system services directly.

### File Contexts Syntax

```
# Pattern                           Label
/vendor/bin/my_daemon               u:object_r:my_daemon_exec:s0
/data/vendor/myapp(/.*)?            u:object_r:myapp_data_file:s0
/dev/my_device                      u:object_r:my_device_dev:s0
```

### Property Contexts Syntax

```
# Prefix                            Label
vendor.myapp.                       u:object_r:vendor_myapp_prop:s0
ro.myapp.version                    u:object_r:vendor_myapp_prop:s0
```

### Android 15 SELinux / Security Changes

| Change | Impact |
|--------|--------|
| Signature permission allowlist | Platform enforces explicit allowlist for signature perms requested by non-system apps; new apps requesting signature perms must be listed |
| Private space isolation | New SELinux domain boundaries for the Private Space feature (secure area hiding sensitive apps) |
| FBE `dusize_4k` flag | New file-based encryption config option forcing 4096-byte data units |
| Mobile network transparency | New privacy settings notify users of unencrypted connections and IMSI/IMEI exposure |

---

## Forbidden Actions

1. **Forbidden:** Using `audit2allow` output verbatim without reviewing each rule — `audit2allow` generates the widest possible allow rules; always narrow scope to minimum required permissions.
2. **Forbidden:** Adding allow rules to `system/sepolicy/private/` for vendor domains — vendor domains must use `vendor/<OEM>/sepolicy/` or `system/sepolicy/vendor/`.
3. **Forbidden:** Modifying SELinux policy in `frameworks/` — all policy lives in `system/sepolicy/` or vendor/device sepolicy paths.
4. **Forbidden:** Using `permissive <domain>` as a permanent fix — permissive mode disables enforcement for the entire domain and is only acceptable as a temporary debug aid.
5. **Forbidden:** Adding `allow <source> <target>:file { open read write }` without first checking neverallow constraints — always `grep neverallow` before writing new allow rules.
6. **Forbidden:** Placing vendor-domain `.te` files in `system/sepolicy/private/` — the public/private split is a Treble ABI boundary.
7. **Forbidden:** Routing a resolved SELinux task back to the router without also checking if the underlying process code needs changes — coordinate with the relevant L2 skill for the daemon's code path.

---

## Tool Calls

```bash
# Analyze avc: denied and draft allow rules (use with caution — review output)
audit2allow -i <logfile>

# Check if a type is already defined in platform policy
grep -r "^type <type_name>" system/sepolicy/

# Find all allow rules for a domain
grep -r "allow my_daemon" system/sepolicy/ vendor/*/sepolicy/

# Check neverallow constraints affecting a type
grep -r "neverallow.*my_daemon\|neverallow my_daemon" system/sepolicy/

# Find file_contexts label for a path
grep -r "/path/to/file" system/sepolicy/ vendor/*/sepolicy/ device/*/sepolicy/

# Verify sepolicy compiles (run from AOSP root)
m sepolicy_tests
m CtsSecurityHostTestCases
```

---

## Handoff Rules

| Condition | Hand off to |
|-----------|------------|
| New daemon `.rc` file needed alongside SELinux domain | `L2-init-boot-sequence-expert` |
| New daemon is a HAL service needing `hwservice_contexts` | `L2-hal-vendor-interface-expert` |
| SELinux issue is in a Java system service | `L2-framework-services-expert` |
| Build fails when compiling updated sepolicy | `L2-build-system-expert` |
| SELinux denial involves `/dev/kvm`, `virtualizationservice`, or Microdroid guest policy | `L2-virtualization-pkvm-expert` |

Emit `[L2 SECURITY → HANDOFF]` before transferring.

---

## References

- `references/selinux_policy_guide.md` — Android SELinux policy authoring reference.
- `system/sepolicy/README` — upstream policy documentation.
- `system/sepolicy/public/` — platform-stable type definitions.
- `ANDROID_SW_OWNER_DEV_PLAN.md §5` — L2 skill design spec.

# HS-001: SELinux Domain and .rc File Are Always Paired

**Category:** SELinux + Init
**Skills involved:** L2-security-selinux-expert, L2-init-boot-sequence-expert
**Android versions:** All

## Insight

Every new daemon that requires its own SELinux domain **must** have both a `.te` policy file and a corresponding `.rc` service definition. These are never optional — missing either causes a boot-loop or a `permission denied` crash.

The complete checklist for a new daemon:
1. `system/sepolicy/private/<daemon>.te` — type declaration + `init_daemon_domain()`
2. `system/sepolicy/private/file_contexts` — label for the executable path
3. `<daemon>.rc` — service definition with `user`, `group`, `seclabel`
4. Build rule in `Android.bp` with correct `init_rc` reference

## Why This Matters

Omitting the `.te` file causes `init` to fall back to the `unlabeled` domain, which is denied by `neverallow` rules — the service crashes immediately. Omitting `seclabel` in the `.rc` means `init` cannot transition to the correct domain.

## Trigger

Activate **both** `L2-security-selinux-expert` and `L2-init-boot-sequence-expert` whenever a new daemon or service is being added.

# HS-021: New System Properties Need property_contexts Entry

**Category:** SELinux / Init
**Skills involved:** L2-security-selinux-expert, L2-init-boot-sequence-expert
**Android versions:** Android 8+

## Insight

Every new system property with a non-default prefix must have a `property_contexts` entry. Without it, SELinux will label the property as `default_prop` and `init` will refuse to set it from a restricted context.

**Required files to update:**
1. `system/sepolicy/private/property_contexts` — for `ro.`, `persist.`, framework-owned props
2. `system/sepolicy/vendor/property_contexts` — for `vendor.` prefixed props
3. `system/sepolicy/private/property.te` — if a new property type is needed

**Example entry:**
```
ro.foo.bar.enabled          u:object_r:foo_prop:s0
vendor.foo.feature.enabled  u:object_r:vendor_foo_prop:s0
```

**Common mistake:** Adding a new `ro.boot.*` property expecting it to be automatically accessible. Boot properties are set by the bootloader and need `property_contexts` entries just like any other property.

## Why This Matters

Missing `property_contexts` causes `avc: denied { read }` on `default_prop` for processes that should be allowed to read the property. The AVC message is misleading — it looks like a denial for reading, but the root cause is an unlabeled property.

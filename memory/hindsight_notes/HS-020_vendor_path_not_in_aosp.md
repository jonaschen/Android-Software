# HS-020: Vendor-Supplied Paths Do Not Exist in Vanilla AOSP

**Category:** Routing / Architecture
**Skills involved:** L1-aosp-root-router
**Android versions:** All

## Insight

The following paths are **vendor/SoC-supplied** and do not exist in the AOSP open-source tree. They are present only in device BSPs from specific SoC vendors (Qualcomm, MediaTek, etc.):

| Path | Supplier | Notes |
|------|---------|-------|
| `bootloader/lk/` | Qualcomm ABL/LK BSP | little-kernel source |
| `atf/` or `arm-trusted-firmware/` | ARM / SoC vendor | TF-A source tree |
| `trusty/` | Google / SoC vendor | Trusty TEE OS |

**Forbidden actions when these paths are absent:**
- Do not assert they exist or cite their file paths as definitive.
- Do not suggest cloning them from AOSP — they are not in AOSP.
- Do not treat their absence as a bug — it is normal for vanilla AOSP builds.

**Routing rule:** Route by **subsystem intent**, not by path presence:
- "LK bootloader" task → `L2-bootloader-lk-expert` regardless of whether `bootloader/lk/` exists locally.
- "ATF/TF-A" task → `L2-trusted-firmware-atf-expert` regardless of whether `atf/` exists locally.

## Why This Matters

An agent that asserts `bootloader/lk/app/aboot/aboot.c` exists on a vanilla AOSP workspace will confuse the developer who cannot find the file. Always confirm BSP layout before citing vendor paths.

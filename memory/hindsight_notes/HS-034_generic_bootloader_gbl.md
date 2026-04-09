---
id: HS-034
title: "Generic Bootloader (GBL) — standardized updatable bootloader in Android 16"
skill: L2-bootloader-lk-expert
date: 2026-04-08
source: research-session
---

## Insight

Android 16 introduces the **Generic Bootloader (GBL)**, described as a
"standardized, updatable bootloader designed to streamline the Android boot
process." This is a significant shift from the current vendor-specific bootloader
landscape (LK, U-Boot, proprietary).

Key implications:
1. GBL is designed to be **updatable** — bootloader OTAs become first-class.
2. GBL aims to **standardize** the boot flow, reducing vendor fragmentation.
3. Vendor bootloaders (LK, U-Boot) may eventually be replaced or wrapped by GBL.
4. The L2-bootloader-lk-expert skill will need a major refresh to cover GBL
   alongside or instead of LK-specific knowledge.

## GBL Technical Details (updated 2026-04-10)

- **AOSP source path**: `bootable/libbootloader` (confirmed in public AOSP).
  Build branch: `uefi-gbl-mainline`. Build system: Bazel.
  Build command: `tools/bazel run //bootable/libbootloader:gbl_efi_dist`
- **Partition layout**: Two FAT partitions `android_esp_a` / `android_esp_b`
  (≥8 MB each, EFI System Partition GUID). GBL binary at `/EFI/BOOT/BOOTAA64.EFI`.
- **Required UEFI protocols**: `EFI_BLOCK_IO_PROTOCOL`, `EFI_RNG_PROTOCOL`,
  `GBL_EFI_AVB_PROTOCOL`, `GBL_EFI_BOOT_CONTROL_PROTOCOL`, `GBL_EFI_AVF_PROTOCOL`.
- **Firmware API level**: `gbl_fw_api_level` UEFI variable must match `ro.board.api_level`.
- **Compatibility**: Reference implementations exist for EDK2, U-Boot, and LK with UEFI.
- **ARM64 recommendation**: "Beginning with Android 16, if you ship a device based
  on ARM-64 chipset, we strongly recommend that you deploy the latest
  Google-certified version of GBL."

## Lesson

The bootloader skill currently focuses on LK (Little Kernel) and vendor-specific
bootloader paths (`bootloader/lk/`, `bootable/bootloader/`). With GBL:
- **Confirmed**: GBL source lives at `bootable/libbootloader` in AOSP.
- The skill's path_scope must expand to cover `bootable/libbootloader/`.
- Fastboot protocol is a core GBL component (not a separate binary).
- A/B slot management is handled via `GBL_EFI_BOOT_CONTROL_PROTOCOL`.
- AVF integration via `GBL_EFI_AVF_PROTOCOL` links GBL to pKVM early boot VMs.

## Cross-Skill Impact

- **L2-init-boot-sequence-expert**: GBL changes the pre-init boot flow.
- **L2-trusted-firmware-atf-expert**: GBL sits between ATF and Android init;
  handoff protocol may change.
- **L2-version-migration-expert**: GBL migration is a major A16 delta item.
- **L1-aosp-root-router**: May need new path mapping for GBL sources.

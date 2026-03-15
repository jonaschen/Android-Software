#!/usr/bin/env python3
"""
check_aidl_version.py — AIDL HAL interface version and freeze status checker

Scans hardware/interfaces/ (or a specified path) for aidl_interface modules
in Android.bp files and reports:
  - Interface name
  - Current version
  - Freeze status (frozen / unfrozen)
  - stability annotation (vintf / local)
  - Whether a VINTF manifest entry likely exists

Usage:
    python3 check_aidl_version.py [search_path]
    python3 check_aidl_version.py hardware/interfaces/
    python3 check_aidl_version.py hardware/interfaces/sensors/
"""

import sys
import os
import re
import json
from pathlib import Path


def find_bp_files(search_path: str) -> list[Path]:
    return list(Path(search_path).rglob("Android.bp"))


def parse_aidl_interfaces(bp_path: Path) -> list[dict]:
    """
    Minimal Android.bp parser for aidl_interface blocks.
    Returns a list of dicts with interface metadata.
    """
    text = bp_path.read_text(errors="replace")
    interfaces = []

    # Find all aidl_interface { ... } blocks (non-nested, best-effort)
    pattern = re.compile(r'aidl_interface\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', re.DOTALL)
    for match in pattern.finditer(text):
        block = match.group(1)

        def extract(field: str, default="<unknown>") -> str:
            m = re.search(rf'{field}\s*:\s*"([^"]+)"', block)
            return m.group(1) if m else default

        def extract_bool(field: str) -> bool | None:
            m = re.search(rf'{field}\s*:\s*(true|false)', block)
            if m:
                return m.group(1) == "true"
            return None

        name = extract("name")
        stability = extract("stability", default="local")
        frozen = extract_bool("frozen")

        # Extract version numbers from versions_with_info or versions
        versions = re.findall(r'version\s*:\s*"(\d+)"', block)
        if not versions:
            versions = re.findall(r'versions\s*:\s*\[([^\]]*)\]', block)
            if versions:
                versions = re.findall(r'"(\d+)"', versions[0])

        latest_version = max((int(v) for v in versions), default=None) if versions else None

        interfaces.append({
            "name": name,
            "stability": stability,
            "frozen": frozen,
            "versions": [int(v) for v in versions],
            "latest_version": latest_version,
            "bp_file": str(bp_path),
        })

    return interfaces


def assess_risk(iface: dict) -> list[str]:
    warnings = []
    if iface["stability"] != "vintf":
        warnings.append("NOT vintf-stable — cannot be used as a HAL interface")
    if iface["frozen"] is False:
        warnings.append("Interface is UNFROZEN — changes are in progress")
    if iface["frozen"] is None and iface["latest_version"] is not None:
        warnings.append("Freeze status unknown — verify frozen: field in Android.bp")
    if not iface["versions"]:
        warnings.append("No versions defined — interface may not be released yet")
    return warnings


def main():
    search_path = sys.argv[1] if len(sys.argv) > 1 else "hardware/interfaces"

    if not os.path.isdir(search_path):
        print(f"ERROR: '{search_path}' is not a directory.")
        sys.exit(1)

    bp_files = find_bp_files(search_path)
    all_interfaces = []

    for bp in bp_files:
        interfaces = parse_aidl_interfaces(bp)
        all_interfaces.extend(interfaces)

    if not all_interfaces:
        print(f"No aidl_interface modules found under '{search_path}'.")
        sys.exit(0)

    print(f"\n{'='*70}")
    print(f"AIDL Interface Report — {search_path}")
    print(f"{'='*70}")
    print(f"{'Interface':<45} {'Ver':>4}  {'Stability':<8}  {'Frozen':<8}  Status")
    print(f"{'-'*70}")

    issues_found = 0
    for iface in sorted(all_interfaces, key=lambda x: x["name"]):
        warnings = assess_risk(iface)
        ver_str = str(iface["latest_version"]) if iface["latest_version"] is not None else "—"
        frozen_str = {True: "yes", False: "NO", None: "?"}[iface["frozen"]]
        status = "OK" if not warnings else f"WARN ({len(warnings)})"
        if warnings:
            issues_found += len(warnings)

        print(f"  {iface['name']:<43} {ver_str:>4}  {iface['stability']:<8}  {frozen_str:<8}  {status}")

        for w in warnings:
            print(f"    ⚠  {w}")

    print(f"{'='*70}")
    print(f"Total interfaces: {len(all_interfaces)} | Issues: {issues_found}")
    print(f"{'='*70}\n")

    sys.exit(1 if issues_found > 0 else 0)


if __name__ == "__main__":
    main()

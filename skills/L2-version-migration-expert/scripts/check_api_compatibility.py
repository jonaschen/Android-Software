#!/usr/bin/env python3
"""
check_api_compatibility.py — Android API surface compatibility checker

Compares two api/current.txt (or system-current.txt) files and reports:
  - Removed methods or classes (breaking changes)
  - Added methods or classes (non-breaking, informational)
  - Changed method signatures (potentially breaking)

Also checks dirty_pages.json and flags skills that need refresh.

Usage:
    python3 check_api_compatibility.py <before.txt> <after.txt>
    python3 check_api_compatibility.py \
        android-14/frameworks/base/api/current.txt \
        android-15/frameworks/base/api/current.txt

    # Check dirty pages status:
    python3 check_api_compatibility.py --dirty-pages memory/dirty_pages.json
"""

import sys
import re
import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ApiEntry:
    kind: str        # "method" | "field" | "class" | "interface"
    signature: str   # full signature line


def parse_api_txt(path: Path) -> dict[str, ApiEntry]:
    """
    Parse an Android api/current.txt file into a dict keyed by signature.
    This is a simplified parser — handles method/field/class declarations.
    """
    entries = {}
    current_class = ""

    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue

        # Class/interface declaration
        m = re.match(r'^(public|protected)\s+(abstract\s+)?(class|interface|enum|@interface)\s+(\S+)', line)
        if m:
            current_class = m.group(4).split("<")[0]
            key = f"CLASS:{current_class}"
            entries[key] = ApiEntry(kind=m.group(3), signature=line)
            continue

        # Method/field declaration
        if current_class and ("(" in line or line.startswith("field") or "method" in line):
            key = f"{current_class}:{line}"
            entries[key] = ApiEntry(kind="member", signature=line)

    return entries


def compare_apis(before: dict, after: dict) -> tuple[list, list, list]:
    removed = [k for k in before if k not in after]
    added = [k for k in after if k not in before]
    # Changed: same key, different signature (shouldn't happen with key = full sig, but catch class redefs)
    changed = [k for k in before if k in after and before[k].signature != after[k].signature]
    return removed, added, changed


def check_dirty_pages(dirty_path: Path):
    print(f"\n=== Dirty Pages Status: {dirty_path} ===")
    data = json.loads(dirty_path.read_text())
    skills = data.get("skills", {})
    dirty_skills = [(name, info) for name, info in skills.items() if info.get("status") == "dirty"]
    not_deployed = [(name, info) for name, info in skills.items() if info.get("status") == "not_yet_deployed"]
    clean_skills = [(name, info) for name, info in skills.items() if info.get("status") == "clean"]

    print(f"\n  Clean ({len(clean_skills)}):")
    for name, info in clean_skills:
        print(f"    ✓ {name} (tested: {info.get('android_version_tested', '?')})")

    print(f"\n  Dirty ({len(dirty_skills)}) — NEED REFRESH:")
    for name, info in dirty_skills:
        print(f"    ✗ {name}")
        print(f"      Reason:  {info.get('dirty_reason', '?')}")
        print(f"      Paths:   {info.get('affected_paths', [])}")

    print(f"\n  Not yet deployed ({len(not_deployed)}):")
    for name, _ in not_deployed:
        print(f"    - {name}")

    if dirty_skills:
        print(f"\n  ACTION REQUIRED: {len(dirty_skills)} skill(s) need refresh.")
        sys.exit(1)
    else:
        print(f"\n  All deployed skills are clean.")


def main():
    if len(sys.argv) == 3 and not sys.argv[1].startswith("--"):
        before_path = Path(sys.argv[1])
        after_path = Path(sys.argv[2])

        if not before_path.exists():
            print(f"ERROR: before file not found: {before_path}")
            sys.exit(1)
        if not after_path.exists():
            print(f"ERROR: after file not found: {after_path}")
            sys.exit(1)

        print(f"\n=== API Compatibility Check ===")
        print(f"  Before: {before_path}")
        print(f"  After:  {after_path}\n")

        before = parse_api_txt(before_path)
        after = parse_api_txt(after_path)
        removed, added, changed = compare_apis(before, after)

        print(f"  REMOVED ({len(removed)}) — Breaking changes:")
        for r in sorted(removed)[:50]:
            print(f"    - {r.split(':', 1)[-1][:100]}")
        if len(removed) > 50:
            print(f"    ... and {len(removed) - 50} more")

        print(f"\n  ADDED ({len(added)}) — New API:")
        for a in sorted(added)[:20]:
            print(f"    + {a.split(':', 1)[-1][:100]}")
        if len(added) > 20:
            print(f"    ... and {len(added) - 20} more")

        print(f"\n  CHANGED ({len(changed)}) — Signature changes:")
        for c in sorted(changed)[:20]:
            print(f"    ~ {c.split(':', 1)[-1][:100]}")

        print(f"\n=== Summary ===")
        print(f"  Removed: {len(removed)} | Added: {len(added)} | Changed: {len(changed)}")
        if removed:
            print("  RESULT: BREAKING CHANGES DETECTED — review before upgrading")
            sys.exit(1)
        else:
            print("  RESULT: No breaking removals detected")

    elif len(sys.argv) == 3 and sys.argv[1] == "--dirty-pages":
        dirty_path = Path(sys.argv[2])
        if not dirty_path.exists():
            print(f"ERROR: dirty_pages.json not found: {dirty_path}")
            sys.exit(1)
        check_dirty_pages(dirty_path)

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

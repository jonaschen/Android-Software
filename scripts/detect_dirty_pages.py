#!/usr/bin/env python3
"""
detect_dirty_pages.py — Git-diff driven dirty page detection
=============================================================
Phase 4 deliverable 4.1.

Scans git diff output (or a file listing changed paths) against the
`path_scope` fields extracted from each SKILL.md frontmatter, and
identifies which skills are affected ("dirty") by the changes.

Can optionally update memory/dirty_pages.json in-place.

Usage:
    # From a git diff --name-only between two tags:
    git diff --name-only android-14.0.0_r1..android-15.0.0_r1 | \\
        python3 scripts/detect_dirty_pages.py --reason android_version_bump

    # From a file of changed paths:
    python3 scripts/detect_dirty_pages.py --input changed_files.txt --reason path_structure_changed

    # Dry run (default): prints affected skills without modifying dirty_pages.json
    python3 scripts/detect_dirty_pages.py --input changed_files.txt

    # Apply: updates dirty_pages.json with dirty status
    python3 scripts/detect_dirty_pages.py --input changed_files.txt --reason android_version_bump --apply

Exit codes:
    0 — success (dirty skills may or may not exist)
    1 — error (bad input, missing files)
"""

import argparse
import fnmatch
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_DIRTY_REASONS = {
    "android_version_bump",
    "path_structure_changed",
    "api_surface_changed",
    "selinux_policy_restructured",
    "hal_interface_version_bump",
    "manual_invalidation",
}


# ---------------------------------------------------------------------------
# SKILL.md frontmatter parser
# ---------------------------------------------------------------------------

def parse_skill_frontmatter(skill_md_path: str) -> Optional[Dict]:
    """Extract YAML-like frontmatter from a SKILL.md file.

    Returns a dict with at least 'name' and 'path_scope' keys, or None
    if the file is missing or has no frontmatter.
    """
    try:
        with open(skill_md_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return None

    # Frontmatter is between --- lines
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Simple key: value parsing (strip inline comments)
        m = re.match(r"^(\w+)\s*:\s*(.+)$", line)
        if m:
            key = m.group(1)
            value = m.group(2).split("#")[0].strip()
            frontmatter[key] = value

    return frontmatter if frontmatter.get("path_scope") else None


def parse_path_scope(path_scope_raw: str) -> List[str]:
    """Parse a comma-separated path_scope string into individual patterns.

    Handles patterns like:
        build/, Android.bp, *.mk, vendor/*/sepolicy/
        cross-cutting (diff analysis across all paths)
    """
    if "cross-cutting" in path_scope_raw.lower():
        # Version migration skill matches everything — skip auto-detection
        return []

    patterns = []
    for part in path_scope_raw.split(","):
        part = part.strip()
        if part:
            patterns.append(part)
    return patterns


# ---------------------------------------------------------------------------
# Path matching logic
# ---------------------------------------------------------------------------

def path_matches_pattern(changed_path: str, pattern: str) -> bool:
    """Check if a changed file path matches a skill's path_scope pattern.

    Matching rules:
    1. Directory prefix: pattern "build/" matches "build/soong/Android.bp"
    2. Glob patterns: "*.mk" matches "device/google/sunfish/BoardConfig.mk"
    3. Wildcard directories: "vendor/*/sepolicy/" matches "vendor/qcom/sepolicy/foo.te"
    4. Exact filename: "Android.bp" matches "packages/modules/Foo/Android.bp"
    5. Template placeholders: "<OEM>" or "<product>" treated as wildcards
    """
    # Normalize: strip leading/trailing slashes for consistent comparison
    changed_path = changed_path.strip().lstrip("/")
    pattern = pattern.strip()

    # Replace template placeholders with wildcard
    pattern = re.sub(r"<[^>]+>", "*", pattern)

    # Case 1: Directory prefix match (pattern ends with /)
    if pattern.endswith("/"):
        prefix = pattern.rstrip("/")
        # Direct prefix match
        if changed_path.startswith(prefix + "/") or changed_path == prefix:
            return True
        # Glob-style prefix (e.g., vendor/*/sepolicy/)
        # Convert to fnmatch pattern
        glob_pattern = prefix + "/*"
        if fnmatch.fnmatch(changed_path, glob_pattern):
            return True
        # Also match the directory itself at any depth via prefix
        if fnmatch.fnmatch(changed_path, prefix):
            return True
        return False

    # Case 2: Glob pattern (contains * or ?)
    if "*" in pattern or "?" in pattern:
        # Match against full path
        if fnmatch.fnmatch(changed_path, pattern):
            return True
        # Match against basename only (e.g., "*.mk" matches "foo/bar/Kconfig.mk")
        basename = os.path.basename(changed_path)
        if fnmatch.fnmatch(basename, pattern):
            return True
        return False

    # Case 3: Exact path or filename match
    # Match as a path prefix
    if changed_path.startswith(pattern + "/") or changed_path == pattern:
        return True
    # Match against basename (e.g., "Android.bp" matches "foo/Android.bp")
    basename = os.path.basename(changed_path)
    if basename == pattern:
        return True

    return False


def detect_affected_skills(
    changed_paths: List[str],
    skills_dir: str,
) -> Dict[str, List[str]]:
    """Scan changed paths against all skills' path_scope fields.

    Returns a dict mapping skill_name -> list of matching changed paths.
    """
    # Load all skill frontmatters
    skill_patterns: Dict[str, List[str]] = {}  # skill_name -> [patterns]
    skill_dirs = sorted(Path(skills_dir).iterdir())

    for skill_dir in skill_dirs:
        if not skill_dir.is_dir() or not skill_dir.name.startswith("L"):
            continue
        skill_md = skill_dir / "SKILL.md"
        fm = parse_skill_frontmatter(str(skill_md))
        if fm is None:
            continue
        patterns = parse_path_scope(fm["path_scope"])
        if patterns:
            skill_patterns[skill_dir.name] = patterns

    # Match each changed path against each skill's patterns
    affected: Dict[str, List[str]] = {}

    for changed_path in changed_paths:
        changed_path = changed_path.strip()
        if not changed_path:
            continue
        for skill_name, patterns in skill_patterns.items():
            for pattern in patterns:
                if path_matches_pattern(changed_path, pattern):
                    affected.setdefault(skill_name, []).append(changed_path)
                    break  # One match per skill per path is enough

    return affected


# ---------------------------------------------------------------------------
# dirty_pages.json updater
# ---------------------------------------------------------------------------

def update_dirty_pages(
    dirty_pages_path: str,
    affected_skills: Dict[str, List[str]],
    reason: str,
) -> None:
    """Update dirty_pages.json with newly affected skills."""
    with open(dirty_pages_path, "r") as f:
        data = json.load(f)

    today = date.today().isoformat()
    data["_last_updated"] = today

    for skill_name, paths in affected_skills.items():
        if skill_name in data["skills"]:
            entry = data["skills"][skill_name]
            entry["status"] = "dirty"
            entry["dirty_reason"] = reason
            # Merge affected paths (deduplicate)
            existing = set(entry.get("affected_paths", []))
            existing.update(paths)
            entry["affected_paths"] = sorted(existing)
        else:
            # Skill exists on disk but not in dirty_pages.json — add it
            data["skills"][skill_name] = {
                "status": "dirty",
                "android_version_tested": None,
                "last_validated": None,
                "dirty_reason": reason,
                "affected_paths": sorted(paths),
            }

    with open(dirty_pages_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"  [APPLY] Updated {dirty_pages_path} ({len(affected_skills)} skills marked dirty)")


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def print_report(
    affected_skills: Dict[str, List[str]],
    total_changed: int,
) -> None:
    """Print a human-readable report of affected skills."""
    print(f"\n{'=' * 60}")
    print("  Dirty Page Detection Report")
    print(f"{'=' * 60}")
    print(f"  Changed files analyzed : {total_changed}")
    print(f"  Skills affected        : {len(affected_skills)}")
    print(f"{'=' * 60}\n")

    if not affected_skills:
        print("  No skills affected by the detected changes.")
        return

    for skill_name in sorted(affected_skills.keys()):
        paths = affected_skills[skill_name]
        print(f"  {skill_name}  ({len(paths)} file(s))")
        for p in sorted(paths)[:10]:  # Show first 10 paths per skill
            print(f"    - {p}")
        if len(paths) > 10:
            print(f"    ... and {len(paths) - 10} more")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect dirty skills from git diff output or a file listing changed paths.",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="File containing changed paths (one per line). If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--skills-dir",
        default=None,
        help="Path to skills/ directory (default: auto-detect from repo root).",
    )
    parser.add_argument(
        "--dirty-pages",
        default=None,
        help="Path to dirty_pages.json (default: auto-detect from repo root).",
    )
    parser.add_argument(
        "--reason",
        default=None,
        choices=sorted(VALID_DIRTY_REASONS),
        help="Reason for marking skills dirty (required with --apply).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Update dirty_pages.json in-place (default: dry run).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable report.",
    )
    args = parser.parse_args()

    # Resolve repo root
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    skills_dir = args.skills_dir or str(repo_root / "skills")
    dirty_pages_path = args.dirty_pages or str(repo_root / "memory" / "dirty_pages.json")

    if not os.path.isdir(skills_dir):
        print(f"ERROR: Skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(1)

    # Read changed paths
    if args.input:
        try:
            with open(args.input, "r") as f:
                changed_paths = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print("Reading changed paths from stdin (pipe git diff --name-only or Ctrl+D to end):",
                  file=sys.stderr)
        changed_paths = [line.strip() for line in sys.stdin if line.strip()]

    if not changed_paths:
        print("WARNING: No changed paths provided.", file=sys.stderr)
        if args.json:
            print(json.dumps({"affected_skills": {}, "total_changed": 0}))
        sys.exit(0)

    # Detect affected skills
    affected = detect_affected_skills(changed_paths, skills_dir)

    # Output
    if args.json:
        result = {
            "total_changed": len(changed_paths),
            "affected_skills": {
                name: sorted(paths) for name, paths in sorted(affected.items())
            },
        }
        print(json.dumps(result, indent=2))
    else:
        print_report(affected, len(changed_paths))

    # Apply if requested
    if args.apply:
        if not args.reason:
            print("ERROR: --reason is required when using --apply.", file=sys.stderr)
            sys.exit(1)
        if not os.path.isfile(dirty_pages_path):
            print(f"ERROR: dirty_pages.json not found: {dirty_pages_path}", file=sys.stderr)
            sys.exit(1)
        if affected:
            update_dirty_pages(dirty_pages_path, affected, args.reason)
        else:
            print("  [APPLY] No skills affected — dirty_pages.json unchanged.")


if __name__ == "__main__":
    main()

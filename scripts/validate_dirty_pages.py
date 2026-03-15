#!/usr/bin/env python3
"""
validate_dirty_pages.py — dirty_pages.json schema validator
============================================================
Phase 3 deliverable 3.4.

Validates memory/dirty_pages.json against the expected schema and reports:
  - Missing required fields
  - Invalid status values
  - Invalid dirty_reason values
  - Skills present in dirty_pages.json but missing on disk (and vice versa)
  - Skills with status=dirty but no dirty_reason or affected_paths

Usage:
    python3 scripts/validate_dirty_pages.py [--dirty-pages <path>] [--skills-dir <path>]

Exit codes:
    0 — valid
    1 — validation errors found
"""

import json
import os
import sys
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

REQUIRED_TOP_KEYS = {
    "_schema_version", "_description", "_last_updated",
    "_android_version_baseline", "skills",
    "_status_enum", "_dirty_reasons_enum",
}

REQUIRED_SKILL_KEYS = {
    "status", "android_version_tested", "last_validated",
    "dirty_reason", "affected_paths",
}

VALID_STATUSES = {"clean", "dirty", "not_yet_deployed"}

VALID_DIRTY_REASONS = {
    "android_version_bump",
    "path_structure_changed",
    "api_surface_changed",
    "selinux_policy_restructured",
    "hal_interface_version_bump",
    "manual_invalidation",
    None,  # allowed when not dirty
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def error(msg: str) -> None:
    print(f"  [ERROR] {msg}")


def warn(msg: str) -> None:
    print(f"  [WARN ] {msg}")


def ok(msg: str) -> None:
    print(f"  [OK   ] {msg}")


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate(dirty_pages_path: str, skills_dir: str) -> int:
    """Returns number of errors found."""
    errors = 0

    # ---- Load JSON ----
    try:
        with open(dirty_pages_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        error(f"File not found: {dirty_pages_path}")
        return 1
    except json.JSONDecodeError as e:
        error(f"JSON parse error: {e}")
        return 1

    print(f"\n{'=' * 60}")
    print(f"  dirty_pages.json validator")
    print(f"  File: {dirty_pages_path}")
    print(f"{'=' * 60}\n")

    # ---- Top-level keys ----
    print("--- Top-level schema ---")
    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            error(f"Missing required top-level key: '{key}'")
            errors += 1
        else:
            ok(f"'{key}' present")

    # ---- Skills section ----
    skills = data.get("skills", {})
    if not isinstance(skills, dict):
        error("'skills' must be a JSON object")
        return errors + 1

    print(f"\n--- Skill entries ({len(skills)} found) ---")

    for skill_name, skill in skills.items():
        skill_errors = 0

        # Required fields
        for key in REQUIRED_SKILL_KEYS:
            if key not in skill:
                error(f"{skill_name}: Missing required field '{key}'")
                skill_errors += 1

        # Status value
        status = skill.get("status")
        if status not in VALID_STATUSES:
            error(f"{skill_name}: Invalid status '{status}' (valid: {sorted(VALID_STATUSES)})")
            skill_errors += 1

        # dirty_reason consistency
        dirty_reason = skill.get("dirty_reason")
        if status == "dirty":
            if dirty_reason is None:
                error(f"{skill_name}: status=dirty but dirty_reason is null")
                skill_errors += 1
            elif dirty_reason not in VALID_DIRTY_REASONS:
                error(f"{skill_name}: Invalid dirty_reason '{dirty_reason}'")
                skill_errors += 1
            affected = skill.get("affected_paths", [])
            if not affected:
                warn(f"{skill_name}: status=dirty but affected_paths is empty")
        elif status == "clean" and dirty_reason is not None:
            warn(f"{skill_name}: status=clean but dirty_reason is set (expected null)")

        # affected_paths type check
        affected_paths = skill.get("affected_paths")
        if affected_paths is not None and not isinstance(affected_paths, list):
            error(f"{skill_name}: 'affected_paths' must be a list")
            skill_errors += 1

        if skill_errors == 0:
            ok(f"{skill_name}: valid (status={status})")
        else:
            errors += skill_errors

    # ---- Cross-check with skills/ directory ----
    print(f"\n--- Cross-check with {skills_dir} ---")
    skills_on_disk = set()
    if os.path.isdir(skills_dir):
        for entry in os.scandir(skills_dir):
            if entry.is_dir() and entry.name.startswith("L"):
                skills_on_disk.add(entry.name)
    else:
        warn(f"Skills directory not found: {skills_dir}")

    skills_in_json = set(skills.keys())

    in_json_not_disk = skills_in_json - skills_on_disk
    in_disk_not_json = skills_on_disk - skills_in_json

    for s in sorted(in_json_not_disk):
        warn(f"Skill '{s}' in dirty_pages.json but not found in {skills_dir}/")

    for s in sorted(in_disk_not_json):
        warn(f"Skill '{s}' exists on disk but has no entry in dirty_pages.json")

    if not in_json_not_disk and not in_disk_not_json:
        ok("dirty_pages.json and skills/ directory are in sync")

    # ---- Summary ----
    print(f"\n{'=' * 60}")
    print(f"  Total skills validated : {len(skills)}")
    print(f"  Errors                 : {errors}")
    print(f"{'=' * 60}\n")

    return errors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate memory/dirty_pages.json schema")
    parser.add_argument(
        "--dirty-pages",
        default="memory/dirty_pages.json",
        help="Path to dirty_pages.json (default: memory/dirty_pages.json)",
    )
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="Path to skills/ directory (default: skills/)",
    )
    args = parser.parse_args()

    # Resolve paths relative to the repo root (script can be run from anywhere)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    dirty_pages_path = args.dirty_pages
    if not os.path.isabs(dirty_pages_path):
        dirty_pages_path = str(repo_root / dirty_pages_path)

    skills_dir = args.skills_dir
    if not os.path.isabs(skills_dir):
        skills_dir = str(repo_root / skills_dir)

    error_count = validate(dirty_pages_path, skills_dir)
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()

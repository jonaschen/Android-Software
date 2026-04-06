#!/usr/bin/env python3
"""
skill_lint.py — SKILL.md schema validator
==========================================
Phase 4 deliverable 4.4.

Validates all SKILL.md files against the template schema from
ANDROID_SW_OWNER_DEV_PLAN.md §11. Checks:
  - Required YAML frontmatter fields (name, layer, path_scope, version,
    android_version_tested, parent_skill)
  - Required markdown sections (Path Scope, Trigger Conditions, Architecture
    Intelligence, Forbidden Actions, Tool Calls, Handoff Rules, References)
  - Minimum 5 entries in Forbidden Actions
  - Layer / parent_skill consistency
  - Version format (semver-like)

Usage:
    python3 scripts/skill_lint.py [--skills-dir <path>] [--include-templates]

Exit codes:
    0 — all skills pass
    1 — validation errors found
    2 — no skills found
"""

import argparse
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

REQUIRED_FRONTMATTER_FIELDS = [
    "name",
    "layer",
    "path_scope",
    "version",
    "android_version_tested",
    "parent_skill",
]

REQUIRED_SECTIONS_L2 = [
    "Path Scope",
    "Trigger Conditions",
    "Architecture Intelligence",
    "Forbidden Actions",
    "Tool Calls",
    "Handoff Rules",
    "References",
]

# L1 has a slightly different structure (includes Role and Routing Algorithm)
REQUIRED_SECTIONS_L1 = [
    "Path Scope",
    "Trigger Conditions",
    "Forbidden Actions",
    "Handoff Rules",
    "Tool Calls",
    "References",
]

REQUIRED_SECTIONS_L3 = REQUIRED_SECTIONS_L2  # L3 follows L2 template

VALID_LAYERS = {"L1", "L2", "L3"}

MIN_FORBIDDEN_ACTIONS = 5

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class LintResult:
    """Collects errors and warnings for a single SKILL.md."""

    def __init__(self, skill_name: str, path: str):
        self.skill_name = skill_name
        self.path = path
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Parse YAML frontmatter delimited by ---. Returns (fields, body)."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    fm_text = parts[1].strip()
    body = parts[2]

    fields: dict[str, str] = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(\w[\w_]*)\s*:\s*(.*)$", line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            # Strip inline YAML comments
            if "  #" in value:
                value = value[: value.index("  #")].strip()
            fields[key] = value

    return fields, body


def extract_sections(body: str) -> list[str]:
    """Extract all ## heading names from the markdown body."""
    sections = []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            sections.append(m.group(1).strip())
    return sections


def count_forbidden_actions(body: str) -> int:
    """Count entries in the Forbidden Actions section.

    Entries are numbered lines like '1. **Forbidden:** ...' or
    bullet lines like '- **Forbidden:** ...' or '- ❌ ...'
    or generic numbered/bulleted list items within the section.
    """
    in_section = False
    count = 0
    for line in body.splitlines():
        if re.match(r"^##\s+Forbidden Actions", line):
            in_section = True
            continue
        if in_section and re.match(r"^##\s+", line):
            break
        if in_section:
            # Numbered entries: 1. ..., 2. ...
            if re.match(r"^\s*\d+\.\s+", line):
                count += 1
            # Bullet entries that contain substantive text
            elif re.match(r"^\s*[-*]\s+\S", line):
                count += 1
            # Table row entries with ❌
            elif re.match(r"^\|.*❌", line):
                count += 1
    return count


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def lint_skill(skill_dir: str, include_templates: bool = False) -> LintResult | None:
    """Lint a single SKILL.md. Returns None if the skill should be skipped."""
    skill_name = os.path.basename(skill_dir)
    skill_path = os.path.join(skill_dir, "SKILL.md")

    # Skip template directories unless explicitly included
    if not include_templates and "TEMPLATE" in skill_name.upper():
        return None

    if not os.path.isfile(skill_path):
        result = LintResult(skill_name, skill_path)
        result.error("SKILL.md file not found")
        return result

    with open(skill_path, encoding="utf-8") as f:
        content = f.read()

    result = LintResult(skill_name, skill_path)

    # ---- Frontmatter ----
    fm, body = parse_frontmatter(content)

    if not fm:
        result.error("No YAML frontmatter found (must start with ---)")
        return result

    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in fm:
            result.error(f"Missing required frontmatter field: '{field}'")

    # Layer validation
    layer = fm.get("layer", "")
    if layer and layer not in VALID_LAYERS:
        result.error(f"Invalid layer '{layer}' (valid: {sorted(VALID_LAYERS)})")

    # Version format
    version = fm.get("version", "")
    if version and not SEMVER_PATTERN.match(version):
        result.warn(f"Version '{version}' does not follow semver format (x.y.z)")

    # parent_skill consistency
    parent = fm.get("parent_skill", "")
    if layer == "L1" and parent and parent != "null":
        result.warn("L1 skill should have parent_skill: null")
    if layer == "L2" and (not parent or parent == "null"):
        result.warn("L2 skill should reference a parent_skill (typically 'aosp-root-router')")
    if layer == "L3" and (not parent or parent == "null"):
        result.warn("L3 skill should reference a parent L2 skill")

    # ---- Required sections ----
    sections = extract_sections(body)

    if layer == "L1":
        required = REQUIRED_SECTIONS_L1
    elif layer == "L3":
        required = REQUIRED_SECTIONS_L3
    else:
        required = REQUIRED_SECTIONS_L2

    for section in required:
        if section not in sections:
            result.error(f"Missing required section: '## {section}'")

    # ---- Forbidden Actions count ----
    if "Forbidden Actions" in sections:
        fa_count = count_forbidden_actions(body)
        if fa_count < MIN_FORBIDDEN_ACTIONS:
            result.error(
                f"Forbidden Actions has {fa_count} entries "
                f"(minimum {MIN_FORBIDDEN_ACTIONS} required)"
            )
    # If the section is missing entirely, the missing-section error covers it.

    return result


def lint_all(skills_dir: str, include_templates: bool = False) -> list[LintResult]:
    """Lint all SKILL.md files under skills_dir."""
    results = []

    if not os.path.isdir(skills_dir):
        print(f"Error: Skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(2)

    for entry in sorted(os.scandir(skills_dir), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        if not entry.name.startswith("L"):
            continue
        result = lint_skill(entry.path, include_templates)
        if result is not None:
            results.append(result)

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(results: list[LintResult]) -> int:
    """Print results and return total error count."""
    total_errors = 0
    total_warnings = 0

    print(f"\n{'=' * 60}")
    print("  SKILL.md Schema Validator (skill_lint.py)")
    print(f"{'=' * 60}\n")

    for r in results:
        status = "PASS" if r.ok else "FAIL"
        print(f"  [{status}] {r.skill_name}")

        for e in r.errors:
            print(f"         [ERROR] {e}")
        for w in r.warnings:
            print(f"         [WARN ] {w}")

        total_errors += len(r.errors)
        total_warnings += len(r.warnings)

    print(f"\n{'=' * 60}")
    print(f"  Skills validated : {len(results)}")
    print(f"  Errors           : {total_errors}")
    print(f"  Warnings         : {total_warnings}")
    print(f"{'=' * 60}\n")

    return total_errors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate SKILL.md files against the schema template"
    )
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="Path to skills/ directory (default: skills/)",
    )
    parser.add_argument(
        "--include-templates",
        action="store_true",
        help="Also validate L3-TEMPLATE and other template directories",
    )
    parser.add_argument(
        "--help-schema",
        action="store_true",
        help="Print the expected SKILL.md schema and exit",
    )
    args = parser.parse_args()

    if args.help_schema:
        print("Expected SKILL.md schema (from ANDROID_SW_OWNER_DEV_PLAN.md §11):")
        print()
        print("  YAML frontmatter fields:")
        for f in REQUIRED_FRONTMATTER_FIELDS:
            print(f"    - {f}")
        print()
        print("  Required sections (L2/L3):")
        for s in REQUIRED_SECTIONS_L2:
            print(f"    - ## {s}")
        print()
        print("  Required sections (L1):")
        for s in REQUIRED_SECTIONS_L1:
            print(f"    - ## {s}")
        print()
        print(f"  Minimum Forbidden Actions entries: {MIN_FORBIDDEN_ACTIONS}")
        sys.exit(0)

    # Resolve paths relative to repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    skills_dir = args.skills_dir
    if not os.path.isabs(skills_dir):
        skills_dir = str(repo_root / skills_dir)

    results = lint_all(skills_dir, args.include_templates)

    if not results:
        print("No skills found to validate.", file=sys.stderr)
        sys.exit(2)

    error_count = print_results(results)
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()

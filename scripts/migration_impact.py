#!/usr/bin/env python3
"""
migration_impact.py — Automated migration impact report generator
=================================================================
Phase 4 deliverable 4.2.

Given an Android version bump (e.g., A14 to A15), generates a per-skill
refresh checklist. For each affected skill, lists: changed path scopes,
steward notes, dirty status, and required SKILL.md updates.

Consumes data from:
  - memory/dirty_pages.json (dirty status, steward notes, affected paths)
  - skills/*/SKILL.md (frontmatter: path_scope, android_version_tested, version)
  - skills/*/SKILL.md (Architecture Intelligence section content)

Usage:
    # Generate a migration report for A14 → A15:
    python3 scripts/migration_impact.py --from "Android 14" --to "Android 15"

    # Generate report in JSON format:
    python3 scripts/migration_impact.py --from "Android 14" --to "Android 15" --json

    # Custom paths:
    python3 scripts/migration_impact.py --from "Android 14" --to "Android 15" \\
        --skills-dir ./skills --dirty-pages ./memory/dirty_pages.json

    # Include only dirty skills (skip clean/not_yet_deployed):
    python3 scripts/migration_impact.py --from "Android 14" --to "Android 15" --dirty-only

Exit codes:
    0 — success
    1 — error (missing files, invalid arguments)
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# SKILL.md parsing
# ---------------------------------------------------------------------------

def parse_skill_frontmatter(skill_md_path: str) -> Optional[Dict[str, str]]:
    """Extract YAML-like frontmatter from a SKILL.md file.

    Returns a dict of key-value pairs, or None if no frontmatter found.
    """
    try:
        with open(skill_md_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return None

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(\w+)\s*:\s*(.+)$", line)
        if m:
            key = m.group(1)
            value = m.group(2).split("#")[0].strip()
            frontmatter[key] = value

    return frontmatter if frontmatter else None


def extract_section(skill_md_path: str, section_name: str) -> Optional[str]:
    """Extract the content of a ## section from a SKILL.md file.

    Returns the text between the named ## heading and the next ## heading,
    or None if the section is not found.
    """
    try:
        with open(skill_md_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return None

    # Find the section heading
    pattern = rf"^## {re.escape(section_name)}\s*$"
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return None

    start = match.end()
    # Find the next ## heading or end of file
    next_heading = re.search(r"^## ", content[start:], re.MULTILINE)
    if next_heading:
        end = start + next_heading.start()
    else:
        end = len(content)

    return content[start:end].strip()


def extract_forbidden_action_count(skill_md_path: str) -> int:
    """Count the number of forbidden action items in a SKILL.md."""
    section = extract_section(skill_md_path, "Forbidden Actions")
    if not section:
        return 0
    # Count lines starting with - or numbered items
    count = 0
    for line in section.splitlines():
        line = line.strip()
        if re.match(r"^[-*]\s+", line) or re.match(r"^\d+\.\s+", line):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Skill data collection
# ---------------------------------------------------------------------------

def collect_skill_data(skills_dir: str) -> Dict[str, Dict[str, Any]]:
    """Collect frontmatter and section info from all SKILL.md files.

    Returns a dict keyed by skill directory name (e.g., "L2-build-system-expert").
    """
    skills: Dict[str, Dict[str, Any]] = {}

    for entry in sorted(Path(skills_dir).iterdir()):
        if not entry.is_dir() or not entry.name.startswith("L"):
            continue

        skill_md = entry / "SKILL.md"
        if not skill_md.exists():
            continue

        fm = parse_skill_frontmatter(str(skill_md))
        if fm is None:
            continue

        # Collect section presence
        sections = [
            "Path Scope", "Trigger Conditions", "Architecture Intelligence",
            "Forbidden Actions", "Tool Calls", "Handoff Rules", "References",
        ]
        section_present = {s: extract_section(str(skill_md), s) is not None for s in sections}

        skills[entry.name] = {
            "frontmatter": fm,
            "sections_present": section_present,
            "forbidden_action_count": extract_forbidden_action_count(str(skill_md)),
            "skill_md_path": str(skill_md),
        }

    return skills


# ---------------------------------------------------------------------------
# Impact analysis
# ---------------------------------------------------------------------------

def analyze_skill_impact(
    skill_name: str,
    skill_data: Dict[str, Any],
    dirty_entry: Optional[Dict[str, Any]],
    version_from: str,
    version_to: str,
) -> Dict[str, Any]:
    """Analyze the migration impact for a single skill.

    Returns a structured dict describing what needs to change.
    """
    fm = skill_data["frontmatter"]
    current_version = fm.get("android_version_tested", "unknown")

    impact: Dict[str, Any] = {
        "skill_name": skill_name,
        "display_name": fm.get("name", skill_name),
        "layer": fm.get("layer", "unknown"),
        "path_scope": fm.get("path_scope", "unknown"),
        "current_android_version": current_version,
        "target_android_version": version_to,
        "needs_update": False,
        "dirty_status": "unknown",
        "dirty_reason": None,
        "affected_paths": [],
        "steward_notes": None,
        "required_updates": [],
    }

    # Check dirty_pages.json status
    if dirty_entry:
        impact["dirty_status"] = dirty_entry.get("status", "unknown")
        impact["dirty_reason"] = dirty_entry.get("dirty_reason")
        impact["affected_paths"] = dirty_entry.get("affected_paths", [])
        impact["steward_notes"] = dirty_entry.get("_steward_note")

    # Determine if this skill needs an update
    is_dirty = impact["dirty_status"] == "dirty"
    version_stale = (
        version_from.lower() in current_version.lower()
        and version_to.lower() not in current_version.lower()
    )

    if is_dirty or version_stale:
        impact["needs_update"] = True

    # Generate required updates checklist
    updates: List[str] = []

    if version_stale:
        updates.append(
            f"Update `android_version_tested` from `{current_version}` to `{version_to}`"
        )

    if is_dirty:
        reason = impact["dirty_reason"] or "unspecified"
        updates.append(f"Address dirty status (reason: {reason})")

    if impact["affected_paths"]:
        updates.append(
            f"Review affected paths: {', '.join(impact['affected_paths'][:5])}"
        )

    if impact["steward_notes"]:
        updates.append(f"Incorporate steward research: {impact['steward_notes'][:120]}...")

    # Architecture Intelligence always needs review on version bump
    if impact["needs_update"] and skill_data["sections_present"].get("Architecture Intelligence"):
        updates.append(
            "Review Architecture Intelligence section for version-specific content"
        )

    # Check forbidden actions adequacy
    if skill_data["forbidden_action_count"] < 5:
        updates.append(
            f"Add forbidden actions (current: {skill_data['forbidden_action_count']}, required: ≥5)"
        )

    impact["required_updates"] = updates
    return impact


# ---------------------------------------------------------------------------
# Report generation — Markdown
# ---------------------------------------------------------------------------

def generate_markdown_report(
    impacts: List[Dict[str, Any]],
    version_from: str,
    version_to: str,
    dirty_pages_baseline: str,
) -> str:
    """Generate a structured markdown migration impact report."""
    today = date.today().isoformat()
    needs_update = [i for i in impacts if i["needs_update"]]
    up_to_date = [i for i in impacts if not i["needs_update"]]

    lines: List[str] = []
    lines.append(f"# Migration Impact Report: {version_from} → {version_to}")
    lines.append("")
    lines.append(f"> **Generated:** {today}")
    lines.append(f"> **Baseline:** {dirty_pages_baseline}")
    lines.append(f"> **Skills analyzed:** {len(impacts)}")
    lines.append(f"> **Skills requiring update:** {len(needs_update)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Skill | Layer | Status | Reason | Updates Required |")
    lines.append("|-------|-------|--------|--------|-----------------|")
    for imp in sorted(impacts, key=lambda x: (0 if x["needs_update"] else 1, x["skill_name"])):
        status_icon = "🔴" if imp["needs_update"] else "🟢"
        reason = imp["dirty_reason"] or "—"
        update_count = len(imp["required_updates"])
        lines.append(
            f"| {imp['display_name']} | {imp['layer']} | "
            f"{status_icon} {imp['dirty_status']} | {reason} | {update_count} |"
        )
    lines.append("")

    # Per-skill details (only for skills needing updates)
    if needs_update:
        lines.append("---")
        lines.append("")
        lines.append("## Per-Skill Refresh Checklist")
        lines.append("")

        for imp in sorted(needs_update, key=lambda x: x["skill_name"]):
            lines.append(f"### {imp['display_name']} (`{imp['skill_name']}`)")
            lines.append("")
            lines.append(f"- **Path scope:** `{imp['path_scope']}`")
            lines.append(
                f"- **Current version:** {imp['current_android_version']} → "
                f"**Target:** {imp['target_android_version']}"
            )
            lines.append(f"- **Dirty reason:** {imp['dirty_reason'] or 'version stale'}")
            lines.append("")

            if imp["affected_paths"]:
                lines.append("**Affected paths:**")
                for p in imp["affected_paths"]:
                    lines.append(f"- `{p}`")
                lines.append("")

            if imp["steward_notes"]:
                lines.append("**Steward research notes:**")
                lines.append(f"> {imp['steward_notes']}")
                lines.append("")

            if imp["required_updates"]:
                lines.append("**Required SKILL.md updates:**")
                for idx, update in enumerate(imp["required_updates"], 1):
                    lines.append(f"- [ ] {update}")
                lines.append("")

    # Up-to-date skills
    if up_to_date:
        lines.append("---")
        lines.append("")
        lines.append("## Skills Not Requiring Update")
        lines.append("")
        for imp in sorted(up_to_date, key=lambda x: x["skill_name"]):
            lines.append(
                f"- **{imp['display_name']}** — "
                f"status: {imp['dirty_status']}, "
                f"version: {imp['current_android_version']}"
            )
        lines.append("")

    # Migration agility metric
    lines.append("---")
    lines.append("")
    lines.append("## Migration Agility Metric")
    lines.append("")
    total = len(impacts)
    if total > 0:
        identified = len(needs_update)
        agility_pct = round(identified / total * 100, 1)
        lines.append(
            f"- **Skills auto-identified as needing refresh:** {identified}/{total} "
            f"({agility_pct}%)"
        )
        lines.append(f"- **Target:** ≥80% migration agility")
        if agility_pct >= 80:
            lines.append(f"- **Status:** PASS")
        else:
            lines.append(f"- **Status:** Below target — manual review recommended")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report generation — JSON
# ---------------------------------------------------------------------------

def generate_json_report(
    impacts: List[Dict[str, Any]],
    version_from: str,
    version_to: str,
    dirty_pages_baseline: str,
) -> str:
    """Generate a JSON migration impact report."""
    needs_update = [i for i in impacts if i["needs_update"]]
    total = len(impacts)

    report = {
        "migration": {
            "from": version_from,
            "to": version_to,
        },
        "generated": date.today().isoformat(),
        "baseline": dirty_pages_baseline,
        "summary": {
            "total_skills": total,
            "skills_needing_update": len(needs_update),
            "migration_agility_pct": round(len(needs_update) / total * 100, 1) if total else 0,
        },
        "skills": impacts,
    }
    return json.dumps(report, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a per-skill migration impact report for an Android version bump."
        ),
    )
    parser.add_argument(
        "--from",
        dest="version_from",
        required="--help-reasons" not in sys.argv,
        help='Source Android version (e.g., "Android 14")',
    )
    parser.add_argument(
        "--to",
        dest="version_to",
        required="--help-reasons" not in sys.argv,
        help='Target Android version (e.g., "Android 15")',
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
        "--output",
        default=None,
        help="Write report to file instead of stdout.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of markdown.",
    )
    parser.add_argument(
        "--dirty-only",
        action="store_true",
        help="Only include skills with dirty status in the report.",
    )
    parser.add_argument(
        "--help-reasons",
        action="store_true",
        help="Show valid dirty reasons and exit.",
    )
    args = parser.parse_args()

    if args.help_reasons:
        print("Valid dirty reasons:")
        for r in sorted([
            "android_version_bump", "path_structure_changed",
            "api_surface_changed", "selinux_policy_restructured",
            "hal_interface_version_bump", "manual_invalidation",
        ]):
            print(f"  - {r}")
        sys.exit(0)

    # Resolve repo root
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    skills_dir = args.skills_dir or str(repo_root / "skills")
    dirty_pages_path = args.dirty_pages or str(repo_root / "memory" / "dirty_pages.json")

    # Validate inputs
    if not os.path.isdir(skills_dir):
        print(f"ERROR: Skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(dirty_pages_path):
        print(f"ERROR: dirty_pages.json not found: {dirty_pages_path}", file=sys.stderr)
        sys.exit(1)

    # Load dirty_pages.json
    with open(dirty_pages_path, "r") as f:
        dirty_pages = json.load(f)

    dirty_skills = dirty_pages.get("skills", {})
    baseline = dirty_pages.get("_android_version_baseline", "unknown")

    # Collect skill data from SKILL.md files
    skill_data = collect_skill_data(skills_dir)

    # Analyze each skill
    impacts: List[Dict[str, Any]] = []
    for skill_name, sdata in sorted(skill_data.items()):
        dirty_entry = dirty_skills.get(skill_name)
        impact = analyze_skill_impact(
            skill_name, sdata, dirty_entry,
            args.version_from, args.version_to,
        )
        if args.dirty_only and not impact["needs_update"]:
            continue
        impacts.append(impact)

    # Generate report
    if args.json:
        report = generate_json_report(
            impacts, args.version_from, args.version_to, baseline,
        )
    else:
        report = generate_markdown_report(
            impacts, args.version_from, args.version_to, baseline,
        )

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
            f.write("\n")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()

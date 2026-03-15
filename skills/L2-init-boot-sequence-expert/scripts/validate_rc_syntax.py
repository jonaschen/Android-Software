#!/usr/bin/env python3
"""
validate_rc_syntax.py — Android init .rc file static validator

Checks .rc files for common mistakes:
  - Services missing 'user' declaration (root is implicit — flag it)
  - Services missing 'seclabel' (SELinux domain not set explicitly)
  - Actions using unknown triggers
  - 'setprop persist.*' before post-fs-data (data partition not mounted)
  - 'socket' declarations missing permission field
  - 'critical' flag on services that also have 'disabled'

Usage:
    python3 validate_rc_syntax.py <file.rc> [file2.rc ...]
    python3 validate_rc_syntax.py vendor/etc/init/my_daemon.rc
    python3 validate_rc_syntax.py $(find vendor/ -name "*.rc")
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass, field


VALID_TRIGGERS = {
    "early-init", "init", "charger", "late-init",
    "post-fs", "post-fs-data", "load_persist_props_action",
    "firmware_mounts_complete", "late-fs", "zygote-start",
    "boot", "nonencrypted", "property:",
    "fs", "early-fs",
}

EARLY_TRIGGERS = {"early-init", "init", "post-fs", "fs", "early-fs"}


@dataclass
class Issue:
    severity: str   # ERROR | WARNING | INFO
    file: str
    line: int
    message: str

    def __str__(self):
        return f"  [{self.severity}] {self.file}:{self.line}: {self.message}"


def validate_rc(path: Path) -> list[Issue]:
    issues = []
    lines = path.read_text(errors="replace").splitlines()

    in_service = False
    service_name = ""
    service_start_line = 0
    service_has_user = False
    service_has_seclabel = False
    service_has_critical = False
    service_has_disabled = False

    current_trigger = None

    def flush_service(end_line: int):
        nonlocal in_service
        if not in_service:
            return
        if not service_has_user:
            issues.append(Issue("WARNING", str(path), service_start_line,
                f"service '{service_name}' has no 'user' declaration — runs as root implicitly"))
        if not service_has_seclabel:
            issues.append(Issue("WARNING", str(path), service_start_line,
                f"service '{service_name}' has no 'seclabel' — SELinux domain not explicitly set"))
        if service_has_critical and service_has_disabled:
            issues.append(Issue("ERROR", str(path), service_start_line,
                f"service '{service_name}' is both 'critical' and 'disabled' — critical has no effect when disabled"))
        in_service = False

    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Skip comments and blank lines
        if not line or line.startswith("#"):
            continue

        # Service block start
        m = re.match(r'^service\s+(\S+)\s+', line)
        if m:
            flush_service(lineno)
            in_service = True
            service_name = m.group(1)
            service_start_line = lineno
            service_has_user = False
            service_has_seclabel = False
            service_has_critical = False
            service_has_disabled = False
            continue

        # Action block start
        m = re.match(r'^on\s+(.+)', line)
        if m:
            flush_service(lineno)
            trigger = m.group(1).strip()
            current_trigger = trigger
            # Check trigger validity (prefix match for property: triggers)
            base_trigger = trigger.split("=")[0].rstrip()
            if base_trigger not in VALID_TRIGGERS and not base_trigger.startswith("property:"):
                issues.append(Issue("WARNING", str(path), lineno,
                    f"unknown trigger '{trigger}' — verify against init documentation"))
            continue

        # Inside a service block
        if in_service:
            if re.match(r'^\s*user\s+', line):
                service_has_user = True
                if "root" in line:
                    issues.append(Issue("INFO", str(path), lineno,
                        f"service '{service_name}' runs as root — verify this is intentional"))
            elif re.match(r'^\s*seclabel\s+', line):
                service_has_seclabel = True
                if "u:r:init:s0" in line:
                    issues.append(Issue("ERROR", str(path), lineno,
                        f"service '{service_name}' uses init's seclabel — must have its own SELinux domain"))
            elif re.match(r'^\s*critical\b', line):
                service_has_critical = True
            elif re.match(r'^\s*disabled\b', line):
                service_has_disabled = True
            elif re.match(r'^\s*socket\s+', line):
                parts = line.split()
                # socket <name> <type> <perm> [user [group]]
                if len(parts) < 4:
                    issues.append(Issue("ERROR", str(path), lineno,
                        f"socket declaration missing permission field: '{line}'"))
            continue

        # Inside an action block — check commands
        if current_trigger:
            # persist.* setprop in early trigger
            if re.match(r'^\s*setprop\s+persist\.', line):
                if current_trigger in EARLY_TRIGGERS:
                    issues.append(Issue("ERROR", str(path), lineno,
                        f"'setprop persist.*' in '{current_trigger}' — /data not mounted yet; persist props will not survive reboot"))

    flush_service(len(lines))
    return issues


def main():
    files = sys.argv[1:]
    if not files:
        print("Usage: validate_rc_syntax.py <file.rc> [file2.rc ...]")
        sys.exit(1)

    all_issues = []
    for f in files:
        path = Path(f)
        if not path.exists():
            print(f"WARNING: file not found: {f}")
            continue
        issues = validate_rc(path)
        all_issues.extend(issues)

    errors = [i for i in all_issues if i.severity == "ERROR"]
    warnings = [i for i in all_issues if i.severity == "WARNING"]
    infos = [i for i in all_issues if i.severity == "INFO"]

    print(f"\n=== validate_rc_syntax.py ===")
    if not all_issues:
        print("  No issues found.")
    else:
        for issue in all_issues:
            print(issue)

    print(f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info(s)")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

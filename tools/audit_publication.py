#!/usr/bin/env python3
"""Fail closed on common publication hazards in tracked candidate files."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"}
FORBIDDEN_NAMES = {".env", "id_rsa", "id_ed25519"}
FORBIDDEN_SUFFIXES = {".db", ".key", ".log", ".p12", ".pem", ".sqlite", ".sqlite3"}


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard"],
        check=True,
        capture_output=True,
        text=True,
    )
    candidates = [root / item for item in result.stdout.splitlines() if item]
    return [path for path in candidates if path.is_file()]


def patterns(extra_terms: list[str]) -> list[tuple[str, re.Pattern[str]]]:
    expressions = [
        ("private-key", re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")),
        ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
        ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
        ("credential-url", re.compile(r"https?://[^\s/:]+:[^\s/@]+@")),
        ("windows-user-path", re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^<>{}\s]+")),
        ("unix-user-path", re.compile(r"/(?:Users|home)/[^/<>{}\s]+/")),
        ("email", re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")),
    ]
    for index, term in enumerate(extra_terms):
        expressions.append((f"deny-term-{index + 1}", re.compile(re.escape(term), re.IGNORECASE)))
    return expressions


def audit(root: Path = ROOT, extra_terms: list[str] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for path in tracked_files(root):
        relative = path.relative_to(root).as_posix()
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append(Finding(relative, "forbidden-artifact"))
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"AGENTS.md", "CLAUDE.md"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding(relative, "non-text-candidate"))
            continue
        for rule, expression in patterns(extra_terms or []):
            for match in expression.finditer(content):
                value = match.group(0)
                if rule == "email" and value.lower().endswith("@example.invalid"):
                    continue
                findings.append(Finding(relative, rule))
                break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deny", action="append", default=[], help="additional case-insensitive term")
    args = parser.parse_args()
    findings = audit(extra_terms=args.deny)
    if findings:
        for finding in findings:
            print(f"ERROR {finding.rule:<20} {finding.path}")
        print(f"publication audit: FAILED ({len(findings)} finding(s))")
        return 1
    print("publication audit: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

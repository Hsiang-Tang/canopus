#!/usr/bin/env python3
"""Screen a portable knowledge candidate before a human reviews it.

Portable knowledge must be de-identified and human-reviewed before it is
promoted. This tool does the mechanical half so the reviewer can spend
attention on meaning:

* structure: every ``## `` section of the template is present, non-empty,
  and no longer the template's own guidance text; every boundary checkbox
  is ticked (``- [x]``);
* denylist: paths, URLs, emails, IPs, ticket or issue references, tokens,
  private keys, plus caller terms (``--deny``) and a machine-local term
  file (``--deny-file``, one term per line; keep it out of Git).

Documentation-reserved values (``example.com``/``.org``/``.net``,
``*.example``, ``*.invalid``, 192.0.2.x, 198.51.100.x, 203.0.113.x) are
allowed. Passing this screen never replaces the human review.

    python3 tools/check_knowledge_candidate.py CANDIDATE.md \\
        [--template templates/portable-knowledge-candidate.md] [--deny TERM] [--deny-file FILE]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "portable-knowledge-candidate.md"
DEFAULT_SECTIONS = (
    "Generic problem", "Reusable lesson", "Applies when", "Does not apply when",
    "Validation", "Failure modes and rollback", "Boundary confirmation",
)
SAFE_HOST = re.compile(r"(?:^|\.)(?:example\.(?:com|org|net)|[\w-]+\.example|[\w-]+\.invalid|example\.invalid)$",
                       re.IGNORECASE)
SAFE_IP = re.compile(r"^(?:192\.0\.2|198\.51\.100|203\.0\.113)\.\d{1,3}$")
PATTERNS = {
    "URL": re.compile(r"\b(?:https?|ssh|git)://([^/\s:@]+@)?([^/\s:]+)[^\s)]*", re.IGNORECASE),
    "SSH remote": re.compile(r"\b[\w.-]+@([\w.-]+):[\w./-]+"),
    "email address": re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"),
    "IPv4 address": re.compile(r"(?<![\d.])((?:\d{1,3}\.){3}\d{1,3})(?![\d.])"),
    "Windows path": re.compile(r"\b[A-Za-z]:[\\/][^\s]+"),
    "home path": re.compile(r"(?:^|[\s`'\"(])(/(?:Users|home|mnt)/)[^\s]*", re.MULTILINE),
    "ticket id": re.compile(r"\b(?!(?:SHA|UTF|ISO|RFC|CVE|TLS|HTTP|IPV|X)-)[A-Z][A-Z0-9]{1,9}-\d+\b"),
    "issue reference": re.compile(r"(?<![\w&])#\d{1,6}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|glpat-[\w-]{20,}|AKIA[0-9A-Z]{16}|"
                        r"xox[abprs]-[\w-]{10,}|sk-[A-Za-z0-9_-]{20,})"),
}


def sections(text: str) -> dict[str, str]:
    """Map each '## ' heading to its body (text up to the next '## ')."""
    result: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            result[current] = ""
        elif current is not None:
            result[current] += line + "\n"
    return {name: body.strip() for name, body in result.items()}


def structure_findings(text: str, template: str | None) -> list[str]:
    expected = sections(template) if template else {name: "" for name in DEFAULT_SECTIONS}
    actual = sections(text)
    problems = []
    for name, guidance in expected.items():
        body = actual.get(name)
        if body is None:
            problems.append(f"missing section '## {name}'")
        elif not body:
            problems.append(f"section '## {name}' is empty")
        elif guidance and body == guidance and "- [" not in guidance:
            problems.append(f"section '## {name}' still holds the template guidance text")
    for name, body in actual.items():
        unticked = re.findall(r"^\s*- \[ \]\s*(.+)$", body, re.MULTILINE)
        problems.extend(f"unticked boundary check in '## {name}': {item}" for item in unticked)
    if re.search(r"<(?:TODO|describe|fill)[^>]*>|\bTODO\b|\bTBD\b", text, re.IGNORECASE):
        problems.append("unfilled placeholder (TODO, TBD, or <...>)")
    return problems


def denylist_findings(text: str, terms: list[str]) -> list[str]:
    terms = [term for term in terms if term.strip()]
    problems = []
    for number, line in enumerate(text.splitlines(), 1):
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(line):
                if label in {"URL", "email address", "SSH remote"} and SAFE_HOST.search(match.group(match.lastindex or 0)):
                    continue
                if label == "IPv4 address" and SAFE_IP.match(match.group(1)):
                    continue
                problems.append(f"line {number}: {label}")
                break
        lowered = line.lower()
        problems.extend(f"line {number}: denied term {term!r}" for term in terms if term.lower() in lowered)
    return problems


def screen(text: str, template: str | None = None, terms: list[str] | None = None) -> list[str]:
    return structure_findings(text, template) + denylist_findings(text, terms or [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Screen a portable knowledge candidate.")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    parser.add_argument("--deny", action="append", default=[], help="case-insensitive term; repeatable")
    parser.add_argument("--deny-file", type=Path, help="machine-local file with one term per line")
    args = parser.parse_args(argv)
    try:
        text = args.candidate.read_text(encoding="utf-8")
        template = args.template.read_text(encoding="utf-8") if args.template.is_file() else None
        terms = list(args.deny)
        if args.deny_file:
            terms += [line.strip() for line in args.deny_file.read_text(encoding="utf-8").splitlines()
                      if line.strip() and not line.startswith("#")]
    except (OSError, UnicodeDecodeError) as error:
        print(f"ERROR cannot read input: {error}", file=sys.stderr)
        return 2
    problems = screen(text, template, terms)
    for problem in problems:
        print(f"REJECT {problem}")
    if problems:
        print(f"knowledge candidate: REJECTED ({len(problems)} finding(s)); keep it local and abstract further")
        return 1
    print("knowledge candidate: automated screen passed; human ownership and disclosure review still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

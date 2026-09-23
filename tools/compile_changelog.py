#!/usr/bin/env python3
"""Fold changelog.d/ fragments into CHANGELOG.md.

Parallel branches that all edit the same "Unreleased" lines conflict on
every merge. Instead, each change adds one fragment file, and this tool
compiles them in one step:

    changelog.d/<slug>.<category>.md    category: added|changed|fixed|removed|security|deprecated

A fragment holds one or more bullets (``- text``; continuation lines are
indented). Fragments are inserted under ``## Unreleased`` -> ``### <Category>``
(created when missing) in filename order, then deleted. All fragments are
validated before anything is written, so a bad fragment changes nothing.

    python3 tools/compile_changelog.py [--root DIR] [--dry-run] [--check]

``--check`` exits 1 when fragments are pending (useful before a release).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ("added", "changed", "deprecated", "removed", "fixed", "security")
UNRELEASED = "## Unreleased"
IGNORED = {"README.md"}


class FragmentError(ValueError):
    """A fragment or changelog that cannot be compiled safely."""


def pending(fragments_dir: Path) -> list[Path]:
    if not fragments_dir.is_dir():
        return []
    return sorted(path for path in fragments_dir.glob("*.md") if path.name not in IGNORED)


def parse_fragment(path: Path) -> tuple[str, list[str]]:
    parts = path.name.split(".")
    if len(parts) != 3 or parts[1] not in CATEGORIES or not parts[0]:
        raise FragmentError(f"{path.name}: name must be <slug>.<category>.md with category in "
                            f"{', '.join(CATEGORIES)}")
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").strip("\n").splitlines()]
    if not lines or not lines[0].startswith("- "):
        raise FragmentError(f"{path.name}: must start with a '- ' bullet")
    for number, line in enumerate(lines, 1):
        if line and not (line.startswith("- ") or line.startswith("  ")):
            raise FragmentError(f"{path.name}:{number}: expected '- ' bullet or indented continuation")
    return parts[1], [line for line in lines if line]


def merge(changelog: str, entries: dict[str, list[str]]) -> str:
    lines = changelog.splitlines() if changelog.strip() else ["# Changelog"]
    if UNRELEASED not in [line.strip() for line in lines]:
        first_release = next((i for i, line in enumerate(lines) if line.startswith("## ")), len(lines))
        insert = [UNRELEASED, ""]
        if first_release == len(lines):
            insert = ([""] if lines and lines[-1].strip() else []) + insert[:1]
        lines[first_release:first_release] = insert
    start = next(i for i, line in enumerate(lines) if line.strip() == UNRELEASED)
    for category in CATEGORIES:
        if category not in entries:
            continue
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        heading = f"### {category.capitalize()}"
        position = next((i for i in range(start + 1, end) if lines[i].strip() == heading), None)
        if position is None:
            # New subsection at the end of the Unreleased section.
            while end > start + 1 and not lines[end - 1].strip():
                end -= 1
            block = ["", heading, ""] + entries[category]
            lines[end:end] = block + ([""] if end < len(lines) and lines[end].strip() else [])
            continue
        stop = next((i for i in range(position + 1, end) if lines[i].startswith("#")), end)
        while stop > position + 1 and not lines[stop - 1].strip():
            stop -= 1
        lines[stop:stop] = entries[category]
    return "\n".join(lines).rstrip("\n") + "\n"


def compile_fragments(root: Path, dry_run: bool = False) -> tuple[list[Path], str]:
    fragments = pending(root / "changelog.d")
    changelog_path = root / "CHANGELOG.md"
    before = changelog_path.read_text(encoding="utf-8") if changelog_path.is_file() else ""
    if not fragments:
        return [], before
    entries: dict[str, list[str]] = {}
    for fragment in fragments:
        category, lines = parse_fragment(fragment)
        entries.setdefault(category, []).extend(lines)
    after = merge(before, entries)
    if not dry_run:
        temporary = changelog_path.with_suffix(".md.tmp")
        temporary.write_text(after, encoding="utf-8")
        temporary.replace(changelog_path)
        for fragment in fragments:
            fragment.unlink()
    return fragments, after


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile changelog.d fragments into CHANGELOG.md.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true", help="print the result; change nothing")
    parser.add_argument("--check", action="store_true", help="exit 1 if fragments are pending")
    args = parser.parse_args(argv)
    try:
        if args.check:
            waiting = pending(args.root / "changelog.d")
            for fragment in waiting:
                parse_fragment(fragment)
            print(f"{len(waiting)} pending changelog fragment(s)")
            return 1 if waiting else 0
        compiled, text = compile_fragments(args.root, args.dry_run)
    except FragmentError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2
    if not compiled:
        print("no pending changelog fragments")
    elif args.dry_run:
        print(text, end="")
    else:
        print(f"compiled {len(compiled)} fragment(s) into CHANGELOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

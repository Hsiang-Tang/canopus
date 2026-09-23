#!/usr/bin/env python3
"""Run the complete Canopus reference validation pipeline locally."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def command_set(extra_deny_terms: list[str]) -> list[list[str]]:
    publication_command = [sys.executable, "tools/audit_publication.py"]
    for term in extra_deny_terms:
        publication_command.extend(["--deny", term])
    return [
        [sys.executable, "tools/check_control_plane.py"],
        [
            sys.executable,
            "tools/workspace_doctor.py",
            "--manifest",
            "examples/workspace.toml",
        ],
        publication_command,
        [sys.executable, "tools/render_diagrams.py", "--check"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "-m", "compileall", "-q", "tools", "tests"],
        ["git", "diff", "--check"],
        ["git", "diff", "--cached", "--check"],
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--deny",
        action="append",
        default=[],
        help="additional case-insensitive publication term; may be repeated",
    )
    args = parser.parse_args()
    for command in command_set(args.deny):
        print(f"+ {' '.join(command)}", flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
    print("local validation pipeline: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

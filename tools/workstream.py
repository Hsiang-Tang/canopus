#!/usr/bin/env python3
"""Check parallel workstream declarations for collisions before work starts.

Each workstream is one TOML file (default directory: ``workstreams/``)::

    id = "api-pagination"
    owner_role = "executor"          # who is accountable, as a role
    writer = "agent-a"               # exactly one writer for this checkout
    status = "active"                # planned|active|blocked|done|abandoned
    branch = "ws/api-pagination"
    worktree = "../wt-api-pagination"
    mutation_scope = ["src/api/**", "tests/api/**"]
    depends_on = []

``check`` reports, for every live (planned/active/blocked) workstream:

* overlapping mutation scopes (conservative glob-overlap test);
* a branch or worktree shared by two workstreams (one writer per checkout);
* a writer that is not exactly one name;
* missing dependencies, dependencies on abandoned work, and cycles.

``files --id ID PATH...`` (or paths on stdin, e.g. from
``git diff --name-only``) reports changed paths outside that workstream's
declared scope. This is a coordination check, not a lock or scheduler.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _toml  # noqa: E402

STATUSES = {"planned", "active", "blocked", "done", "abandoned"}
LIVE = {"planned", "active", "blocked"}
REQUIRED = {"id": str, "owner_role": str, "writer": str, "status": str, "branch": str,
            "worktree": str, "mutation_scope": list}
WILDCARDS = set("*?[")


def load(directory: Path) -> tuple[list[dict[str, Any]], list[str]]:
    streams, errors = [], []
    if not directory.is_dir():
        return [], [f"{directory}: workstream directory not found"]
    for path in sorted(directory.glob("*.toml")):
        try:
            data = _toml.read_toml(path)
        except ValueError as error:
            errors.append(f"{path.name}: invalid TOML ({error})")
            continue
        problems = validate(data)
        errors.extend(f"{path.name}: {problem}" for problem in problems)
        if not problems:
            data.setdefault("depends_on", [])
            data["_file"] = path.name
            streams.append(data)
    ids = [stream["id"] for stream in streams]
    for duplicate in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"duplicate workstream id {duplicate!r}")
    return streams, errors


def validate(data: dict[str, Any]) -> list[str]:
    problems = []
    for key, kind in REQUIRED.items():
        if key == "writer" and isinstance(data.get(key), list):
            problems.append(f"one-writer violation: writer lists {len(data[key])} names; declare exactly one")
        elif not isinstance(data.get(key), kind) or (kind is str and not data[key].strip()):
            problems.append(f"{key} must be a non-empty {kind.__name__}")
    if isinstance(data.get("status"), str) and data["status"] not in STATUSES:
        problems.append(f"status must be one of {', '.join(sorted(STATUSES))}")
    depends = data.get("depends_on", [])
    if not isinstance(depends, list) or not all(isinstance(item, str) for item in depends):
        problems.append("depends_on must be a list of workstream ids")
    for glob in data.get("mutation_scope") or []:
        if not isinstance(glob, str) or not glob or glob.startswith("/") or ".." in PurePosixPath(glob).parts \
                or "\\" in glob:
            problems.append(f"mutation_scope entry {glob!r} must be a relative POSIX glob")
    if isinstance(data.get("mutation_scope"), list) and not data["mutation_scope"]:
        problems.append("mutation_scope must not be empty")
    return problems


# ------------------------------------------------------------- glob overlap

def _parts(glob: str) -> list[str]:
    glob = glob + "**" if glob.endswith("/") else glob
    return [part for part in glob.split("/") if part and part != "."]


def _segment_overlap(a: str, b: str) -> bool:
    wild_a, wild_b = bool(WILDCARDS & set(a)), bool(WILDCARDS & set(b))
    if not wild_a:
        return fnmatch.fnmatchcase(a, b) if wild_b else a == b
    if not wild_b:
        return fnmatch.fnmatchcase(b, a)
    return True  # two wildcard segments: assume they can meet (conservative)


def _overlap(a: list[str], b: list[str]) -> bool:
    if not a or not b:
        return all(part == "**" for part in a + b)
    if a[0] == "**":
        return _overlap(a[1:], b) or _overlap(a, b[1:])
    if b[0] == "**":
        return _overlap(a, b[1:]) or _overlap(a[1:], b)
    return _segment_overlap(a[0], b[0]) and _overlap(a[1:], b[1:])


def globs_overlap(a: str, b: str) -> bool:
    """True when some path could match both globs. May over-report, never under-report."""
    return _overlap(_parts(a), _parts(b))


def in_scope(path: str, scope: list[str]) -> bool:
    return any(globs_overlap(path, glob) for glob in scope)


# ------------------------------------------------------------------- checks

def check(streams: list[dict[str, Any]]) -> list[str]:
    errors = []
    live = [stream for stream in streams if stream["status"] in LIVE]
    for index, first in enumerate(live):
        for second in live[index + 1:]:
            pair = f"{first['id']} / {second['id']}"
            overlaps = sorted({f"{a} ~ {b}" for a in first["mutation_scope"]
                               for b in second["mutation_scope"] if globs_overlap(a, b)})
            if overlaps:
                errors.append(f"scope collision {pair}: {', '.join(overlaps)}")
            if first["branch"] == second["branch"]:
                errors.append(f"shared branch {first['branch']!r}: {pair}")
            if PurePosixPath(first["worktree"]) == PurePosixPath(second["worktree"]):
                errors.append(f"one-writer violation: worktree {first['worktree']!r} shared by {pair}")
    by_id = {stream["id"]: stream for stream in streams}
    for stream in live:
        for dependency in stream["depends_on"]:
            if dependency not in by_id:
                errors.append(f"{stream['id']}: depends on missing workstream {dependency!r}")
            elif by_id[dependency]["status"] == "abandoned":
                errors.append(f"{stream['id']}: depends on abandoned workstream {dependency!r}")
    errors.extend(f"dependency cycle: {' -> '.join(cycle)}" for cycle in cycles(by_id))
    return errors


def cycles(by_id: dict[str, dict[str, Any]]) -> list[list[str]]:
    found, done = [], set()

    def visit(node: str, path: list[str]) -> None:
        if node in path:
            cycle = path[path.index(node):] + [node]
            if not any(set(cycle) == set(other) for other in found):
                found.append(cycle)
            return
        if node in done or node not in by_id:
            return
        for dependency in by_id[node]["depends_on"]:
            visit(dependency, path + [node])
        done.add(node)

    for node in sorted(by_id):
        visit(node, [])
    return found


def out_of_scope(stream: dict[str, Any], paths: list[str]) -> list[str]:
    return [path for path in paths if path and not in_scope(path, stream["mutation_scope"])]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Workstream collision checks.")
    parser.add_argument("--dir", type=Path, default=Path("workstreams"))
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    commands.add_parser("list")
    files_cmd = commands.add_parser("files")
    files_cmd.add_argument("--id", required=True)
    files_cmd.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)

    streams, errors = load(args.dir)
    if args.command == "list":
        for stream in streams:
            print(f"{stream['id']:<24} {stream['status']:<10} {stream['writer']:<12} {stream['branch']}")
    elif args.command == "check":
        errors += check(streams)
    elif args.command == "files":
        stream = next((s for s in streams if s["id"] == args.id), None)
        if stream is None:
            errors.append(f"unknown workstream {args.id!r}")
        else:
            paths = args.paths or [line.strip() for line in sys.stdin if line.strip()]
            errors += [f"{args.id}: {path} is outside the declared mutation_scope"
                       for path in out_of_scope(stream, paths)]
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "workstreams": len(streams)}, indent=2))
    else:
        for error in errors:
            print(f"ERROR {error}")
        if args.command != "list":
            print(f"workstream {args.command}: {'OK' if not errors else f'FAILED ({len(errors)})'}"
                  f" · {len(streams)} workstream(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

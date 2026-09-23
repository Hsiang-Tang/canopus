#!/usr/bin/env python3
"""Replay a synthetic task scenario through the bounded convergence contract.

Usage:
    python3 tools/convergence_demo.py examples/scenarios/runaway-fix-loop.json
    python3 tools/convergence_demo.py examples/scenarios/scope-drift.json --lang zh-TW
    python3 tools/convergence_demo.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import convergence  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "examples" / "scenarios"


def replay(path: Path, lang: str, view: str, trace: bool) -> convergence.TaskState:
    data = json.loads(path.read_text(encoding="utf-8"))
    task = convergence.TaskState(envelope=convergence.Envelope.from_dict(data["envelope"]))
    print(f"=== {data['title']} ===")
    print(data["story"])
    print()
    for event in data["events"]:
        before = task.state
        convergence.apply_event(task, event)
        if trace:
            label = event.get("item") or event.get("what") or event.get("family") or event.get("summary") or ""
            marker = f"  -> {task.state}" if task.state != before else ""
            print(f"  [{event['kind']:<15}] {label}{marker}")
    if trace:
        print()
    if view in {"owner", "both"}:
        print(convergence.render_owner(task, lang))
        print()
    if view in {"agent", "both"}:
        print(convergence.render_agent(task))
        print()
    return task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenario", nargs="?", type=Path)
    parser.add_argument("--all", action="store_true", help="replay every bundled scenario")
    parser.add_argument("--lang", choices=sorted(convergence.LABELS), default="en")
    parser.add_argument("--view", choices=("owner", "agent", "both"), default="both")
    parser.add_argument("--no-trace", action="store_true")
    args = parser.parse_args(argv)
    if args.all:
        paths = sorted(SCENARIOS.glob("*.json"))
    elif args.scenario:
        paths = [args.scenario]
    else:
        parser.error("give a scenario path or --all")
    for path in paths:
        replay(path, args.lang, args.view, not args.no_trace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

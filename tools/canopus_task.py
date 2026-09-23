#!/usr/bin/env python3
"""Durable Canopus task records built on tools/convergence.py.

A task's identity is its ID, not the chat session, engine, or machine that
happens to be working on it. Each task is one JSON file holding the frozen
envelope and the append-only event log. The current state is never stored:
it is recomputed by replaying the log through ``convergence.run``, so every
fresh session derives exactly the same Owner Footer and Agent Handoff.

State directory: ``$CANOPUS_STATE_DIR`` or ``~/.canopus/state`` (tasks/<id>.json).

    admit      --task ID --envelope FILE.json [--readmit] [--latch-session SID]
    event      --task ID --json '{"kind": "accept", "item": "AC1"}'
    checkpoint --task ID [--note TEXT]
    footer     --task ID [--lang en|zh-TW]
    handoff    --task ID
    status     [--task ID] [--json]
    close      --task ID --outcome complete|handoff|blocked|abandoned

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import convergence  # noqa: E402

SCHEMA = 1
OUTCOMES = ("complete", "handoff", "blocked", "abandoned")
TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class TaskError(ValueError):
    """A task-record operation that must not proceed."""


# ------------------------------------------------------------------ storage

def state_dir() -> Path:
    override = os.environ.get("CANOPUS_STATE_DIR")
    return Path(override).expanduser() if override else Path.home() / ".canopus" / "state"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_stamp(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def task_path(task_id: str, root: Path | None = None) -> Path:
    if not TASK_ID.match(task_id):
        raise TaskError(f"invalid task id {task_id!r}: use letters, digits, '.', '_', '-'")
    return (root or state_dir()) / "tasks" / f"{task_id}.json"


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Atomic write: a crash leaves either the old or the new file, never half."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load(task_id: str, root: Path | None = None) -> dict[str, Any]:
    path = task_path(task_id, root)
    if not path.is_file():
        raise TaskError(f"task {task_id} is not admitted")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise TaskError(f"task {task_id} record is corrupt ({error}); restore it from backup") from error
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        raise TaskError(f"task {task_id} record has an unsupported schema")
    return record


def replay(record: dict[str, Any]) -> convergence.TaskState:
    return convergence.run(record["envelope"], [entry["event"] for entry in record["events"]])


# --------------------------------------------------------------- operations

def admit(task_id: str, envelope: dict[str, Any], *, readmit: bool = False,
          root: Path | None = None, now: datetime | None = None) -> tuple[str, dict[str, Any]]:
    """Admit a new task, resume an identical one, or re-admit with a new envelope.

    Returns (``admitted`` | ``resumed`` | ``readmitted``, record).
    """
    if not isinstance(envelope, dict):
        raise TaskError("an envelope must be a JSON object")
    convergence.Envelope.from_dict(envelope)  # validate before touching disk
    moment = stamp(now or utc_now())
    path = task_path(task_id, root)
    if not path.exists():
        record = {"schema": SCHEMA, "task_id": task_id, "envelope": envelope, "events": [],
                  "admitted_at": moment, "closed_at": None, "outcome": None, "rounds": []}
        write_json(path, record)
        return "admitted", record
    record = load(task_id, root)
    if record["envelope"] == envelope and record["closed_at"] is None:
        return "resumed", record
    if not readmit:
        reason = "is closed" if record["closed_at"] else "has a different frozen envelope"
        raise TaskError(f"task {task_id} {reason}; widening needs an explicit --readmit")
    # Re-admission: archive the old round, keep acceptance still in the new envelope.
    keep = set(envelope["acceptance"])
    carried = [entry for entry in record["events"]
               if entry["event"].get("kind") == "accept" and entry["event"].get("item") in keep]
    record["rounds"].append({"envelope": record["envelope"], "events": record["events"],
                             "outcome": record["outcome"], "ended_at": moment})
    record.update(envelope=envelope, events=carried, closed_at=None, outcome=None)
    write_json(path, record)
    return "readmitted", record


def add_event(task_id: str, event: dict[str, Any], *, root: Path | None = None,
              now: datetime | None = None) -> convergence.TaskState:
    """Validate an event by replaying it, then append it durably."""
    record = load(task_id, root)
    if record["closed_at"]:
        raise TaskError(f"task {task_id} is closed ({record['outcome']})")
    if not isinstance(event, dict):
        raise TaskError("an event must be a JSON object")
    before = replay(record)
    if before.state in convergence.STOPPING_STATES:
        raise TaskError(f"task {task_id} is {before.state}; the owner must close or re-admit it")
    events = [entry["event"] for entry in record["events"]] + [event]
    try:
        state = convergence.run(record["envelope"], events)
    except KeyError as error:
        raise TaskError(f"event {event.get('kind')!r} is missing field {error}") from error
    except convergence.ConvergenceError as error:
        raise TaskError(str(error)) from error
    record["events"].append({"at": stamp(now or utc_now()), "event": event})
    write_json(task_path(task_id, root), record)
    return state


def checkpoint(task_id: str, note: str = "", **kwargs: Any) -> convergence.TaskState:
    event: dict[str, Any] = {"kind": "checkpoint"}
    if note:
        event["note"] = note
    return add_event(task_id, event, **kwargs)


def close(task_id: str, outcome: str, *, root: Path | None = None,
          now: datetime | None = None) -> dict[str, Any]:
    if outcome not in OUTCOMES:
        raise TaskError(f"outcome must be one of {', '.join(OUTCOMES)}")
    record = load(task_id, root)
    if record["closed_at"]:
        if record["outcome"] == outcome:
            return record  # idempotent
        raise TaskError(f"task {task_id} is already closed as {record['outcome']}")
    state = replay(record)
    if outcome == "complete" and state.state != "COMPLETE":
        raise TaskError(f"cannot close as complete: state is {state.state}, "
                        f"remaining {', '.join(state.remaining)}")
    record.update(closed_at=stamp(now or utc_now()), outcome=outcome)
    write_json(task_path(task_id, root), record)
    return record


# ---------------------------------------------------------------- rendering

def elapsed_seconds(record: dict[str, Any], now: datetime | None = None) -> int:
    end = parse_stamp(record["closed_at"]) if record["closed_at"] else (now or utc_now())
    return max(0, int((end - parse_stamp(record["admitted_at"])).total_seconds()))


def human_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    return f"{hours}h {remainder // 60:02d}m" if hours else f"{remainder // 60}m {remainder % 60:02d}s"


def footer(task_id: str, lang: str = "en", *, root: Path | None = None,
           now: datetime | None = None) -> str:
    """Owner Footer from convergence.render_owner plus elapsed time.

    The extra rows go before the final Decision row so the Decision row stays
    last, which is what the Stop-hook latch checks for.
    """
    record = load(task_id, root)
    rows = convergence.render_owner(replay(record), lang).splitlines()
    zh = lang == "zh-TW"
    extra = [f"{'耗時' if zh else 'Elapsed'} │ {human_duration(elapsed_seconds(record, now))}"]
    if record["outcome"]:
        extra.append(f"{'結案' if zh else 'Closed'} │ {record['outcome']}")
    return "\n".join(rows[:-1] + extra + rows[-1:])


def handoff(task_id: str, *, root: Path | None = None, now: datetime | None = None) -> str:
    record = load(task_id, root)
    lines = convergence.render_agent(replay(record)).splitlines()
    notes = [entry["event"]["note"] for entry in record["events"]
             if entry["event"].get("kind") == "checkpoint" and entry["event"].get("note")]
    lines += [
        f"Admitted: {record['admitted_at']} | elapsed {human_duration(elapsed_seconds(record, now))}"
        f" | events {len(record['events'])} | re-admissions {len(record['rounds'])}",
        f"Outcome: {record['outcome'] or 'open'}",
        f"Last checkpoint: {notes[-1] if notes else 'none'}",
        f"Resume: python3 tools/canopus_task.py status --task {task_id}",
    ]
    return "\n".join(lines)


def summary(task_id: str, *, root: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    record = load(task_id, root)
    state = replay(record)
    return {
        "task_id": task_id, "task_ref": state.envelope.task_ref, "state": state.state,
        "accepted": len(state.accepted), "total": len(state.envelope.acceptance),
        "remaining": state.remaining, "open_blockers": sorted(state.open_blockers),
        "deferred_findings": state.deferred_findings, "reason": state.reason,
        "admitted_at": record["admitted_at"], "closed_at": record["closed_at"],
        "outcome": record["outcome"], "elapsed_seconds": elapsed_seconds(record, now),
    }


def list_tasks(root: Path | None = None) -> list[str]:
    directory = (root or state_dir()) / "tasks"
    return sorted(path.stem for path in directory.glob("*.json")) if directory.is_dir() else []


# ---------------------------------------------------------------------- CLI

def _read_envelope(path: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TaskError(f"cannot read envelope {path}: {error}") from error
    # Accept either a bare envelope or a scenario file with an "envelope" key.
    return data.get("envelope", data) if isinstance(data, dict) else data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    admit_cmd = commands.add_parser("admit")
    admit_cmd.add_argument("--task", required=True)
    admit_cmd.add_argument("--envelope", required=True)
    admit_cmd.add_argument("--readmit", action="store_true")
    admit_cmd.add_argument("--latch-session", help="also set the footer latch for this session")
    event_cmd = commands.add_parser("event")
    event_cmd.add_argument("--task", required=True)
    event_cmd.add_argument("--json", required=True, dest="payload")
    checkpoint_cmd = commands.add_parser("checkpoint")
    checkpoint_cmd.add_argument("--task", required=True)
    checkpoint_cmd.add_argument("--note", default="")
    footer_cmd = commands.add_parser("footer")
    footer_cmd.add_argument("--task", required=True)
    footer_cmd.add_argument("--lang", default="en", choices=sorted(convergence.LABELS))
    commands.add_parser("handoff").add_argument("--task", required=True)
    status_cmd = commands.add_parser("status")
    status_cmd.add_argument("--task")
    status_cmd.add_argument("--json", action="store_true")
    close_cmd = commands.add_parser("close")
    close_cmd.add_argument("--task", required=True)
    close_cmd.add_argument("--outcome", required=True, choices=OUTCOMES)
    args = parser.parse_args(argv)

    try:
        if args.command == "admit":
            result, record = admit(args.task, _read_envelope(args.envelope), readmit=args.readmit)
            print(f"{result} {args.task} at {record['admitted_at']}")
            if args.latch_session:
                import footer_latch
                footer_latch.set_latch(args.latch_session, args.task)
                print(f"footer latch set for session {args.latch_session}")
        elif args.command in {"event", "checkpoint"}:
            if args.command == "event":
                try:
                    event = json.loads(args.payload)
                except json.JSONDecodeError as error:
                    raise TaskError(f"--json is not valid JSON: {error}") from error
                state = add_event(args.task, event)
            else:
                state = checkpoint(args.task, args.note)
            print(f"{args.task}: {state.state} {len(state.accepted)}/{len(state.envelope.acceptance)}"
                  + (f" ({state.reason})" if state.reason else ""))
        elif args.command == "footer":
            print(footer(args.task, args.lang))
        elif args.command == "handoff":
            print(handoff(args.task))
        elif args.command == "status":
            ids = [args.task] if args.task else list_tasks()
            rows = [summary(task_id) for task_id in ids]
            if args.json:
                print(json.dumps(rows[0] if args.task else rows, indent=2, ensure_ascii=False))
            elif not rows:
                print("no admitted tasks")
            for row in [] if args.json else rows:
                print(f"{row['task_id']:<24} {row['state']:<14} {row['accepted']}/{row['total']}  "
                      f"{row['outcome'] or 'open':<9} {human_duration(row['elapsed_seconds'])}")
        elif args.command == "close":
            record = close(args.task, args.outcome)
            print(f"closed {args.task} as {record['outcome']} at {record['closed_at']}")
    except (TaskError, convergence.ConvergenceError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

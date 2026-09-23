#!/usr/bin/env python3
"""Deterministic Owner Footer enforcement for Claude Code sessions.

Asking a model to remember "end every substantial turn with the footer" is a
prompt rule; it fails silently. This module replaces it with a one-way latch
per session plus a Stop hook:

    CHAT --set--> MANAGED_TASK --(SessionEnd)--> cleared

Once a session is latched (at task admission), every turn that hands control
back to the owner must end with a Canopus Owner Footer: a final block whose
header line starts with ``Canopus · `` and whose last row is ``Decision │ ...``
(or ``決策 │ ...``). Nothing in this module can move a latched session back
to CHAT except ``end``.

    set    --session SID --task ID    latch a session (idempotent, one-way)
    stop                              Stop-hook entrypoint; hook JSON on stdin
    end    [--session SID]            SessionEnd entrypoint; clears the latch
    status [--session SID]            show one latch or all latches

Latch files live under ``$CANOPUS_STATE_DIR/latches/`` (default
``~/.canopus/state/latches/``). ``--session`` may be omitted when
``CANOPUS_SESSION_ID`` is set.

The Stop hook fails open for unlatched sessions and unreadable payloads (it
cannot tell whose turn it is), fails closed for latched sessions (a missing
or unreadable response is treated as having no footer), and never blocks
twice in a row: when Claude Code reports ``stop_hook_active`` the turn is
already a retry caused by this hook, so it is allowed to end.
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

SESSION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
HEADER = "Canopus · "
DECISION_ROW = re.compile(r"^(?:Decision|決策) │ \S")
FENCE = re.compile(r"^(?:```|~~~)[\w-]*$")


class LatchError(ValueError):
    """An invalid latch operation."""


def latch_dir() -> Path:
    override = os.environ.get("CANOPUS_STATE_DIR")
    base = Path(override).expanduser() if override else Path.home() / ".canopus" / "state"
    return base / "latches"


def latch_path(session_id: str) -> Path:
    if not isinstance(session_id, str) or not SESSION_ID.match(session_id):
        raise LatchError(f"invalid session id {session_id!r}")
    return latch_dir() / f"{session_id}.json"


def read_latch(session_id: str) -> dict[str, Any] | None:
    path = latch_path(session_id)
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # A damaged latch file still means the session was latched: fail closed.
        return {"session_id": session_id, "tasks": [], "corrupt": True}
    return record if isinstance(record, dict) else {"session_id": session_id, "tasks": [], "corrupt": True}


def set_latch(session_id: str, task_id: str) -> dict[str, Any]:
    """One-way CHAT -> MANAGED_TASK. Re-setting keeps the original set_at."""
    path = latch_path(session_id)
    record = read_latch(session_id)
    if record is None or record.get("corrupt"):
        record = {"session_id": session_id, "state": "MANAGED_TASK", "tasks": [],
                  "set_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if task_id not in record["tasks"]:
        record["tasks"].append(task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    return record


def clear_latch(session_id: str) -> bool:
    path = latch_path(session_id)
    if path.is_file():
        path.unlink()
        return True
    return False


# ---------------------------------------------------------- footer detection

def footer_is_final_block(text: str) -> tuple[bool, str]:
    """Return (ok, reason). The footer must be the last block of the response.

    A surrounding Markdown code fence is tolerated; blank lines inside the
    footer block, or any text after the Decision row, are not.
    """
    lines = [line.rstrip() for line in (text or "").rstrip().splitlines()]
    while lines and (not lines[-1] or FENCE.match(lines[-1])):
        lines.pop()
    if not lines:
        return False, "the final response is empty"
    if not DECISION_ROW.match(lines[-1]):
        return False, "the final line is not a 'Decision │' row"
    for index in range(len(lines) - 1, -1, -1):
        line = lines[index]
        if line.startswith(HEADER) and len(line) > len(HEADER):
            return True, "footer is the final block"
        if not line or FENCE.match(line):
            break
    return False, "no 'Canopus · <task>' header directly above the Decision row"


def last_assistant_text(transcript_path: str | None) -> str:
    """Best-effort text of the last assistant message in a transcript JSONL."""
    if not transcript_path:
        return ""
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for raw in reversed(lines):
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        message = entry.get("message") if isinstance(entry.get("message"), dict) else entry
        if message.get("role") != "assistant" and entry.get("type") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [block.get("text", "") for block in content
                     if isinstance(block, dict) and block.get("type") == "text"]
            if texts:
                return "\n".join(texts)
    return ""


def handle_stop(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Return a block decision, or None to let the turn end."""
    session_id = payload.get("session_id")
    try:
        record = read_latch(session_id) if session_id else None
    except LatchError:
        return None
    if record is None or payload.get("stop_hook_active"):
        return None
    if "last_assistant_message" in payload:
        text = payload.get("last_assistant_message") or ""
    else:
        text = last_assistant_text(payload.get("transcript_path"))
    ok, reason = footer_is_final_block(text if isinstance(text, str) else "")
    if ok:
        return None
    tasks = ", ".join(record.get("tasks") or []) or "the admitted task"
    return {
        "decision": "block",
        "reason": (f"Canopus footer required: {reason}. This session is latched to {tasks}. "
                   "End the response with the current Owner Footer, e.g. "
                   "`python3 tools/canopus_task.py footer --task <id>`, as the final block."),
    }


# ---------------------------------------------------------------------- CLI

def _stdin_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (OSError, json.JSONDecodeError):
        print("footer_latch: unreadable hook payload; not blocking", file=sys.stderr)
        return {}
    return payload if isinstance(payload, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canopus per-session footer latch")
    commands = parser.add_subparsers(dest="command", required=True)
    set_cmd = commands.add_parser("set")
    set_cmd.add_argument("--session", default=os.environ.get("CANOPUS_SESSION_ID"))
    set_cmd.add_argument("--task", required=True)
    commands.add_parser("stop")
    commands.add_parser("session-start")
    end_cmd = commands.add_parser("end")
    end_cmd.add_argument("--session")
    status_cmd = commands.add_parser("status")
    status_cmd.add_argument("--session", default=os.environ.get("CANOPUS_SESSION_ID"))
    args = parser.parse_args(argv)

    try:
        if args.command == "set":
            if not args.session:
                raise LatchError("--session is required (or set CANOPUS_SESSION_ID)")
            record = set_latch(args.session, args.task)
            print(f"latched {args.session}: {', '.join(record['tasks'])}")
        elif args.command == "stop":
            decision = handle_stop(_stdin_payload())
            if decision:
                print(json.dumps(decision, ensure_ascii=False))
        elif args.command == "session-start":
            # SessionStart hook stdout becomes agent context, so the agent
            # learns its own session id without guessing.
            session_id = _stdin_payload().get("session_id")
            if isinstance(session_id, str) and SESSION_ID.match(session_id):
                print(f"Canopus: this session id is {session_id}. When you admit a task, run "
                      f"`canopus_task.py admit ... --latch-session {session_id}`.")
        elif args.command == "end":
            session_id = args.session or _stdin_payload().get("session_id")
            if session_id:
                try:
                    clear_latch(session_id)
                except LatchError:
                    pass  # SessionEnd must never fail the session
        elif args.command == "status":
            sessions = [args.session] if args.session else sorted(
                path.stem for path in latch_dir().glob("*.json")) if latch_dir().is_dir() else []
            if not sessions:
                print("no latched sessions")
            for session_id in sessions:
                record = read_latch(session_id)
                print(f"{session_id}: " + ("CHAT (not latched)" if record is None else
                      f"MANAGED_TASK {', '.join(record.get('tasks') or []) or '(corrupt latch)'}"))
    except LatchError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

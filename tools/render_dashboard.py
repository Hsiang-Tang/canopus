#!/usr/bin/env python3
"""Render Canopus tasks as one self-contained HTML dashboard.

State is never read from a cache: every task is replayed through
``convergence.py`` exactly as ``canopus_task.py`` does, and the timeline
replays one event at a time so the step where a task changed state shows.

    render_dashboard.py [--state-dir DIR | --scenarios DIR] [--out FILE]
                        [--title TEXT] [--generated-at TEXT]
    render_dashboard.py --serve [--port 8765] [--state-dir DIR | --scenarios DIR]

Standard library only. ``--serve`` binds 127.0.0.1 and re-renders per request.
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

import canopus_task  # noqa: E402
import convergence  # noqa: E402

STATE_TONE = {"HEALTHY": "ok", "WATCH": "warn", "REALIGN": "warn",
              "CIRCUIT_BREAK": "stop", "COMPLETE": "done"}


# ------------------------------------------------------------------ sources

def records_from_state(root: Path | None = None) -> list[dict[str, Any]]:
    return [canopus_task.load(task_id, root) for task_id in canopus_task.list_tasks(root)]


def records_from_scenarios(directory: Path) -> list[dict[str, Any]]:
    """Wrap scenario files in the task-record shape (no timestamps)."""
    records = []
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        records.append({"task_id": path.stem, "title": data.get("title", ""),
                        "envelope": data["envelope"],
                        "events": [{"at": None, "event": event} for event in data["events"]],
                        "admitted_at": None, "closed_at": None, "outcome": None})
    return records


# ------------------------------------------------------------------ model

def timeline(record: dict[str, Any]) -> list[tuple[dict[str, Any], str | None, str]]:
    """(event, timestamp, state after the event) for every event in order."""
    task = convergence.TaskState(envelope=convergence.Envelope.from_dict(record["envelope"]))
    rows = []
    for entry in record["events"]:
        convergence.apply_event(task, entry["event"])
        rows.append((entry["event"], entry.get("at"), task.state))
    return rows


def describe(event: dict[str, Any]) -> str:
    detail = {key: value for key, value in event.items() if key != "kind"}
    if not detail:
        return ""
    if len(detail) == 1:
        return str(next(iter(detail.values())))
    return ", ".join(f"{key}: {value}" for key, value in detail.items())


# ------------------------------------------------------------------ html

STYLE = """
:root { color-scheme: light dark; --bg: #fafaf8; --fg: #1d1d1b; --muted: #6b6b66;
  --line: #e2e1dc; --card: #ffffff; --ok: #2f6f4f; --warn: #9a6200; --stop: #b3261e; --done: #2b5aa8; }
@media (prefers-color-scheme: dark) { :root { --bg: #141413; --fg: #ecebe6; --muted: #a3a29b;
  --line: #34332f; --card: #1d1d1b; --ok: #7cc49c; --warn: #e3b25a; --stop: #f2867e; --done: #8fb2f0; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
main { max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { font-size: 22px; margin: 0 0 4px; }
.sub { color: var(--muted); margin: 0 0 24px; }
.summary { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 24px; padding: 0; list-style: none; }
.summary li { border: 1px solid var(--line); border-radius: 999px; padding: 2px 12px; font-size: 13px; }
article { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 20px; margin: 0 0 20px; }
article h2 { font-size: 17px; margin: 0; }
.ref { color: var(--muted); font: 13px ui-monospace, SFMono-Regular, Menlo, monospace; }
.story { color: var(--muted); margin: 6px 0 12px; }
.state { display: inline-block; font: 600 12px ui-monospace, SFMono-Regular, Menlo, monospace;
  padding: 2px 8px; border-radius: 4px; border: 1px solid currentColor; }
.ok { color: var(--ok); } .warn { color: var(--warn); } .stop { color: var(--stop); } .done { color: var(--done); }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; margin: 12px 0; }
dt { color: var(--muted); } dd { margin: 0; }
progress { width: 160px; height: 8px; vertical-align: middle; accent-color: var(--done); }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
th, td { text-align: left; padding: 6px 8px; border-top: 1px solid var(--line); vertical-align: top; }
th { color: var(--muted); font-weight: 500; }
td.num { color: var(--muted); width: 2.5em; }
details summary { cursor: pointer; color: var(--muted); margin-top: 8px; }
"""


def _list(items: list[str], none: str = "none") -> str:
    return ", ".join(escape(str(item)) for item in items) or f'<span class="ref">{none}</span>'


def render_task(record: dict[str, Any]) -> str:
    rows = timeline(record)
    state = canopus_task.replay(record)
    envelope = state.envelope
    total, done = len(envelope.acceptance), len(state.accepted)
    tone = STATE_TONE[state.state]
    decision = convergence.DECISIONS[state.state][0]
    facts = [
        ("Goal", escape(envelope.north_star)),
        ("Progress", f'<progress max="{total}" value="{done}" aria-label="accepted items">'
                     f'</progress> {done} / {total} accepted'),
        ("Remaining", _list(state.remaining)),
        ("Decision", escape(decision)),
        ("Blockers", _list(sorted(state.open_blockers))),
        ("Deferred", _list(state.deferred_findings)),
    ]
    if state.reason:
        facts.append(("Reason", escape(state.reason)))
    if record.get("outcome"):
        facts.append(("Outcome", escape(record["outcome"])))
    if record.get("admitted_at"):
        facts.append(("Admitted", escape(record["admitted_at"])))
    body = "".join(f"<dt>{label}</dt><dd>{value}</dd>" for label, value in facts)
    events = "".join(
        f'<tr><td class="num">{index}</td><td>{escape(str(event.get("kind")))}</td>'
        f"<td>{escape(describe(event))}</td>"
        + (f'<td class="ref">{escape(at)}</td>' if at else "")
        + f'<td><span class="state {STATE_TONE[after]}">{after}</span></td></tr>'
        for index, (event, at, after) in enumerate(rows, 1))
    has_time = any(at for _, at, _ in rows)
    head = "<th>#</th><th>Event</th><th>Detail</th>" + ("<th>At</th>" if has_time else "") + "<th>State after</th>"
    story = f'<p class="story">{escape(record["title"])}</p>' if record.get("title") else ""
    return (f'<article aria-labelledby="t-{escape(record["task_id"])}">'
            f'<h2 id="t-{escape(record["task_id"])}"><span class="ref">{escape(envelope.task_ref)}</span> '
            f'<span class="state {tone}">{state.state}</span></h2>'
            f"{story}<dl>{body}</dl>"
            f"<details open><summary>Timeline, {len(rows)} events</summary>"
            f"<table><thead><tr>{head}</tr></thead><tbody>{events}</tbody></table></details></article>")


def render(records: list[dict[str, Any]], *, title: str = "Canopus tasks",
           generated_at: str | None = None) -> str:
    counts: dict[str, int] = {}
    for record in records:
        current = canopus_task.replay(record).state
        counts[current] = counts.get(current, 0) + 1
    summary = "".join(f'<li><span class="{STATE_TONE[name]}">{name}</span> {counts[name]}</li>'
                      for name in convergence.STATES if name in counts)
    sub = f"{len(records)} task{'s' if len(records) != 1 else ''}"
    if generated_at:
        sub += f" · generated {escape(generated_at)}"
    tasks = "".join(render_task(record) for record in records) or "<p>No tasks.</p>"
    return ("<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{escape(title)}</title><style>{STYLE}</style></head><body><main>"
            f"<h1>{escape(title)}</h1><p class=\"sub\">{sub}</p>"
            f"<ul class=\"summary\" aria-label=\"tasks by state\">{summary}</ul>{tasks}"
            "</main></body></html>\n")


# ------------------------------------------------------------------ cli

def make_server(build: Callable[[], str], port: int) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (http.server API)
            if self.path not in ("/", "/index.html"):
                self.send_error(404)
                return
            payload = build().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args: Any) -> None:
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--state-dir", type=Path, help="task state directory (default: canopus_task state dir)")
    source.add_argument("--scenarios", type=Path, help="directory of synthetic scenario JSON files")
    parser.add_argument("--out", type=Path, help="write the page here instead of stdout")
    parser.add_argument("--title", default="Canopus tasks")
    parser.add_argument("--generated-at", help="optional generation label shown on the page")
    parser.add_argument("--serve", action="store_true", help="serve a live page on 127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    def build() -> str:
        records = (records_from_scenarios(args.scenarios) if args.scenarios
                   else records_from_state(args.state_dir))
        return render(records, title=args.title, generated_at=args.generated_at)

    try:
        if args.serve:
            server = make_server(build, args.port)
            print(f"serving http://127.0.0.1:{server.server_address[1]}/ (Ctrl-C to stop)")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            return 0
        page = build()
    except (canopus_task.TaskError, convergence.ConvergenceError, OSError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.out:
        args.out.write_text(page, encoding="utf-8")
    else:
        sys.stdout.write(page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

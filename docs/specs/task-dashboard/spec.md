# Task dashboard requirements

## Outcome

An owner can see every Canopus task on one page: its goal, acceptance
progress, convergence state and decision, and the event timeline that led
there, without reading JSON or running several CLI commands.

## Requirements

- **DASH-001 — Same state as the CLI:** `render_dashboard.py` derives each
  task's state by replaying its events through `convergence.py`, exactly as
  `canopus_task.py` does. It never stores or edits task state.
- **DASH-002 — Two sources:** it reads durable task records from the state
  directory (`--state-dir`, default the `canopus_task.py` state directory) or
  synthetic scenario files (`--scenarios DIR`, the `examples/scenarios/`
  format).
- **DASH-003 — What a task shows:** task reference, North Star, accepted and
  total acceptance items with the remaining items listed, convergence state,
  the decision for that state, open blockers, deferred findings, the stop
  reason, and outcome when closed.
- **DASH-004 — Timeline:** every event appears in order with its kind, its
  detail, and the convergence state after that event, so the step where a
  task entered `WATCH`, `REALIGN`, `CIRCUIT_BREAK`, or `COMPLETE` is visible.
- **DASH-005 — One self-contained file:** the output is a single HTML file
  with inline CSS, no scripts, and no external URLs; it follows the system
  light or dark preference. Every task-supplied string is HTML-escaped.
- **DASH-006 — Deterministic output:** the same input renders the same
  bytes. A generation time appears only when `--generated-at` is given.
- **DASH-007 — Local live view:** `--serve` re-renders on every request from
  `127.0.0.1` only, so a refresh shows the latest events.

## Acceptance

| ID | Check |
| --- | --- |
| DASH-AC1 | Rendering `examples/scenarios/` shows all four scenarios with their final state and `accepted / total`. |
| DASH-AC2 | A task record admitted with `canopus_task.py` renders with the same state that `canopus_task.summary` reports. |
| DASH-AC3 | The timeline lists one row per event with the state after it. |
| DASH-AC4 | Markup in a North Star or event is escaped; the page has no `<script>` and no `http://` or `https://`. |
| DASH-AC5 | Two renders of the same input are byte-identical. |
| DASH-AC6 | `--serve` answers `GET /` with HTTP 200 and the page. |

Evidence: `tests/test_render_dashboard.py`; sample page
`docs/assets/dashboard-sample.html` rendered from `examples/scenarios/`.

## Non-goals

No editing of tasks from the page, no JavaScript, no authentication, no
hosting, and no network listener beyond `127.0.0.1`.

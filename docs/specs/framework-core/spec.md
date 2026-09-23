# Framework core requirements

## Outcome

A colleague can adopt Canopus in their own repositories: install the rules into
their agents, admit a task with a frozen envelope, have the harness enforce the
closing footer, and resume the task from durable state in any later session.

## Requirements

- **FW-001 — Durable task records:** `canopus_task.py` admits a task from a
  valid envelope, stores events atomically outside every repository, rebuilds
  state by replay, rejects invalid events without storing them, requires
  explicit re-admission for a changed envelope, and refuses a `complete` close
  that the evaluator does not confirm.
- **FW-002 — Harness enforcement:** `footer_latch.py` tells the agent its
  session id at `SessionStart`, latches one-way at admission, blocks a latched
  turn without a final Owner Footer, never blocks twice in one turn, fails open
  for unlatched sessions and closed for latched ones, and clears at
  `SessionEnd`.
- **FW-003 — Reversible bootstrap:** `install_bootstrap.py` is dry-run by
  default, idempotent, preserves and backs up unmanaged content, merges hooks
  without clobbering settings, and removes only what it added.
- **FW-004 — Recommendation-only routing:** `model_route.py` recommends the
  cheapest adequate tier for a task class and risk with an escalation tier,
  applies recorded evidence, and never launches work.
- **FW-005 — Workstream safety:** `workstream.py` reports scope collisions,
  shared branches or worktrees, dependency problems, and one-writer violations.
- **FW-006 — Knowledge gate:** `check_knowledge_candidate.py` rejects missing
  sections, template placeholders, and identifying values, and a pass still
  requires human review.
- **FW-007 — Adoptable kit:** rules, methodology, templates, and playbooks use
  the tool interfaces exactly as implemented, and every example is synthetic.

## Non-goals

No agent runtime, provider calls, scheduler, telemetry, or real project data.

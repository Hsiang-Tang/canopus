<!--
Body of the managed block that `tools/install_bootstrap.py --apply` writes into
~/.claude/CLAUDE.md between the canopus:bootstrap:start and
canopus:bootstrap:end markers. Edit here, rerun the installer; never hand-edit
the installed block. Text outside the markers is left untouched.
-->
# Canopus bootstrap (Claude Code)

For every session that involves local development, do this before material
changes:

1. Resolve the Canopus root from `CANOPUS_ROOT`, otherwise
   `git config --global --get canopus.root`. Never guess a path. If it
   is unset, stop and say that `python3 tools/register_machine.py --apply`
   must be run once from a Canopus clone.
2. If the Canopus checkout is clean and on its approved remote, run
   `git pull --ff-only`. If it is dirty or the pull fails, keep all changes,
   report it, and do not claim the rules are current.
3. Run `python3 tools/check_control_plane.py` from the Canopus root and read the
   files in the order declared by `control-plane.toml`.
4. If a workspace manifest pointer is registered, run
   `python3 tools/workspace_doctor.py --manifest <path>` and report every
   error. An error on this task's target blocks the task; an unparsable
   manifest blocks everything.
5. At the target project root, read `AGENTS.md`. The project `CLAUDE.md`
   imports it with `@AGENTS.md`; do not duplicate project rules here.
6. Inspect Git identity, remote, branch, and worktree before editing.

## Task discipline

- Classify the request. A formal task (it changes durable state or needs more
  than a quick answer) is admitted from its task Issue and latched for this
  session in one call, using the session id the `SessionStart` hook printed at
  startup:
  `python3 <canopus-root>/tools/canopus_task.py admit --task <id> --envelope <file.json> --latch-session <session-id>`
- Once latched, the installed `Stop` hook blocks a turn (once per turn) unless
  the response ends with the Owner Footer from
  `python3 <canopus-root>/tools/canopus_task.py footer --task <id>`. The latch is
  one-way; only `SessionEnd` clears it.
- Resume from the task Issue and `canopus_task.py handoff`, never chat history.
- Progress is accepted items or resolved blockers only. Stop at `COMPLETE`;
  on `REALIGN` do alignment only; on `CIRCUIT_BREAK` hand back to the owner.

## Boundaries

- One writer per checkout. Simultaneous writers use separate branches and
  worktrees; otherwise keep the second agent read-only as reviewer.
- Keep employer-owned or restricted material in its approved repositories and
  remotes. Keep local-only projects off hosted remotes.
- Load playbooks and model-routing guidance only when the task needs them.
  Keep the startup report to failures, stale state, and safety conditions.

# The continuation loop

Rule: [`rules/session.md`](../../rules/session.md) (Task admission; Owner
Footer; Agent Handoff; Resuming from durable state). Tool:
`tools/canopus_task.py` (`admit`, `event`, `checkpoint`, `footer`, `handoff`,
`status`, `close`). Template: `templates/handoff.md`.

## The problem

Long tasks outlive sessions. Context windows fill, sessions time out, a task
moves from one engine to another, or from a laptop to a remote runner. The
usual recovery is to paste the old conversation or a compacted summary into a
new session. That is lossy, it carries forward the old session's mistakes, and
it quietly resets any limit the old session had reached: the new session does
not know it already spent its correctives.

## The idea

**Task identity is not the session, the engine, or the machine.** A task is
its Issue plus its durable task record. Sessions are replaceable nodes that
read that state, do one bounded piece of work, and write state back.

```text
        +-------------------- task Issue + durable task record --------------------+
        |   North Star, frozen envelope, event log, convergence state, elapsed     |
        +------^----------------------------+---------------------------^----------+
               | read state                 | write events              | render
        +------+------+              +------v------+             +------+------+
        |    Brain    |  plan/review |  Executor   |  change/test| three views |
        | (any engine)| -----------> | (any engine)| ----------> |             |
        +-------------+              +-------------+             +-------------+
```

- **Brain:** plans, reviews, judges. Often read-only.
- **Executor:** changes, tests, delivers inside the envelope.
- Either may be any engine, and either may be replaced between rounds.

## Three views of one state

`tools/canopus_task.py` stores one record per task (under `$CANOPUS_STATE_DIR`, by
default `~/.canopus/state`) and renders it three ways:

1. **Machine state** (`status`): the full JSON, for validation and tools.
2. **Agent Handoff** (`handoff`): compact text for the next session: remaining
   acceptance, frozen scope, allowance usage, stagnation counters, deferred
   findings, and what the successor is permitted to do.
3. **Owner Footer** (`footer`): a few rows for the human, in English or
   Traditional Chinese.

All three come from the same record, so they cannot disagree. None is written
by hand.

## Example

A synthetic `acme-notes` task hits the session's hard context budget halfway
through, in the state reached in the [convergence example](convergence.md).
The old session records the next action, renders the handoff for the Issue,
and closes its run:

```sh
python3 tools/canopus_task.py event --task acme/acme-notes/issues/8 \
  --json '{"kind":"activity","what":"handoff","note":"Narrow to AC2 dedupe key"}'
python3 tools/canopus_task.py handoff --task acme/acme-notes/issues/8
python3 tools/canopus_task.py close --task acme/acme-notes/issues/8 --outcome handoff
```

The owner sees the footer at the end of the response:

```text
Canopus · acme/acme-notes/issues/8
────────────────────
Goal │ Notes sync without duplicates
Progress │ ■■■□□□□□□□ 1 / 3
Loop │ REALIGN · stalled cycles 2
Align │ drifted
Blocker │ none
Deferred │ 1
Reason │ 2 cycles without accepted progress
Next │ Narrow to AC2 dedupe key
Decision │ ALIGN ONLY
```

A new session, possibly on a different engine, starts cold. It reads the Issue,
runs `admit` with the same task ID (which resumes rather than resets), and
reads the handoff. It sees `REALIGN`, so its first action is alignment, not
another fix. Elapsed time keeps accumulating on the same task. Nothing from the
old chat was needed.

## Why not chat history

- It is not available to a different engine or machine.
- A summary chooses what to forget, and it forgets limits first.
- It mixes decisions with discarded ideas; a fresh reader cannot tell which is
  which.

Durable state is smaller, checkable, and the same for every reader.

## Operating notes

- Admission is idempotent: re-admitting resumes. A different ID is a different
  task.
- A bounded round with its own time limit gets its own child ID, so its elapsed
  time is not mixed with the parent's history.
- If the durable record is missing, the new session says so. It does not
  rebuild a task list from memory.

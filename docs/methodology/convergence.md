# Bounded convergence

Rule: [`rules/development.md`](../../rules/development.md) (Bounded
convergence contract). Tool: `tools/convergence.py` (evaluator),
`tools/canopus_task.py event` and `checkpoint` (durable driver). Decision record:
[`docs/adr/0002-bounded-convergence.md`](../adr/0002-bounded-convergence.md).

## The problem

A clear goal is not enough to make an agent stop. The common loop:

1. The agent implements a fix.
2. A review finds a valid issue.
3. The agent fixes it, adding code and tests.
4. The next review finds an issue in the new code.
5. Repeat.

Every step is reasonable and produces commits, passing tests, and review
comments. None of it closes an acceptance item. Measured by activity, the task
is thriving. Measured by outcomes, it stalled several cycles ago.

## Activity is not progress

The evaluator counts only two things as progress:

- an **accepted** acceptance item from the frozen list;
- a **resolved** blocker.

Everything else is recorded as activity: commits, test runs, reviews, turns,
tokens, handoffs, new findings. Activity is useful evidence and appears in the
Agent Handoff, but it never resets the stagnation counter.

## States

Work is recorded as events. A `checkpoint` closes a cycle and evaluates it.

- **HEALTHY:** the last cycle made progress. Continue.
- **WATCH:** one cycle without progress. Continue, but narrow.
- **REALIGN:** `realign_after` cycles without progress, a scope change without
  re-admission, or an attempt to accept something outside the frozen list.
  Only alignment work is allowed; a corrective or scope change here breaks the
  circuit.
- **CIRCUIT_BREAK:** `circuit_break_after` cycles without progress, an
  exhausted allowance, or the same blocker family seen twice. Stop mutation;
  the owner decides.
- **COMPLETE:** every frozen acceptance item is accepted. Stop.

Progress in a later cycle clears `WATCH` and `REALIGN`. Nothing clears
`CIRCUIT_BREAK` or `COMPLETE` except a new owner admission.

## Three rules that close the usual escape hatches

- **Out-of-scope findings are deferred, not done.** A reviewer's finding
  outside the envelope is recorded and shown to the owner at the end. It does
  not spend the corrective allowance and does not become work.
- **Allowances do not replenish.** Two correctives means two, across every
  session and engine.
- **A repeated blocker breaks.** If the same family of blocker (for example
  `flaky-fixture`) appears twice, retrying a third time is not a plan. Stop and
  hand back.

## Example

A synthetic `acme-notes` task: "Notes sync without duplicates", acceptance
`AC1`–`AC3`, `corrective_limit: 2`, `realign_after: 2`,
`circuit_break_after: 3`.

```sh
T=acme/acme-notes/issues/8
python3 tools/canopus_task.py event --task $T --json '{"kind":"accept","item":"AC1"}'
python3 tools/canopus_task.py checkpoint --task $T            # HEALTHY
python3 tools/canopus_task.py event --task $T --json '{"kind":"activity","what":"commits","count":4}'
python3 tools/canopus_task.py event --task $T --json '{"kind":"review"}'
python3 tools/canopus_task.py event --task $T --json '{"kind":"finding","summary":"sidebar flicker","in_scope":false}'
python3 tools/canopus_task.py checkpoint --task $T            # WATCH: activity only
python3 tools/canopus_task.py event --task $T --json '{"kind":"corrective"}'
python3 tools/canopus_task.py checkpoint --task $T            # REALIGN: 2 cycles, no progress
```

The sidebar flicker is deferred. Four commits and a review did not move
progress off `1 / 3`. At `REALIGN` the agent may only realign (re-read the
spec, narrow the next step); attempting another corrective now would break the
circuit. The footer tells the owner exactly this, in one line per fact.

The same scenarios run offline with `python3 tools/convergence_demo.py` and
the fixtures under `examples/scenarios/`.

## Why a deterministic evaluator

If the agent decides whether it is converging, it will usually decide that it
is; the next fix always looks close. The evaluator is a small pure function of
the envelope and the event log, so any session, engine, or human reviewer gets
the same answer from the same record.

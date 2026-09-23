# Bounded convergence requirements

## Outcome

Demonstrate, with synthetic data and the standard library only, how an
agent-executed task is kept on target by a frozen envelope and a deterministic
convergence evaluator, and how its state is handed to a human and to the next
agent session.

## Requirements

- **CONV-001 — Frozen envelope:** An admitted task declares unique acceptance
  items, scope, non-negative corrective and review allowances, and ordered
  realign and circuit-break thresholds; an invalid envelope is rejected.
- **CONV-002 — Progress is outcome:** Only a newly accepted frozen item or a
  resolved blocker is progress. Activity events never change progress.
- **CONV-003 — Stagnation escalation:** Consecutive checkpoints without
  progress move the task to `WATCH`, then `REALIGN` at the realign threshold,
  then `CIRCUIT_BREAK` at the circuit-break threshold. Verified progress
  returns it to `HEALTHY`.
- **CONV-004 — Finite allowances:** Corrective and review allowances never
  replenish; using one past its limit is `CIRCUIT_BREAK`.
- **CONV-005 — Drift:** A scope change without re-admission, or accepting an
  item outside the frozen list, is `REALIGN`. Material work attempted during
  `REALIGN` is `CIRCUIT_BREAK`.
- **CONV-006 — Deferred findings:** An out-of-scope finding is recorded as
  deferred evidence and never alters the envelope.
- **CONV-007 — Repeated blocker:** A second occurrence of the same blocker
  family is `CIRCUIT_BREAK`.
- **CONV-008 — Stop at done:** When every frozen item is accepted the task is
  `COMPLETE`, and later events are ignored.
- **CONV-009 — Two views, one state:** The same state renders an Owner Footer
  (English and Traditional Chinese) and an Agent Handoff whose successor
  instruction blocks mutation after a stop.
- **CONV-010 — Footer-last gate:** A response passes only when it ends with the
  exact current Owner Footer.
- **CONV-011 — Replayable scenarios:** Bundled synthetic scenarios reach their
  documented end state through the demo CLI.

## Non-goals

No scheduler, orchestration runtime, provider telemetry, persistence layer, or
real project data.

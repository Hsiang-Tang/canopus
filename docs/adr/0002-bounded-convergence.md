# ADR-0002: Bounded convergence for agent-executed tasks

- Status: Accepted
- Decision: Admit agent work with a frozen envelope and let a deterministic
  evaluator, not the agent, decide whether to continue, realign, or stop.

## Context

A long-running agent with a clear goal, acceptance criteria, and non-goals can
still fail to converge: valid review findings produce corrections, corrections
produce more tests and more reviews, and the implementation surface grows while
the stated goal stays the same. Budgets written only in a prompt are overrun
because nothing enforces them.

## Decision

- The owner freezes an envelope at admission: acceptance items, scope, finite
  corrective and review allowances, and stagnation thresholds.
- Delegated sessions inherit the envelope and cannot widen it. Changing scope
  or acceptance requires a new admission.
- Progress is only a closed acceptance item or a resolved blocker. Commits,
  tests, reviews, and findings are activity.
- Allowances only decrease. Exhaustion, a repeated blocker family, or the
  circuit-break stagnation threshold produces `CIRCUIT_BREAK`.
- The realign threshold, a scope change, or accepting an item outside the
  frozen list produces `REALIGN`, which permits alignment work only.
- Out-of-scope findings are deferred as evidence and never become work.
- When every acceptance item is satisfied the task is `COMPLETE` and stops.
- Each checkpoint renders an Owner Footer and an Agent Handoff from the same
  state, and a response that does not end with the current footer is blocked.

## Consequences

The agent can no longer turn thoroughness into an endless loop, and the owner
sees one consistent state regardless of which engine or session produced it.
The cost is that a genuinely larger task must be re-admitted explicitly, which
is the intended friction.

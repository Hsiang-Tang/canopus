# <Task title>

<!--
Body for a task Issue. The GitHub form version lives in
.github/ISSUE_TEMPLATE/canopus-task.md. The owner fills this in; the envelope JSON
block is what `canopus_task.py admit --envelope` reads. Once admitted, the
envelope is frozen: widening scope or acceptance means a new admission, not an
edit to this Issue.
-->

## North Star

<!-- One sentence: the observable outcome that means this task succeeded. -->

## Acceptance

<!-- Unique IDs. Each must be verifiable by a command or a named observation. -->

- [ ] `AC1` <positive case> — verify: `<command>`
- [ ] `AC2` <boundary or negative case> — verify: `<command>`
- [ ] `AC3` <recovery case> — verify: `<command>`

## Scope

- In scope: <modules, paths, contracts>
- Mutation scope (globs): `<src/export/**>`, `<tests/test_export*.py>`

## Non-goals

- <tempting adjacent work that must not be done in this task>

## Allowances

<!-- Finite and non-replenishing. Exhaustion stops the task for owner review. -->

- Corrective attempts: `2`
- Review rounds: `2`
- Checkpoints without progress before REALIGN: `2`
- Checkpoints without progress before CIRCUIT_BREAK: `3`

## Assumptions

| Assumption | Cost if wrong |
| --- | --- |
| <assumption> | <cost> |

## Envelope

Save this block as `envelope.json` and admit with
`python3 <canopus-root>/tools/canopus_task.py admit --task <TASK-ID> --envelope envelope.json`.

```json
{
  "task_ref": "<TASK-ID>",
  "north_star": "<North Star sentence>",
  "acceptance": ["AC1 <short>", "AC2 <short>", "AC3 <short>"],
  "scope": ["<scope area>"],
  "corrective_limit": 2,
  "review_limit": 2,
  "realign_after": 2,
  "circuit_break_after": 3
}
```

## Links

- Spec: `<docs/specs/<slug>/spec.md or none (R1)>`
- Risk: `<R0 | R1 | R2 | R3>`

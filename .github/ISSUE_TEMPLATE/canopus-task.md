---
name: Canopus task
about: Admit a bounded agent task with a North Star, frozen envelope, and acceptance list
title: "<TASK-ID>: <outcome in a few words>"
labels: ["canopus-task"]
---

<!--
Fill every section. After admission the envelope is frozen: do not edit
acceptance, scope, or allowances here. To widen the task, close this one
(outcome: handoff) and open a new admission that links it.
Never include secrets, customer data, internal URLs, or restricted material.
-->

## North Star

<!-- One sentence: the observable outcome that means this task succeeded. -->

## Acceptance

<!-- Unique IDs, each verifiable by a command or a named observation. -->

- [ ] `AC1` <positive case> — verify: `<command>`
- [ ] `AC2` <boundary or negative case> — verify: `<command>`
- [ ] `AC3` <recovery case> — verify: `<command>`

## Scope

- In scope: <modules, paths, contracts>
- Mutation scope (globs): `<src/area/**>`

## Non-goals

- <adjacent work that must not be done here>

## Allowances

<!-- Finite and non-replenishing. Exhaustion stops the task for owner review. -->

- Corrective attempts: `2`
- Review rounds: `2`
- Checkpoints without progress before REALIGN: `2`
- Checkpoints without progress before CIRCUIT_BREAK: `3`

## Assumptions

<!-- Required when the request was ambiguous: 3-5 rows. -->

| Assumption | Cost if wrong |
| --- | --- |
| <assumption> | <cost> |

## Envelope

<!-- Keep in sync with the sections above; this is what gets admitted. -->

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

Admit with:
`python3 <canopus-root>/tools/canopus_task.py admit --task <TASK-ID> --envelope envelope.json`

## Risk and links

- Risk: `<R0 | R1 | R2 | R3>`
- Spec: `<docs/specs/<slug>/spec.md | none>`
- Supersedes: `<previous task issue | none>`

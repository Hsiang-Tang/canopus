# North Star and frozen envelope

Rule: [`rules/development.md`](../../rules/development.md) (North Star and
envelope; Bounded convergence contract). Tool: `tools/canopus_task.py admit`,
evaluated by `tools/convergence.py`. Template: `templates/task-issue.md`.

## The problem

An agent given a goal will keep finding reasonable work near that goal. Each
step is defensible: a test is missing, a function could be cleaner, a reviewer
noticed an edge case. After a few hours the diff is three times the size, the
original goal is not done, and nobody decided to widen it. Scope grew because
nothing said where it ended.

## The idea

Separate two things that are usually blurred:

- **North Star:** one sentence naming the outcome the task exists for. It is
  the tie-breaker when a choice is unclear. It is not measured directly.
- **Envelope:** the finite, checkable contract, frozen at admission:
  - `acceptance`: unique IDs for the outcomes that define done. Their count is
    the progress denominator.
  - `scope`: IDs of what the task may change.
  - `corrective_limit` and `review_limit`: how many fix attempts and review
    rounds the task may spend.
  - `realign_after` and `circuit_break_after`: how many cycles without
    progress trigger realignment and then a hard stop.

"Frozen" is literal. Nothing downstream may widen it: not the executor, not a
reviewer, not a fresh session picking up the handoff. If the task genuinely
needs more, the owner re-admits it with a new envelope. That friction is the
point; it turns silent scope growth into an explicit decision.

## Why finite allowances

Allowances that refill ("one more review round") are not limits. The envelope
gives a fixed number of correctives and reviews, and they only go down. When
they run out, the task stops and the owner decides whether the remaining gap
is worth another admission. Most of the time it is not, and the owner is the
right person to make that call.

## Example

A task on a synthetic `docs-site` project: "Readers can search the docs
offline."

```json
{
  "task_ref": "acme/docs-site/issues/17",
  "north_star": "Readers can search the docs offline",
  "acceptance": ["AC1-index-built", "AC2-search-box", "AC3-no-network"],
  "scope": ["search/", "templates/header"],
  "corrective_limit": 2,
  "review_limit": 2,
  "realign_after": 2,
  "circuit_break_after": 3
}
```

```sh
python3 tools/canopus_task.py admit --task acme/docs-site/issues/17 --envelope envelope.json
```

Midway, a reviewer notes the navigation menu is slow. That is real, but it is
not in `scope` and not an acceptance item. It is recorded as a deferred
finding and shown to the owner at the end. It does not become work in this
task. When `AC1`–`AC3` are accepted, the task is `COMPLETE` and stops, even
though the menu is still slow.

## Checklist for writing an envelope

- Each acceptance item is observable and independently checkable.
- Three to seven items is typical. One is fine. Twenty means the task is too
  big; split it.
- Scope names directories or components, not "anything related".
- Small allowances (1–3) are normal. A task that needs more is usually
  under-specified.
- Record the envelope in the task's Issue so every session sees the same one.

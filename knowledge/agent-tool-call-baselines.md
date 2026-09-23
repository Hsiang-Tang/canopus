# Task shape sets the baseline for agent tool-call counts

## Type

Knowledge note.

## Scope

Reviewing an agent's session log to judge whether it worked efficiently,
looped, or re-verified pointlessly, especially when comparing call counts
across different kinds of tasks.

## Problem shape

Two tasks of different shape are compared side by side. One only queries
state; the other includes a long-running long-running build or pipeline job. The
second shows far more tool calls and more literally repeated commands, and
reads as "the agent behaves worse on this kind of task". On its own, that
comparison is misleading.

## Guidance

Task shape sets a structural floor on call count unrelated to agent quality.
A task with an embedded long-running process must poll it until it finishes,
and every poll is a separate call that does no new work.

1. **Bucket each call by role:** new work (changes state or gathers new
   information) versus polling an already-started operation. Compare only the
   new-work bucket across task shapes.
2. **Check what happened between duplicates.** A byte-identical repeat after a
   reported failure and a fix is correct fix-then-reverify. A fresh read after
   a new instruction widened scope is legitimate. Classify each occurrence from
   its surrounding turns, not from the raw count.
3. **Report evidence, not impression.** Cite the calls per bucket and the
   context around each duplicate rather than "N duplicate calls".

## Validation

For every literal duplicate, locate both occurrences and check the turns in
between for an intervening fix, a scope-changing instruction, or progress in
a polled operation. Classify each individually.

## Limits and failure modes

- When both tasks have the same shape, a raw count comparison is meaningful.
- A repeat with no intervening event of any kind is a real stuck loop; this
  note is not an excuse for it.
- Over-crediting hides runaway retries; under-crediting "fixes" a workflow
  that was never broken. Both are corrected by rereading the log with the
  bucketing method.
- Read-only diagnostic; nothing to roll back except a wrong conclusion.

## Related guidance

- [`confirmed-redundant-rereads.md`](confirmed-redundant-rereads.md) — the
  test for when a duplicate really is waste.
- [`generation-verification-throughput.md`](generation-verification-throughput.md)

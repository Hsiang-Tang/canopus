# When a repeated read is confirmed waste

## Type

Knowledge note.

## Scope

Auditing an agent's session log for redundant work, as the counterweight to
[`agent-tool-call-baselines.md`](agent-tool-call-baselines.md), whose
context-check method finds a legitimate reason for most repeats.

## Problem shape

After finding one or two genuine explanations for repeated calls (polling, a
scheduled recurring check, fix-then-reverify), a reviewer generalizes them
into a blanket excuse and stops checking the remaining duplicates. A real
waste pattern then passes as "probably fine, like the others".

## Guidance

A literal duplicate call is confirmed waste when all three hold:

1. **Identical output.** Both occurrences return byte-identical results, so
   the underlying content did not change.
2. **Nothing changed in between.** No repair after a failing check, no new
   instruction that widened scope, no progress from a polled operation.
3. **Already in context.** The same content was already available earlier in
   the same continuous working context, so re-fetching it taught the agent
   nothing.

When all three hold, the agent failed to treat content it had already read as
durable. That is a defect to investigate, not something to wave away with the
polling or recurrence explanation. Check each remaining duplicate against the
three conditions individually.

## Validation

For the specific pair of calls, record explicitly: outputs identical (yes or
no), state-changing event between them (none or which), content present
earlier in context (yes or no). All three together are the signature; a raw
repeat count or a resemblance to an excused pattern is not.

## Limits and failure modes

- Does not apply across separately triggered invocations, such as a scheduled
  check that is designed to run the same command each time.
- Does not apply when a fix, new instruction, or progress event sits between
  the calls; that is legitimate re-verification.
- Fixing the agent behavior (trusting recorded content, keeping notes) is a
  separate follow-up; see
  [`notes-and-searchable-history-over-lossy-compaction.md`](notes-and-searchable-history-over-lossy-compaction.md).

## Related guidance

- [`agent-tool-call-baselines.md`](agent-tool-call-baselines.md)

# Durable notes beat a single lossy summary

## Type

Knowledge note.

## Scope

Long agent sessions that outgrow their context window, and any workflow that
must continue across sessions, engines, or machines.

## Problem shape

When context fills, the default remedy is compaction: replace older history
with one generated summary. That is lossy by construction. The summarizer
decides what mattered before anyone knows which detail (why an earlier fix
failed, an exact value the owner stated) will be needed later. The loss is
silent until a session acts on incomplete information.

## Guidance

- Write what matters to files as it is learned, outside the compressible
  conversation: the task record, the handoff, the spec's decisions section,
  a memory or notes file.
- Read back only the relevant file when a task needs it. Do not re-derive or
  re-summarize conclusions that are already recorded.
- Resume a task from its durable record (Issue, task record, handoff), never
  from a summary of the old chat.
- Coding-agent hosts increasingly ship this as a built-in: file-based memory
  directories that survive compaction and are reloaded in later sessions.
  Prefer the built-in where it exists; it is the same pattern.

In Canopus, the task record plus `canopus_task.py handoff` is the durable note for
task state, and the handoff template captures what the machine state cannot.

## Validation

- A correction or preference recorded once is applied by a later session
  without the owner repeating it.
- A fresh session given only the handoff and the repository reaches the same
  next action the previous session had planned.

## Limits and failure modes

- Notes do not fix bad judgment about what to record. An agent that writes too
  little still loses detail; this removes the summarization failure, not the
  selection failure.
- Plain compaction is fine for disposable back-and-forth with no lasting value.
  Do not turn every exchange into a permanent note; update an existing note
  instead of adding a new one.
- Notes help only if their storage is durable and actually re-read.

## Related guidance

- [`canonical-state-and-replaceable-execution.md`](canonical-state-and-replaceable-execution.md)
- [`confirmed-redundant-rereads.md`](confirmed-redundant-rereads.md) — the
  opposite failure: re-reading content already available instead of trusting
  what is recorded.

# Enforce with the harness, and audit the harness itself

## Type

Knowledge note.

## Scope

Any agent governance setup that relies on instruction files the model reads,
and any project deciding which policies need technical enforcement rather than
documented expectation.

## Problem shape

A prose rule such as "never commit the local manifest" or "end every task
response with the footer" can be clear, indexed, and validated for presence,
yet nothing makes violating it impossible. A session that skims, forgets under
context pressure, or is manipulated by injected text can still break it. The
rule only makes the violation detectable afterward.

Separately, security reviews usually examine the project's code while
ignoring the agent's own configuration: hook scripts, permission settings,
MCP or tool server config, and instruction files. Those can be tampered with,
can leak secrets, or can silently widen what an agent is allowed to do.

## Guidance

1. **A hook enforces; a rule advises.** Harness hooks (session start, stop,
   before and after a tool call) run outside the model's context. A
   pre-tool-call hook can block a command outright; a stop hook can refuse to
   end a turn. No wording of a prose rule achieves that.
2. **Convert only what is critical and mechanically checkable.** Good
   candidates: a forbidden path or filename, an unapproved remote, a
   destructive command pattern, a required final block. Poor candidates:
   anything needing judgment. Leave those as prose.
3. **Make the enforcement state one-way.** Canopus's footer latch is set at task
   admission and cleared only at session end, so the agent cannot talk itself
   out of the requirement mid-session. The `Stop` hook checks the final
   message and never blocks twice in the same turn, so it cannot deadlock.
4. **Treat harness config as an attack surface.** Review hook scripts,
   settings files, tool-server config, and instruction files with the same
   care as code: version them, diff them, scan them for secrets, and question
   any change that widens permissions or adds a network-reachable tool.

## Validation

- Every adopted hook has a test with a known-bad input that it blocks and a
  known-good input it allows.
- The installer that writes hooks is idempotent, preserves unrelated settings,
  and has a remove path.
- A review of instruction and hook files is part of the normal diff review,
  not a separate afterthought.

## Limits and failure modes

- A buggy or over-broad hook locks out legitimate work exactly when it
  matters. Keep conditions narrow and keep an escape path (for example, not
  blocking a second time in one turn).
- A config scanner only covers the patterns it knows; it is defense in depth,
  not proof that nothing was tampered with.
- Converting every rule to a hook recreates a large, brittle policy engine.
  Convert one concrete, repeatedly violated rule at a time.

## Related guidance

- [`canonical-state-and-replaceable-execution.md`](canonical-state-and-replaceable-execution.md)
- [`../rules/security.md`](../rules/security.md)

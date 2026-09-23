# Knowledge index

Knowledge notes explain reusable patterns, tradeoffs, and failure modes. They
are not mandatory rules and are loaded only when relevant to the task. Every
note here is generic and de-identified.

- [`canonical-state-and-replaceable-execution.md`](canonical-state-and-replaceable-execution.md)
  — give every class of durable state one owner; treat machines, sessions,
  worktrees, and engines as replaceable consumers.
- [`deterministic-enforcement-and-harness-as-attack-surface.md`](deterministic-enforcement-and-harness-as-attack-surface.md)
  — convert critical, mechanically checkable rules into harness hooks, and
  review hook, permission, and instruction files as an attack surface.
- [`notes-and-searchable-history-over-lossy-compaction.md`](notes-and-searchable-history-over-lossy-compaction.md)
  — write what matters to durable files and read it back on demand instead of
  relying on one lossy context summary.
- [`generation-verification-throughput.md`](generation-verification-throughput.md)
  — verification capacity, not generation speed, sets delivery throughput;
  invest in intent, plans, tiered checks, and evidence-first review first.
- [`agent-tool-call-baselines.md`](agent-tool-call-baselines.md) — task shape
  sets a floor on tool-call counts; bucket calls by role before judging
  efficiency.
- [`confirmed-redundant-rereads.md`](confirmed-redundant-rereads.md) — the
  three-part test for when a repeated call is genuine waste rather than
  polling or re-verification.

New notes start from [`../templates/knowledge-pack.md`](../templates/knowledge-pack.md)
and go through [`../playbooks/knowledge-distillation.md`](../playbooks/knowledge-distillation.md).

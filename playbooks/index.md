# Playbook index

Playbooks are repeatable procedures with validation and rollback. Load one only
when the task needs it. They never replace a project's own runbooks or grant
authority the project has not granted.

- [`adopting-canopus.md`](adopting-canopus.md) — start here: install the bootstrap,
  add Canopus to a repository, and run one admitted task end to end in about 15
  minutes.
- [`validation-throughput.md`](validation-throughput.md) — staged edit,
  integration, merge, and release gates with evidence reuse, precise
  invalidation, and latency measurement.
- [`parallel-workstreams.md`](parallel-workstreams.md) — declared mutation
  scopes, collision checks, one writer per worktree, ordered integration, and
  recovery of abandoned work.
- [`knowledge-distillation.md`](knowledge-distillation.md) — capture reusable
  lessons at task closeout, triage without auto-promotion, human review, and a
  separate gate for crossing ownership boundaries.
- [`skill-portfolio-review.md`](skill-portfolio-review.md) — periodic,
  read-only review of skill scope, routing, discovery cost, and retirement.

New playbooks start from [`../templates/knowledge-pack.md`](../templates/knowledge-pack.md)
and go through [`knowledge-distillation.md`](knowledge-distillation.md).

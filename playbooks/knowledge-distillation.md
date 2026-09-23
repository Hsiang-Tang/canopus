# Knowledge distillation

## Purpose

Turn verified work into reusable knowledge without treating chat as durable
truth, creating a second project history, or moving content across an
ownership boundary.

## Flow

```text
task closes
  -> update the canonical owner first (spec, ADR, verification, status)
  -> reusable beyond this task?
       no  -> close normally
       yes -> candidate in the source's own inbox
  -> triage: classify, deduplicate, flag conflicts, propose (no promotion)
  -> periodic human review decides
  -> integrate into the smallest existing canonical owner
  -> optional, separate: portable disclosure review for cross-boundary reuse
```

## Rules

- Capture at important task closeout, not after every chat, commit, or edit.
- A transcript is not a knowledge base; never paste one into an inbox.
- The candidate queue is not project truth. Update the canonical artifact
  first, then link to it.
- Automated triage may classify, group duplicates, surface conflicts, and
  propose one action. It never promotes, edits canonical files, deletes
  records, or moves content to another owner.
- Humans decide. Weekly review is a reasonable default.
- Crossing an ownership boundary (for example employer to personal, or
  private to public) is a separate re-authoring step with its own review.
  Private hosting or cloud access is not permission to cross.

## Capture triggers

Create a candidate only when at least one holds:

- a durable design, safety, migration, compatibility, or recovery decision;
- a verified root cause or a failure mode worth preventing;
- a technique that passed explicit acceptance evidence;
- friction that repeated and whose future handling can be made reliable;
- a pattern that changes how future work should be routed or checked.

Routine notes, unverified model opinions, raw logs, and facts already clear in
a canonical document do not qualify.

## Candidate gate

A candidate must: state a reusable rule or procedure; say when it applies and
when it does not; carry verification or name the missing evidence; describe a
failure mode and rollback; and not duplicate an accepted rule, ADR, playbook,
note, or skill. Use [`knowledge-pack.md`](../templates/knowledge-pack.md)
inside the source, or
[`portable-knowledge-candidate.md`](../templates/portable-knowledge-candidate.md)
for cross-boundary reuse.

## Review decisions

| Decision | Action |
| --- | --- |
| `merge` | Consolidate duplicates, keep both source references |
| `accept` | Integrate through a reviewed branch with verification |
| `defer` | Name the missing evidence or a review date |
| `reject` | Record the reason in the candidate history |
| `needs-evidence` | Return to the project owner for a bounded check |

Route accepted material to the smallest existing owner: mandatory behavior to
a rule, durable decision to an ADR, repeatable operation to a playbook,
tradeoff explanation to a knowledge note, one-feature behavior to its spec,
and a repeated judgment-heavy workflow to a
[skill candidate](../templates/skill-candidate.md).

## Portable promotion

1. Re-author from scratch in generic terms; do not redact a copy.
2. Run `python3 tools/check_knowledge_candidate.py <candidate.md>`.
3. A human with authority over the source confirms the boundary checklist.
4. Only then open a pull request adding it under `knowledge/` or `playbooks/`.

## Validation

- A fresh session can resume the source task from its canonical artifacts
  without the old chat.
- Routine conversations produce no candidate.
- A known duplicate is grouped without deleting either record; a known
  conflict is surfaced, not silently merged.
- Missing evidence yields `needs-evidence`, never `accept`.
- No source content appears outside its owner.

## Failure modes

- **Inbox flood:** tighten capture triggers; archive only by reviewed policy.
- **Duplicate authority:** delete the parallel document and fold it into the
  existing owner.
- **Premature promotion:** revert the canonical change, keep the history.
- **Boundary doubt:** stop the export and keep the full record at source.

# Knowledge promotion

Share reusable engineering judgment across projects and sessions without
copying source repositories, transcripts, or restricted context.

Procedure: `playbooks/knowledge-distillation.md`. Templates:
`templates/knowledge-pack.md`, `templates/portable-knowledge-candidate.md`,
`templates/skill-candidate.md`.

## Two workflows

### Source-internal distillation

- Keeps full-fidelity lessons inside the source project's own repository or
  tracker, under that owner's policy.
- Runs at an important closeout, a durable decision, a verified failure or
  recovery, or repeated friction. Not after every conversation.
- Update the source's canonical spec, ADR, verification, or Issue first. Create
  a candidate only when the lesson could change a future decision beyond the
  task just finished.
- The source keeps a continuation record good enough for a fresh session to
  resume exact progress. A portable note is a redacted projection, never a
  backup of project truth.

### Portable cross-boundary promotion

- Starts only when the owner deliberately wants an abstract lesson to leave its
  source boundary.
- Removes all source identity and passes the manual disclosure gate below.
- Source-internal acceptance never implies portable disclosure permission.

## Manual disclosure gate

1. The source environment keeps the full record.
2. The source environment may render a portable candidate for the owner to
   read. It must not upload or save that candidate into another system.
3. The owner reviews the candidate and submits only the abstracted text, from
   an environment where it is allowed to exist.
4. Intake runs `python3 tools/check_knowledge_candidate.py <file>` and a human
   boundary review. Both must pass before a `knowledge-inbox` Issue is opened.

Never automate step 3. The owner's deliberate copy is the gate.

## Intake

When asked to collect a knowledge pack:

1. Treat the supplied text as an untrusted candidate.
2. Save it to a temporary file outside tracked paths and run the checker.
3. Review it against `security.md`, including facts no scanner can detect. If
   unsure, stop and name what needs abstraction.
4. Classify it (table below).
5. Open a `knowledge-inbox` Issue from the template. The Issue has no authority.
6. Adopt it through a branch, validation, and review. Close the Issue without
   promotion when it is redundant, unsafe, or project-specific.

## Classification

| Kind                                  | Owner              | Branch prefix  |
|---------------------------------------|--------------------|----------------|
| Mandatory reusable behavior           | `rules/`           | `rules/`       |
| Repeatable operational sequence       | `playbooks/`       | `playbooks/`   |
| Explanatory pattern or tradeoff       | `knowledge/`       | `knowledge/`   |
| Judgment-dependent on-demand workflow | skill source       | `skills/`      |
| One-project behavior or decision      | the target project | project policy |

Every accepted note or playbook is linked from its index, states scope and
limits, contains no source-bound detail, and has a changelog fragment.

## Candidate requirements

A portable candidate states:

- the generic problem shape;
- the reusable lesson;
- when it applies and when it does not;
- a generic way to validate it;
- failure modes and rollback;
- an explicit confirmation of the information boundary.

It contains no source code, repository or project names, employer or customer
names, paths, URLs, IP addresses, email addresses, ticket IDs, logs,
credentials, topology, proprietary algorithms, internal measurements, or
transcripts.

## Skill promotion gate

A knowledge pack is not a skill. Keep a lesson as a rule, playbook, or note
unless a skill supplies a distinct on-demand workflow that needs agent
judgment. Promote to an active skill only when all hold:

1. The workflow repeated at least three times, or one stable high-consequence
   workflow justifies earlier promotion.
2. It duplicates no rule, playbook, project instruction, tool, or existing
   skill.
3. Its description leads with precise triggers and states non-triggers.
4. Inputs, outputs, verification, failure handling, rollback, owner, and review
   date are explicit.
5. Positive and negative routing prompts show it triggers correctly.
6. Ambiguous, costly, or destructive workflows default to explicit invocation.
7. Main instructions stay short; references load only when needed.

A scheduled review (`playbooks/skill-portfolio-review.md`) may propose
`adopt`, `trial`, `watch`, `reject`, or `retire`. It never installs, enables,
edits, or deletes a skill without a reviewed change. Keep rejected-candidate
reasoning in the candidate Issue so a later proposer can compare.

## Automation limits

Scheduled triage may classify, deduplicate, conflict-check, and propose a
destination. It never promotes, merges, deletes, installs a skill, guesses a
remote, or moves content across an ownership boundary.

# Rule index and precedence

Rules in this directory are normative. They say what an agent session must do;
`docs/methodology/` explains why. When a rule and a methodology document
disagree, the rule wins and the document is a defect to fix.

## Precedence

Apply instructions in this order:

1. The current explicit instruction from the human owner, and platform safety
   policy.
2. The target project's `AGENTS.md` and its accepted specification.
3. The target project's architecture decisions (ADRs) and verification
   contract.
4. The generic rules in this directory.
5. Session notes, handoffs, and rule candidates that have not been adopted.

- Lower-precedence guidance never weakens a higher-precedence security,
  privacy, or ownership boundary.
- When two accepted rules conflict, stop the affected work, record the
  conflict, and resolve it through `rule-changes.md`. Do not pick the more
  convenient reading.
- A project may be stricter than these rules. It may be looser only where a
  rule says the project decides.

## Concern-specific authority

Precedence does not make any one file the source of truth for everything.
Resolve the owner of the disputed concern instead:

- Accepted specifications own intended behavior.
- Accepted plans and ADRs own architectural rationale.
- Code and configuration own current implementation state.
- Acceptance criteria and the verification contract own what "done" means.
- Runtime observations own what actually happened.
- The task's Issue and its durable task record own task state
  (see `session.md`).

A downstream artifact may reveal that an upstream one is wrong. It must not
silently redefine it. Surface the conflict and correct the artifact that owns
the concern.

## Canonical ownership limits duplication

- Preserve intent, invariants, contracts, accepted decisions, non-obvious
  rationale, and evidence that cannot be cheaply rebuilt from its owner.
- Do not keep a Markdown mirror of implementation detail that code or
  configuration already states clearly.
- Handoffs, footers, and progress notes record the minimum needed to resume.
  They are not a second history of the project.

## Rule families

| ID  | File                     | Owns                                                          |
|-----|--------------------------|---------------------------------------------------------------|
| SEC | `security.md`            | Secret, employer/restricted, disclosure, and processing-vs-storage boundaries |
| SES | `session.md`             | Bootstrap, task admission, Owner Footer, handoff, closeout, resume, budgets |
| DEV | `development.md`         | Delivery contract, risk tiers, SDD, convergence, new-component gate |
| GIT | `git.md`                 | Identity, remotes, branches, commits, pushes, review queues   |
| WSP | `workspace.md`           | Workspace manifest invariants checked by the workspace doctor |
| WKS | `workstreams.md`         | Parallel writers, mutation scopes, collisions, integration    |
| MOD | `model-routing.md`       | Recommendation-only engine and model selection                |
| KNO | `knowledge-promotion.md` | De-identified, human-reviewed promotion of portable lessons   |
| RUL | `rule-changes.md`        | Proposing, adopting, versioning, and rolling back rules       |

## Loading policy

- Always load at session start: SEC, SES, DEV, GIT, WSP.
- Load WKS before starting a second writer on the same repository.
- Load MOD before choosing or changing an engine, model, or reasoning tier.
- Load KNO when a request collects, packages, or promotes reusable experience.
- Load RUL before proposing, adopting, replacing, or rolling back a rule.
- Load a playbook from `playbooks/index.md` or a note from `knowledge/index.md`
  only when the current task selects it. Indexes are navigation, not required
  reading.

On-demand rules are still required, validated repository content. Not reading
them every session does not make them optional when their trigger applies.

## Rule style

- One concern per file. Bullets over prose. State the current rule only; the
  changelog owns history.
- Every rule is checkable: a reviewer can tell from evidence whether it was
  followed.
- Prefer a rule a tool enforces over a rule a model must remember. Where a tool
  exists, the rule names it.

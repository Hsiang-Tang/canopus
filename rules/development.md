# Risk-scaled development

Use specification-driven development (SDD) as the outer frame and scale every
other practice to risk. Method names do not create requirements; the target
project's own artifacts stay canonical.

Background: `docs/methodology/risk-scaled-sdd.md`,
`docs/methodology/assumptions-first.md`, `docs/methodology/convergence.md`,
`docs/methodology/anti-over-engineering.md`.

## Minimum delivery contract

For every behavior-changing task:

1. Name the requirement owner and the observable outcome.
2. If the request is ambiguous, run assumptions-first (below) before material
   work.
3. Write acceptance cases in proportion to risk: positive, negative, boundary,
   and recovery. Plain language is the default; Given/When/Then is optional.
4. Record design and dependency choices in the plan. Write an ADR only for an
   architecturally significant decision.
5. Map each task to a requirement and a verification before implementing it.
6. Preserve acceptance integrity. Never delete or weaken a check to make an
   implementation pass. Prove important checks against a known-bad case when
   practical.
7. Verify the real runtime or artifact, not only automated checks, when the
   change is user-visible, platform-specific, an integration, a release, or
   visual.

A small correction with an adequate existing requirement and verification
does not need a new spec set. Ambiguous, cross-component, privacy-sensitive,
migration, or new durable product work does.

## Risk tiers

Classify before starting. The tier sets the required artifacts and gates, not
the model (see `model-routing.md`).

- **R0 — trivial and reversible.** No behavior change: typo, formatting,
  comment, dead link. Required: the edit plus the repository's fast checks.
- **R1 — local change under an existing requirement.** One component, existing
  acceptance and tests cover it. Required: a failing or known-bad check first
  when feasible, then the affected tests.
- **R2 — new or cross-component behavior.** New feature, public interface,
  schema, dependency, or user-visible change. Required: `spec.md`, `plan.md`,
  `tasks.md` under `docs/specs/<slug>/`, a frozen envelope, and the full
  verification contract on the merge candidate.
- **R3 — boundary or irreversible impact.** Security or privacy boundary,
  credentials, data migration, destructive operation, release, or an external
  action without a tested recovery path. Required: everything in R2, an ADR
  when architecture changes, an independent review that the implementing
  session cannot self-approve, a rollback path, and explicit owner acceptance.

When impact is uncertain, use the higher tier. Reclassify upward as soon as
evidence shows the task is bigger; reclassifying downward needs a stated
reason.

## Spec artifacts

- Feature artifacts live at `docs/specs/<slug>/spec.md`, `plan.md`, and
  `tasks.md`. Use `templates/spec-kit/` to seed them.
- The project `AGENTS.md` holds durable governing principles. Do not add a
  second constitution file.
- Refer to plan decisions by a short stable slug, not a list position.
- An ADR that is replaced stays in place, marked superseded, with a link to its
  replacement. Use `templates/adr.md`.
- Code comments state technical intent. Put the reason for a non-obvious
  decision in `plan.md` or an ADR, not a comment that narrates the conversation
  that produced the change.

## Assumptions-first

When the outcome, scope, or success signal would have to be guessed:

- List three to five assumptions or open points before material work.
- Give each one the cost of being wrong ("if wrong, we rebuild the importer").
- Let the owner confirm or correct them. Proceed on the confirmed set.
- Record confirmed assumptions in the spec or task Issue, not only in chat.
- Skip this step when the request is already clear. It adds no tool, field, or
  template.

## Verification ladder

Choose the stage before running commands. Stages accumulate evidence; they do
not require replaying every gate after every edit.

- **Edit loop:** the smallest deterministic check that could disprove the
  change, starting with the failing or known-bad case.
- **Integration gate:** affected component, contract, and boundary checks after
  a coherent batch of edits.
- **Merge candidate:** the full repository contract, once, on the exact commit
  proposed for merge.
- **Release candidate:** packaging, platform, migration, visual, and owner
  acceptance gates, only for the exact artifact that will ship.

- Escalate straight to the full gate for uncertain impact, a shared interface,
  schema or migration, dependency or toolchain, build configuration, security
  or privacy boundary, concurrency, or test-selection logic.
- Passed evidence stays valid while its commit, inputs, toolchain, lockfile,
  configuration, and artifact are unchanged. Time alone does not invalidate
  it; name the input that changed.
- CI is a place evidence runs, not proof that acceptance is met.

## North Star and envelope

Every admitted R2 or R3 task, and any task run as an autonomous loop, has:

- **North Star:** one sentence naming the outcome the task exists for.
- **Frozen envelope:** acceptance item IDs (the denominator), scope IDs,
  finite corrective and review allowances, and stagnation thresholds
  (`realign_after`, `circuit_break_after`).

The envelope is fixed at admission with `tools/canopus_task.py admit` and is
evaluated by `tools/convergence.py`. Use `templates/task-issue.md` to record
it in the task's Issue.

## Bounded convergence contract

- Delegated sessions, reviewers, executors, handoffs, and fresh sessions
  inherit the envelope. None may add acceptance items, scope, allowances, or
  time.
- Widening the envelope requires re-admission by the same owner. Mutation under
  the old admission stops until then.
- **Progress** is only an accepted acceptance item or a resolved blocker.
  Commits, tests, reviews, turns, tokens, handoffs, and new findings are
  activity. Activity never resets stagnation.
- Allowances only decrease and never replenish.
- A reviewer classifies each finding. An in-scope defect may use the finite
  corrective path. An out-of-scope finding is recorded as deferred evidence
  and never becomes work in this task.
- States and their meaning:
  - `HEALTHY`: progress inside the envelope; continue.
  - `WATCH`: a cycle ended without progress; continue, narrowed.
  - `REALIGN`: drift, a scope change, or the realign threshold; alignment work
    only. A corrective or scope change while in `REALIGN` breaks the circuit.
  - `CIRCUIT_BREAK`: exhausted allowance, a repeated blocker family, or the
    stagnation threshold; stop mutation and return the decision to the owner.
  - `COMPLETE`: every frozen acceptance item is satisfied; stop.
- At `COMPLETE`, stop. Optional hardening, refactoring, or cleanup is a new,
  separately admitted task.
- A fresh session, engine, or machine never resets `REALIGN`,
  `CIRCUIT_BREAK`, or spent allowances. State lives in the task record, not the
  session.

## New-component gate

Before proposing a new durable component (tool, schema, service, dashboard,
adapter, or subsystem) for a control plane or shared platform, classify it:

- **Vendor commodity** (generic agent loop, memory, scheduler, orchestration,
  browser use): default is do not build; adopt the vendor version.
- **Adapter** (to an engine, forge, or notifier): build thin and swappable, with
  no owner-specific logic inside.
- **Owner-specific control** (ownership graph, rules, boundaries, evidence,
  recovery, routing): the only class worth deep investment.

Then answer all four questions in the proposing Issue:

1. Has this solved a real, observed friction at least twice?
2. What specific decision or action does it change?
3. Why can it not stay with the project that has the friction?
4. Could it be unplugged within a day once a vendor ships the native version?

A proposal that cannot answer all four defaults to `WATCH`, `DEFER`, or
`NO CHANGE`. Architectural completeness, future possibility, or a vendor
buzzword is not evidence. An accepted proposal starts as the smallest trial
with a stated rollback or retirement trigger.

## Practice selection

- **SDD:** intent must survive sessions or split across tasks. Evidence:
  requirement-to-task-to-verification traceability.
- **Behavior examples:** acceptance language or policy boundaries are
  ambiguous. Evidence: examples including failure and boundary cases.
- **TDD:** deterministic logic, parsers, migrations, regressions, security
  invariants. Evidence: a failing test before the fix when feasible.
- **Domain modeling:** vocabulary and invariants are genuinely complex. Do not
  force layers onto a simple utility.
- **ADR:** a decision affects structure, interfaces, persistence, dependencies,
  or non-functional qualities. Do not record routine choices.

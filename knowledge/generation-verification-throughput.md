# Verification, not generation, sets delivery throughput

## Type

Knowledge note.

## Scope

Teams or individuals scaling agent-assisted code generation while review, CI,
environments, and human judgment time stay roughly fixed.

## Problem shape

Agents raise code-generation speed sharply; the rest of the pipeline does not
speed up with them. Two failures follow. A backlog of generated but unverified
changes forms, with low-risk work queued behind high-risk work. And ambiguous
requirements are amplified rather than caught: a vague request becomes a
large, plausible, wrong change before anyone reviews it.

## Guidance

Model delivery as two coupled stages, generation and verification, and treat
the slower one as the ceiling. Invest in verification before adding
generation capacity:

1. **Intent first.** A short task artifact with intent, constraints, and
   testable acceptance before generation, so a misunderstanding is caught while
   it is cheap. In Canopus this is the task Issue and its envelope.
2. **Plan before change.** A short plan (what changes, what depends on what,
   what the risk is) so drift is caught at design-review cost.
3. **Reproducible, isolated environments** per task, so runs replay and
   parallel tasks cannot corrupt each other.
4. **Risk-tiered checks.** Fast checks for low risk; full checks plus human
   approval for money, permissions, data migration, or anything irreversible.
5. **Evidence-first review.** Each change states what it implements, what was
   tested, what was not, its risk tier, and its rollback, so reviewers spend
   judgment on risk rather than reconstructing context.
6. **Capability is not permission.** Separate what an agent may do alone
   (read, test, draft) from what needs a human or a hard gate (protected
   merge, production data, infrastructure). Log consequential actions.
7. **Close the loop.** Feed production signals back into the task artifacts
   and tests so the next similar task starts from corrected ground truth.

## Validation

Track cycle time from proposal to merge, CI queue and run time, defect and
rollback rate, and whether high-risk changes consistently carry complete
evidence. Do not use change count or lines of code as the success metric: both
reward the generation stage and hide a growing verification backlog.

## Limits and failure modes

- Where change volume and review capacity are already low and matched, this
  adds overhead with no queue to drain.
- A team with no tests, CI, or review should build that baseline first.
- When verification lags, throttle generation (limit tasks in flight); do not
  accept an unreviewed backlog or skip review under time pressure.
- Skipping the intent or plan step "to save time" moves rework later and makes
  it larger.

## Related guidance

- [`../playbooks/validation-throughput.md`](../playbooks/validation-throughput.md)
- [`agent-tool-call-baselines.md`](agent-tool-call-baselines.md)

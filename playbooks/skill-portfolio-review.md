# Skill portfolio review

## Purpose

Keep the set of agent skills small, well-routed, and owned. Every active skill
and plugin-provided skill competes for discovery attention in every session,
so a reusable lesson should not automatically become a permanent skill.

## When to run

- Monthly, and after: a wrong or missed skill invocation that repeated, a
  skill-list truncation warning, a major host upgrade, a security concern, or
  a workflow that keeps needing the same manual instructions.
- The review is read-only. Accepted changes are applied afterward, by the
  owner, in the skill's canonical source.

## Procedure

1. **Refresh sources.** Check the host's current skill and plugin docs and the
   installed version. Map new vendor terms to existing primitives before
   adopting a new label.
2. **Inventory discovery cost.** Count active skills per scope, measure total
   description size, and note any truncation or omission warning.
3. **Check ownership.** Move single-project behavior to project scope. Keep
   only cross-project workflows in personal or shared scope. List duplicates
   and ambiguous names.
4. **Test routing.** For each changed or disputed description, run two or
   three prompts that must trigger it and two or three nearby prompts that
   must not. It passes only if it preserves or beats the recorded baseline.
5. **Inspect load cost.** The main instructions hold one workflow with inputs,
   outputs, verification, failure handling, and stop conditions. Optional
   detail moves to on-demand references.
6. **Set invocation policy.** Keep implicit invocation only for specific,
   routinely useful skills. Make ambiguous, costly, destructive, or rare ones
   explicit-only or disabled.
7. **Decide.** One of `adopt`, `trial`, `watch`, `reject`, `retire`, with
   evidence, owner, next review date, and rollback.
8. **Apply separately.** After approval, change the canonical source, rerun the
   routing prompts, and restart the host only if required.

## Output

With nothing actionable, report one line: `SKILL PORTFOLIO | GREEN | <date>`.
Otherwise list only actionable rows:

```text
decision  skill            evidence                          action                   approval
retire    csv-cleanup      0 invocations in 60 days          disable, keep in history owner
trial     release-notes    missed 3 of 5 positive prompts    rewrite description      owner
```

Never auto-install a suggested skill, and never promote a session lesson
straight to a skill: start from
[`skill-candidate.md`](../templates/skill-candidate.md).

## Validation

- No two active skills claim the same trigger.
- Positive and negative routing prompts pass for every changed description.
- No unexplained truncation warning.
- Disabled or retired skills remain recoverable from version history.

## Rollback

Restore the previous version or invocation policy when a change causes missed
routing or removes a needed capability. If disabling a plugin also removed a
needed tool, re-enable it. Record the reversal at the next review.

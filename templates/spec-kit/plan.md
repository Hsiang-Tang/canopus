# <Feature name> plan

<!--
Save as docs/specs/<slug>/plan.md next to spec.md. Say HOW the requirements
will be met and what could go wrong. Move a durable, cross-feature decision
into an ADR and link it here instead of burying it.
-->

## Baseline

<!-- What exists today, measured where it matters (latency, size, coverage). -->

## Risk and authority

- Risk: `<R1 | R2 | R3>` because <consequence if this goes wrong>
- Authorized without further approval: <reversible steps, e.g. edit, test, commit, push to approved remote>
- Human gate: <release, migration, public exposure, anything irreversible>
- Failure posture: <fail closed | degrade to X | roll back to Y>

## Design

- `<component or file>` owns <responsibility>.
- `<component or file>` owns <responsibility>.
- Interfaces changed: <none | list with consumers affected>

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| <option> | <reason> |

<!--
New-component gate: a new tool, service, or abstraction must answer all four.
Observed friction twice or more? Which decision changes? Why not the project
owner's existing mechanism? Removable within a day if a vendor ships it?
-->

## Verification

- Edit loop: `<command>`
- Integration: `<command>`
- Merge candidate: `<command>`
- Release: `<gate or none>`

## Rollback

<How to return to the previous safe state, and how you would know you need to.>

## Decisions

- <ADR link or "none">

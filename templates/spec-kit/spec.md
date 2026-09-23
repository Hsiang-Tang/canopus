# <Feature name> requirements

<!--
Save as docs/specs/<slug>/spec.md. Required from risk R2 upward; optional for
R1. Say WHAT must be true, not HOW. Every requirement must be checkable by a
test, a command, or a named human observation.
-->

- Status: `<draft | accepted | superseded by <slug>>`
- Owner: `<person-or-team>`
- Risk: `<R1 | R2 | R3>`
- Task Issue: `<issue-url>`

## North Star

<!-- One sentence: the observable outcome for a user or operator. -->
<Who> can <do what> so that <why it matters>.

## Assumptions

<!-- For an ambiguous request, list 3-5 before accepting the spec. -->

| Assumption | Cost if wrong |
| --- | --- |
| <assumption> | <what breaks or must be redone> |

## Requirements

- **<PREFIX>-001 — <name>:** <observable behavior, including the boundary case>
- **<PREFIX>-002 — <name>:** <observable behavior>
- **<PREFIX>-003 — <failure or recovery behavior>:** <what happens on error>

## Acceptance

<!-- These IDs become the frozen `acceptance` list in the task envelope. -->

- `AC1` <positive case> — verified by `<command or observation>`
- `AC2` <negative or boundary case> — verified by `<command or observation>`
- `AC3` <recovery case> — verified by `<command or observation>`

## Scope

- In scope: `<modules, paths, or contracts>`
- Non-goals: <what this work explicitly will not do, even if tempting>

## Open questions

- <question> — owner: `<who decides>`, needed by: `<task id or milestone>`

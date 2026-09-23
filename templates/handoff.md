# Handoff: <TASK-ID>

<!--
Write this when a session ends before the task closes: context is heavy, the
engine or machine changes, or the task is stopped. Post it as a comment on the
task Issue (or save under docs/handoffs/ if the project keeps them in Git).
Start from `canopus_task.py handoff --task <TASK-ID>` and add only what the
machine state cannot hold. The next session must be able to continue from this
plus the repository, with no access to the old chat.
-->

## Machine state

<!-- Paste the output of: python3 <canopus-root>/tools/canopus_task.py handoff --task <TASK-ID> -->

```text
<agent handoff block>
```

## Objective (unchanged)

<North Star, copied from the task Issue. If it changed, this is not a handoff:
the task needs re-admission.>

## Done, with evidence

- `AC1` accepted — `<test name or command and result>`
- <other completed step> — `<evidence>`

## Git state

- Branch / worktree: `<branch>` / `<worktree-id>`
- Last commit: `<sha> <subject>`
- Uncommitted or unpushed: `<none | paths>`

## Open

- Remaining acceptance: `<AC2, AC3>`
- Blockers: `<family: description | none>`
- Deferred findings (not work): `<list | none>`
- Residual risks: `<list | none>`

## Next action

<Exactly one concrete step, and the command that verifies it.>

## Successor instruction

<!-- Copy from the machine state. After a stop it forbids mutation. -->
`<continue | alignment only | stop: owner decides>`

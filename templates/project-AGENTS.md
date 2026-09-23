# <project-name> agent rules

<!--
Copy to the project root as AGENTS.md. This file is canonical for every agent.
Add a root CLAUDE.md that contains only `@AGENTS.md` so Claude Code imports it
instead of keeping a second copy. Replace every <placeholder>; delete sections
that do not apply. Keep it short: agents read this on every session.
-->

## Ownership and scope

- Owner: `<person-or-team>`
- Canonical repository and remote: `<org>/<repo>` (the only approved push target)
- Data class: `<public | internal | restricted>`; restricted data never leaves
  approved systems, whichever engine or machine processes it.
- Default risk: `<R0 | R1 | R2 | R3>` (see Development practice below)
- Project rules override generic Canopus rules for project-specific behavior.

## Startup order

Read only what the current task needs, in this order:

1. `AGENTS.md` (this file)
2. `README.md`
3. `docs/ARCHITECTURE.md` and the ADR index in `docs/adr/`
4. The active spec: `docs/specs/<slug>/spec.md`, `plan.md`, `tasks.md`
5. `docs/VERIFICATION.md`
6. `docs/STATUS.md`
7. Live Git state: identity, remote, branch, worktree, uncommitted changes

Resume from these files and the task's Issue, never from an earlier chat.

## Authority and stops

- An explicit request to change, fix, or build authorizes the complete
  reversible chain inside the admitted envelope: edit, test, fix, verify,
  commit, and push to the approved remote.
- Stop and ask for: credentials or OTP, account, legal, or purchase decisions,
  scope or acceptance changes (these need re-admission), new public exposure,
  an unapproved remote, or any irreversible external action.
- Out-of-scope findings are recorded as deferred proposals, not implemented.

## Development practice

| Risk | Meaning | Required artifacts |
| --- | --- | --- |
| R0 | read-only or explanatory | none |
| R1 | local, easily reversed | task issue with acceptance |
| R2 | shared contract or durable state | spec + plan + tasks; ADR if a decision is durable |
| R3 | release, migration, security, privacy, user data | R2 + rollback plan + human review |

- For an ambiguous request, state 3-5 assumptions and the cost of each being
  wrong before building.
- New component gate: add a tool, service, or abstraction only if the friction
  was observed at least twice, a named decision changes because of it, and it
  could be removed within a day. Otherwise record it as WATCH or DEFER.
- Code comments state technical intent. Put durable "why" in `plan.md` or an
  ADR, never conversation history in source.

## Verification

- Edit loop: `<fast focused command>`
- Integration: `<affected boundary command>`
- Merge candidate: `<full repository command>`
- Release candidate: `<release-only gates, or none>`
- Evidence invalidators: `<dependency lock | schema | build config | toolchain>`

Do not replay valid evidence for unchanged inputs. Escalate to the full gate
when impact is uncertain.

## Canopus task discipline

- Formal tasks are admitted with a frozen envelope (North Star, acceptance,
  scope, finite allowances) from a task Issue:
  `python3 <canopus-root>/tools/canopus_task.py admit --task <id> --envelope <file.json>`
- Record progress only as accepted items or resolved blockers; commits, test
  runs, and reviews are activity.
- End every substantial response with the current Owner Footer:
  `python3 <canopus-root>/tools/canopus_task.py footer --task <id>`
- On `REALIGN`, do alignment work only. On `CIRCUIT_BREAK` or `COMPLETE`, stop
  and hand the decision back to the owner.

## Git

- One writer per checkout. Parallel writers use separate branches and
  worktrees with declared, non-overlapping mutation scopes.
- Commit identity: `<name> <noreply-email>`; trailers: `<policy>`.
- Inspect staged paths and the staged diff before every commit.

## Boundaries

- Never commit secrets, `.env` files, machine-local manifests or inventories,
  raw transcripts, logs, caches, or build output.
- Reusable lessons leave this project only after de-identification and human
  review (see `templates/portable-knowledge-candidate.md` in Canopus).

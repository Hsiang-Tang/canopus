# Canonical state lives with owners; execution nodes are replaceable

## Type

Knowledge note.

## Scope

Development systems that span several sessions, machines, remote shells, CI
runners, or agent engines.

## Problem shape

The machine or chat where most work happens starts to look like the system's
authority. Recovery then depends on one checkout, one local config, or one
conversation, and "synchronized" can be declared while intent or unresolved
work is still trapped in a node that may disappear.

## Guidance

Map every class of durable state to one owner, and treat everything else as a
consumer:

| State | Durable owner |
| --- | --- |
| Generic agent policy | Version-controlled control plane (this repository) |
| Requirements, architecture, tasks, evidence | The project repository and its tracker |
| Task progress and next action | The task Issue plus its task record and footer |
| Reusable judgment | A reviewed rule, playbook, note, or skill source |
| Credentials and restricted data | An approved secret store or local-only location |
| Machine paths and lifecycle mapping | An untracked, machine-local manifest |
| Recovery | Verified remote history and tested backups |

Machines, checkouts, sessions, worktrees, engines, and runners may cache or
transform that state. They never become its sole holder. The brain (planning,
review, judgment) and the executor (change, test, deliver) are roles any
capable engine can fill, because the task's identity is its Issue, not the
session that happens to be running it.

Architecture test:

> Can a fresh, authorized session on a different machine reconstruct the
> rules, project state, open work, and required local pointers without the old
> chat or the original machine?

If not, find the state with no durable owner before adding automation or
concurrency.

## Validation

1. Start a fresh session in an isolated checkout.
2. Resolve the control plane through its registered pointer, not a fixed path.
3. Recover the spec, status, and open work from the repository and the Issue.
4. Restore only the pointers and secrets that cannot live in Git.
5. Run the smallest representative check and compare it with recorded evidence.

A successful recovery proves more than the health of the original machine.

## Limits and failure modes

- Git history is not a backup for durable non-source data.
- A hosted remote is wrong when policy marks the work local-only or assigns a
  different owner.
- Synchronizing incomplete or unsafe state spreads the problem.
- Too many always-loaded instructions make the control plane itself a context
  burden; keep mandatory rules short and load detail on demand.

## Related guidance

- [`notes-and-searchable-history-over-lossy-compaction.md`](notes-and-searchable-history-over-lossy-compaction.md)
- [`../rules/workspace.md`](../rules/workspace.md)

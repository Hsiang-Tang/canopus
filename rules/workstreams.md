# Parallel workstreams

Parallel writers are supported only when each has a declared workstream, an
isolated branch and worktree, and a mutation scope that does not collide with
another. The declaration coordinates work; it does not launch agents, take a
lock, merge branches, or grant authority.

Tool: `python3 tools/workstream.py check` reads `workstreams/*.toml` and
reports collisions. Procedure: `playbooks/parallel-workstreams.md`.

## One writer per checkout

- A checkout has at most one writing agent at a time. Any other agent in that
  checkout is a read-only reviewer.
- Two writers never share a branch or a worktree.
- This holds across engines: a Codex session and a Claude Code session in the
  same checkout are two writers.

## Declaration

Each workstream is one file `workstreams/<id>.toml` with:

- `id`: stable, unique identifier.
- `owner_role`: the role that writes (for example `executor`), not a person or
  session.
- `branch` and `worktree`: unique to this workstream. The worktree value is a
  repository-relative or symbolic name, never an absolute local path.
- `mutation_scope`: repository-relative globs this workstream may change.
- `depends_on`: IDs of workstreams that must integrate first.

A declaration is a coordination claim. It never authorizes changing a path the
task is otherwise not allowed to change.

## Allocation

Before a second writer starts:

1. Split the objective into concern-sized workstreams, each tied to one Issue.
2. Route each one under `model-routing.md` if engine choice matters.
3. Declare exact mutation scopes. Prefer narrow globs.
4. Fetch the remote, create the branch and worktree from a recorded base
   commit, and commit the declaration before material mutation.
5. Run `python3 tools/workstream.py check`. It reports:
   - overlapping mutation scopes;
   - a shared branch or worktree;
   - a dependency cycle;
   - a dependency on an undeclared workstream;
   - one-writer violations.
   Any finding needs an explicit decision before the affected work proceeds.

## Semantic collisions

- Different files can share a contract (a schema and its consumer). Declare
  the dependency and merge order, or record why the contracts are
  independent.
- Shared hotspots (indexes, changelogs, required-file lists) should use
  per-change fragments where the repository supports them. Otherwise the
  integration owner edits them once, at integration.

## Execution

- Checkpoint the workstream's Issue after any change of ownership, scope,
  dependency, status, commit, or next action. A chat message is not a
  checkpoint.
- Before marking a workstream ready, check the diff against its base and its
  declared scope. Any path outside the scope is a defect.
- A stale checkpoint is an observation, never an automatic release. Inspect
  branch, worktree, Issue, and handoff evidence before reassigning.
- An abandoned workstream records its resume commit, completed and remaining
  work, and recovery notes. Its scope is not released until a successor names
  it explicitly.

## Integration

- One integration owner fetches current refs, checks dependency order, reviews
  semantic interactions, and integrates one branch at a time.
- Run the full verification contract on the merged candidate. A green branch is
  not a green integration, and "ready" is not permission to merge.
- After integration, the workstream's claim ends; its record stays as history.

## Recovery

- Every field is human-readable, so the protocol works by hand if the tool
  fails.
- Never delete another workstream's branch or worktree during takeover.
- Removing a declaration file never silently releases a scope held by an
  unmerged branch.

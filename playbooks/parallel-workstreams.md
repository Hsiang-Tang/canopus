# Parallel workstreams

## Purpose

Let two or more agent sessions work at the same time without editing the same
files, sharing a checkout, or merging in the wrong order. This extends the
one-writer-per-checkout rule with declared scopes and a collision check.

## Rules

- One writer per checkout. Each writer gets its own branch and worktree.
- Every workstream declares its mutation scope before it edits anything.
- Collisions are stop conditions for the affected pair, not warnings.
- A stale or silent workstream is inspected; it never authorizes takeover.
- One named integration owner merges, in dependency order, and runs the final
  merged gate. Passing independently does not prove passing together.

## 1. Declare

Create one file per writer under `workstreams/` in the repository:

```toml
# workstreams/export-api.toml
id = "export-api"
owner_role = "executor"
branch = "feat/export-api"
worktree = "wt-export-api"          # an abstract id, not a filesystem path
mutation_scope = ["src/export/**", "tests/test_export*.py"]
depends_on = []
```

```toml
# workstreams/export-docs.toml
id = "export-docs"
owner_role = "executor"
branch = "docs/export"
worktree = "wt-export-docs"
mutation_scope = ["docs/export/**"]
depends_on = ["export-api"]
```

Use the narrowest globs that cover the work. Use `/**` only for a whole
subtree you truly own.

## 2. Check before anyone writes

```sh
python3 <canopus-root>/tools/workstream.py check
```

Run it from the repository root that holds `workstreams/`. It reports:

- overlapping mutation scopes;
- a branch or worktree shared by two workstreams (one-writer violation);
- a dependency on an undeclared workstream;
- a dependency cycle.

Fix the declarations until the check is clean. Then create the branches and
worktrees:

```sh
git fetch origin
git worktree add ../wt-export-api -b feat/export-api origin/main
git worktree add ../wt-export-docs -b docs/export origin/main
```

## 3. Work

- Each session admits its own task (`canopus_task.py admit`) and stays inside its
  declared scope.
- If a session needs a path outside its scope, it stops and asks; the owner
  either re-declares scopes (and reruns `check`) or defers the change.
- Before its final checkpoint, compare the branch diff with the declaration:
  `git diff --name-only origin/main...HEAD` must fall inside `mutation_scope`.

## 4. Integrate

The integration owner fetches, merges in `depends_on` order one branch at a
time, reviews shared contracts, and runs the merge-candidate gate after the
last merge. A stacked pull request names its base and merge order.

## 5. Recover an abandoned workstream

Keep its branch and worktree. Write a [handoff](../templates/handoff.md) on its
task Issue and close the task with `--outcome handoff`. A successor declares a
new workstream that names the old id, verifies the handoff commit, and only
then continues. Deleting the old worktree is a separate, later decision.

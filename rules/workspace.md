# Workspace invariants

`tools/workspace_doctor.py --manifest <path>` checks the invariants in this
file. It reports drift and never repairs, moves, deletes, commits, or pushes
files.

## Manifest

- Every registered project has one relative path and one stable synthetic-safe
  identifier in the local manifest.
- The manifest separates ownership class, sensitivity, canonical source,
  lifecycle, remote policy, and backup expectation.
- The manifest itself is machine-local. Only the synthetic example is tracked.
- A missing required field, a duplicate ID or path, an escaping path, or a
  remote allowlist declared together with `remote_policy = "none"` is an
  error.
- A manifest the doctor cannot parse blocks all work until fixed
  (`session.md`, bootstrap step 5).
- Machine-local manifests may name real projects and paths. That is allowed
  because they never leave the machine; de-identification applies to portable
  content, not to the local manifest.

## Topology

- Top-level workspace entries must be in the declared allowlist.
- Unknown Git repositories inside the workspace are errors unless they are
  declared dependency trees or linked worktrees governed by a registered Git
  owner.
- A registered project path must exist, and a project declared as Git-backed
  must have Git metadata.
- Downloads and chat attachments are transport locations, not canonical
  roots. New external files enter the inbox before classification. Files older
  than `inbox_max_age_days` produce a warning.

## Git identity and remotes

- A repository-local identity must match the manifest when an expected email is
  declared.
- Required remotes must exist. Forbidden remotes must not exist. Every fetch
  and push URL must remain inside the declared host and URL-prefix allowlists.

## Instruction bridge

- A project used by both Codex and Claude Code keeps `AGENTS.md` as the
  canonical rule file. A root `CLAUDE.md` must import it with `@AGENTS.md`;
  the doctor reports a `CLAUDE.md` that does not.
- The doctor verifies only the root bridge. It does not prove nested
  instruction discovery, settings precedence, or hook behavior; inspect those
  engine-native surfaces directly when they matter.

## Generated output

- A thousand or more pending paths is an invariant error because it usually
  signals an uncontained generated-output tree.
- Before a tool first writes to a repository-local build, export, or cache
  root, confirm the exact root is ignored (test a sentinel path with
  `git check-ignore`). A nested ignore pattern does not cover a root-level
  directory.
- Keep source, durable data, generated artifacts, and disposable cache in
  separate trees.

## Canonical state and replaceable machines

- Canonical state lives in its durable owner: this repository for generic
  policy, the target repository and tracker for project truth, and approved
  secret or machine-local stores for data that must not enter Git.
- A laptop, checkout, session, remote shell, or CI runner is a replaceable
  node. A recovery claim is valid only when a fresh authorized node can rebuild
  rules, project state, and unresolved work without the old chat or machine.
- Tools resolve paths from the repository root, configuration, or environment,
  never a machine-specific absolute path. Instructions must not assume a fixed
  directory depth.

## Destructive operations

- Before any destructive command, list the target immediately beforehand. Do
  not rely on an earlier listing in the session.
- On a case-insensitive filesystem, never batch names that differ only by case
  into one `rm`, `mv`, or `cp`. Rename case-only through a non-colliding
  intermediate name and verify after each step.
- A directory with no remote and no backup needs its scope and expected
  outcome confirmed before any rename or delete near it.

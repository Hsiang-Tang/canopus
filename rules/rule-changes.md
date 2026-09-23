# Rule changes

Rules change through a reviewed, reversible process. A rule that changes in a
chat is not a rule.

## Candidate

- Capture the idea as a `rule-inbox` Issue: trigger (the observed friction),
  proposed rule, scope, expected benefit, conflicts, and data boundary.
- A candidate has no authority. Sessions do not follow it until adopted.
- One-task preferences stay in that task. Only durable behavior becomes a rule.

## Review

Answer before adoption:

- Is this durable, or a one-task preference?
- Is it generic, personal, or owned by an employer or other restricted owner?
  Only generic content belongs in a shared rule set.
- Which existing rule does it extend, conflict with, or supersede?
- What changes for existing projects and running sessions?
- Can a tool enforce it instead of a model remembering it
  (`docs/methodology/deterministic-enforcement.md`)?
- How is it verified, and how is it rolled back?

A rule that adds a new durable component also passes the new-component gate in
`development.md`.

## Adoption

- Work on a `rules/<lowercase-kebab-topic>` branch.
- Update the canonical rule file, `rules/index.md` when a family is added or
  its loading trigger changes, and the tool that enforces it, in the same
  change.
- Add a changelog fragment under `changelog.d/` instead of editing
  `CHANGELOG.md` directly. `python3 tools/compile_changelog.py` folds fragments
  into `CHANGELOG.md` at release. Fragments avoid merge conflicts when several
  sessions change rules at once.
- Add new files to `control-plane.toml` `validation.required_files`.
- Run `python3 tools/validate.py`.
- Merge only a reviewed, internally consistent change.
- Record an ADR in the target project when the change alters architecture, not
  merely agent behavior.

## Writing the rule

- State the current rule only. History, rationale for past versions, and
  incident narratives belong in the changelog or an ADR.
- Keep it checkable: a reviewer can tell from evidence whether it was followed.
- Name the enforcing tool and its exact command when one exists.
- Put the "why" in `docs/methodology/` and link to it.

## Versioning

- **Patch:** a clarification with no behavior change.
- **Minor:** a new compatible rule, template, or tool.
- **Major:** a rule that invalidates an existing workflow or requires
  migration. A major change states the migration steps.

## Supersession and rollback

- Never silently delete a rule or edit history to make an old rule appear never
  to have existed. Mark the replacement in the changelog.
- Rollback is a revert of the adoption change plus its changelog fragment.
  Rules whose tools hold state (latches, task records) state how to roll the
  state back or why it is safe to leave.

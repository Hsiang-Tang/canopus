# Changelog fragments

Branches that all edit the same `## Unreleased` lines of `CHANGELOG.md`
conflict on every merge. Each change therefore adds one small fragment file
here instead, and `tools/compile_changelog.py` folds them in at release time.

## Rules

- One change, one file: `changelog.d/<short-slug>.<category>.md`.
- `<category>` is one of `added`, `changed`, `deprecated`, `removed`,
  `fixed`, `security`.
- The file holds one or more `- ` bullets; wrap long bullets with an
  indented continuation line. No headings.
- Describe the user-visible effect, not the internal history of the change.
- An empty directory (only this README) is the normal state between releases.

## Example

`changelog.d/csv-export.added.md`:

```markdown
- Export the weekly report as CSV, including a header row for empty weeks.
```

## Commands

```bash
python3 tools/compile_changelog.py --check     # exit 1 if fragments are pending
python3 tools/compile_changelog.py --dry-run   # print the merged CHANGELOG.md
python3 tools/compile_changelog.py             # merge under "## Unreleased", delete fragments
```

All fragments are validated before anything is written; one malformed
fragment leaves both `CHANGELOG.md` and every fragment untouched.

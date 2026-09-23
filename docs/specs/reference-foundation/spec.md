# Workspace foundation requirements

## Outcome

Give every machine that runs Canopus a closed configuration contract, scoped
registration, and read-only workspace validation, so agents always load the
same rules and never leak machine-specific or private details into Git.

## Requirements

- **REF-001 — Closed configuration:** A versioned control-plane file declares
  product identity, startup order, registration pointers, and required files;
  invalid or incomplete configuration fails deterministically.
- **REF-002 — Scoped registration:** A machine can resolve and register the
  reference checkout and an optional manifest pointer without copying manifest
  contents or changing unrelated configuration.
- **REF-003 — Federated manifest:** A versioned manifest records route,
  ownership, sensitivity, source, lifecycle, backup expectation, identity, and
  remote policy while project content remains with its owner.
- **REF-004 — Read-only validation:** Workspace validation detects structural,
  governance, repository, identity, remote, linked-worktree, generated-output,
  and stale-intake drift without mutating the workspace.
- **REF-005 — Privacy-aware delivery:** Candidate files exclude secrets,
  machine-user paths, real inventories, non-placeholder email addresses,
  restricted artifacts, and uncertain source-bound material.
- **REF-006 — Synthetic examples:** Checked-in examples and tests use only
  fictional data and reserved example domains.
- **REF-007 — Reproducible evidence:** The exact candidate passes validators,
  unit tests, Python compilation, tracked-files review, privacy scanning, and a
  clean-checkout execution before delivery.


## Negative and boundary cases

- An unknown Git repository inside the workspace is an error.
- A linked worktree governed by a registered repository is not a duplicate
  project, but its pending changes remain visible.
- A required remote with no URL, a forbidden remote, an unapproved host, or an
  out-of-scope fetch or push URL is an error.
- A missing governance field or escaping relative path is an error.
- A thousand pending paths is an error rather than an ordinary warning.
- A clean scanner result does not authorize publication.
- Registration removal deletes pointers only and never deletes files.

## Non-goals

This feature does not migrate a real workspace, install an automation,
aggregate project data, host a service, manage secrets, or publish a package.

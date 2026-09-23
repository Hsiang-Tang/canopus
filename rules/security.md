# Security and privacy boundary

## Secrets and local state

- Keep secrets in an approved secret manager or local environment, never Git.
- Keep machine inventories, exact local paths, logs, databases, credentials,
  and private project records outside this repository.
- A manifest records routing metadata; it does not authorize copying project
  contents across ownership boundaries.
- Public examples and tests use synthetic identifiers and reserved example
  domains only.

## Ownership boundaries

Every project belongs to one ownership class, declared in the workspace
manifest: personal, employer (or other restricted owner), or public.

- Employer-owned or otherwise restricted material stays in its approved
  repository, tracker, and remote. A personal host is never an approved
  employer remote.
- Never move source, project identifiers, architecture, tickets, credentials,
  device data, logs, customer data, transcripts, or internal URLs across that
  boundary.
- Privacy-sensitive local-only projects stay off hosted remotes entirely.
- Authorship does not grant disclosure rights. Keep a work product in its owner
  unless disclosure permission is explicit.
- When disclosure safety is uncertain, leave the material with its source owner
  and require human review. Convenience never justifies crossing a boundary.

## Processing versus storage

These are separate questions. Answer both.

- **Processing:** may an authorized AI session read and act on this material
  where it lives? That is decided by the source owner's own approved-tool and
  data policy, not by this control plane.
- **Storage:** may the material, or anything derived from it, be written,
  synchronized, published, or promoted somewhere else? The boundaries in this
  file decide that.
- Processing permission never implies storage permission.
- Apply the same rule to every AI engine. No engine receives a permission
  another is denied, and this control plane invents no extra provider ban the
  source owner did not define.

## Federated governance

- The control plane governs routing, lifecycle, and generic practice. It is not
  a warehouse for governed projects' content.
- Full project truth (instructions, architecture, decisions, requirements,
  status, evidence) stays in the project's own repository or tracker.
- Status output, footers, handoffs, and automation reports must not disclose
  project identifiers, local paths, remote URLs, detailed private findings, or
  sensitive values by default (`canopus.toml` `[status]`).

## Portable knowledge

- A lesson leaves its source boundary only as a de-identified candidate that
  the owner reviews and submits from an environment where it is allowed to
  exist. The full procedure is `knowledge-promotion.md`.
- Never upload a candidate from a restricted environment into a personal or
  public system automatically.
- Reject candidates containing identifying nouns, source excerpts, unique
  values, topology, timings, incidents, or behavior that could reconstruct the
  source.

## Restricted data classes

- Credentials, personal data, and regulated records are restricted by default
  in every project.
- A manifest may index a restricted project by path. It must not embed its
  values, identifiers, report contents, or credentials.
- Permission to analyze restricted data never authorizes logging in to an
  external system, transmitting records, or executing a transaction.

## Harness integrity

The agent's own configuration is an attack surface, not only the code it edits.

- Treat global and project instruction files, hook scripts, hook entries in
  settings files, and tool-server configuration as security-relevant. Review
  diffs to them like code.
- Install hooks and managed instruction blocks only through
  `tools/install_bootstrap.py`, which writes idempotent, clearly delimited
  managed content and preserves everything else.
- A hook that blocks must have a known-bad test as well as a known-good one,
  and must fail open on its own internal error rather than lock out all work.

## Public repositories

- Public visibility makes every committed object a disclosure surface. A clean
  working tree does not prove history is sanitized.
- Do not enable static-page hosting, publish releases or packages, add
  collaborators, or change visibility during ordinary development.

## Before delivery

Run `python3 tools/audit_publication.py` (with any source-specific `--deny`
terms passed on the command line, never stored in the repository), inspect all
tracked files, and review the staged diff. A clean automated result never
replaces ownership and disclosure review.

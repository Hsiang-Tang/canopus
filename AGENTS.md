# Canopus agent rules

## Scope

- This repository is Canopus, an open framework for running AI coding agents
  with discipline.
- Keep it self-contained, synthetic, standard-library-only, and safe for its
  current public visibility.
- Add only capabilities required by an active specification.
- Treat every tracked file and every commit as immediately public, and have a
  human review the full diff before any public push.

## Startup order

Read `README.md`, `docs/ARCHITECTURE.md`, the active specification under
`docs/specs/`, `docs/VERIFICATION.md`, `docs/STATUS.md`, and live Git state
before changing behavior.

## Boundaries

- Never commit secrets, credentials, cookies, private keys, `.env` files,
  machine-local inventories, private remote URLs, real customer or employer
  data, personal notes, transcripts, logs, caches, databases, or build output.
- Examples and tests use only synthetic names, paths, URLs, and records.
- Machine-local manifests stay outside Git. The checked-in manifest is a
  synthetic fixture only.
- Preserve federated ownership: a manifest routes to project owners but never
  grants permission to copy their data.
- Unknown disclosure safety fails closed: omit the material and request human
  review.
- Do not enable Pages, publish releases or packages, add collaborators, or
  change repository visibility as part of ordinary development.

## Development and verification

- Requirements, design, and task state live in
  `docs/specs/reference-foundation/`, `docs/specs/bounded-convergence/`, and
  `docs/specs/framework-core/`.
- Architecture decisions live in `docs/adr/`; accepted decisions are preserved
  rather than silently rewritten.
- Keep runtime dependencies to the Python standard library unless an accepted
  specification changes that constraint.
- Run the complete verification contract before delivery:

  ```sh
  python3 tools/validate.py
  ```

- Hosted CI is intentionally absent. Run validation locally and repeat it from
  a clean checkout of the exact delivery commit.

- Inspect staged paths and the staged diff before every commit. Push only to
  the verified owner remote.
- Commit identity and AI-attribution policy follow `rules/git.md`.

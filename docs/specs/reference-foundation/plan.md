# Workspace foundation plan

## Design

- `control-plane.toml` owns the closed file and startup contract.
- `canopus.toml` owns machine-verifiable state and disclosure defaults.
- `register_machine.py` owns two namespaced path pointers.
- `workspace_doctor.py` owns read-only manifest and observed-state comparison.
- `audit_publication.py` owns deterministic publication-hazard patterns plus
  caller-supplied deny terms.
- The checked-in example is self-contained and non-Git; tests create temporary
  Git owners for boundary behavior.

## Risk

- Risk: a public repository that must never carry machine paths, inventories,
  or credentials.
- Failure posture: exclude uncertain content; unknown state is an error, never
  inferred success.

## Verification strategy

Use known-good and known-bad unit fixtures, run all repository validators, scan
the tracked file set, then clone the pushed commit into a disposable directory
and repeat the main gate.

## Rollback

Revert a faulty change with a new commit. If sensitive material ever enters
history, treat it as exposed: rotate any affected credential first, then remove
it through a reviewed recovery procedure.

# ADR-0001: Federated state and trust boundaries

- Status: Accepted
- Decision: Keep portable governance in this repository, machine routing in a
  local manifest, and full project truth with each project owner.

## Context

Centralizing project content can simplify retrieval but duplicates truth and
increases disclosure, conflict, and recovery risk.

## Decision

The reference implementation validates routes and boundaries without copying
project content. Real manifests remain untracked. Examples use synthetic data.
Uncertain material stays with its source owner until a human confirms ownership
and disclosure rights.

## Consequences

Cross-project search is intentionally limited. A machine needs local routing
configuration after cloning, while portable policy remains reproducible.

## Reversal criteria

Any broader data flow requires explicit ownership, a versioned contract,
reconstructive-risk review, least privilege, verified recovery, and a new ADR.

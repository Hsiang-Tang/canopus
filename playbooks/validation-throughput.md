# Validation throughput

## Purpose

Shorten edit-to-feedback time without weakening merge or release acceptance.
Verification is a staged pipeline: expensive checks run when risk or an
invalidated input demands them, not merely because another edit happened.

## Inputs

- The project's verification contract (`docs/VERIFICATION.md`) and dependency
  map.
- The changed paths and what they touch: modules, consumers, schemas, build
  settings, release surfaces.
- A measured baseline for each stage that exists (edit loop, integration, CI
  queue and run, release steps, human wait).
- The last accepted evidence and the inputs it was produced from.

## Build the ladder

1. **Edit loop.** One fast, focused command per independently testable module.
   When fixing deterministic behavior, it includes the regression case.
2. **Integration.** Checks for the affected module boundaries and consumers.
3. **Merge candidate.** The full repository contract on one nominated revision.
4. **Release candidate.** Packaging, signing, migration rehearsal, visual
   review, or human acceptance, run only when the change can affect them.
5. **Escalate on doubt.** If impact is uncertain or the test-selection rules
   themselves changed, run the full relevant gate. An empty selected set is
   never proof of safety.

Run independent checks concurrently only when their environments and outputs
cannot collide. Cancel superseded CI runs, never the nominated candidate.

## Reuse evidence, invalidate precisely

Record a fingerprint for each accepted result: source revision, toolchain,
dependency lock, configuration, selected test plan, and artifact hash. Reuse
the result only while every relevant input is unchanged. Invalidate the
smallest affected class:

| Change | Invalidates |
| --- | --- |
| Source or resource in one module | That module's edit and integration evidence |
| Shared interface, schema, migration, dependency, build setting, security or concurrency code, test selection | Merge and relevant release evidence |
| Expired credential, new toolchain or OS, changed external platform state | Only the platform evidence that depends on it |
| Documentation or data validated outside the build artifact | That data contract only; not the unchanged build |

## Score effort separately from risk

Before starting, score the task 0-2 on each of uncertainty, breadth,
integration, and verification burden, and sum them (0-8). Risk (R0-R3)
estimates consequence; the score estimates effort. Do not rescore after seeing
the elapsed time. If scope materially grows, hand off and admit a new task
with a new score.

## Measure

- Record elapsed time per stage and in total, including startup and routing.
- For a repeated workflow, track p50 and p95 latency, CI queue time, cache hit
  rate, and rollback or escaped-defect rate.
- Compare accepted changes per unit time within the same risk and effort
  score. Do not divide time by the score; an ordinal 6 is not twice a 3.
- With fewer than five comparable runs, show the samples and label the trend
  unverified.

## Example

A change touches one parser module in `billing-service`. The edit loop runs
`python3 -m unittest tests.test_parser` (4 s) on each save. Before commit, the
integration gate runs the three consumer suites (40 s). The merge gate runs
the full suite once on the nominated commit (6 min). A later commit changes
only `README.md`; the merge evidence is reused because no fingerprint input
changed.

## Adopt, tighten, or roll back

- Adopt the ladder when feedback latency drops without more escaped defects.
- Tighten the impact map when a selected check misses a known-bad fixture.
- Roll back selection or caching when a result cannot be tied to a
  fingerprint, cache provenance is unsafe, or full-gate failures rise.

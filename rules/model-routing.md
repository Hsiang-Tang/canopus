# Model routing

Load this rule only when choosing or changing an execution engine, model, or
reasoning tier. Routing is a recommendation. It never grants authority, widens
scope, or replaces verification.

Tool: `tools/model_route.py` reads `routing/catalog.toml` and prints a ranked
recommendation with reasons. It never launches, bills, or configures an engine.

## Decision order

1. Prefer a deterministic script or fixed transformation when no judgment is
   needed.
2. Classify the task before seeing any result: task class, risk tier `R0`–`R3`
   (`development.md`), uncertainty, breadth, verification burden, required
   capabilities, cost priority, latency priority.
3. Choose the engine for its demonstrated role, then the model tier for the
   capability need. Engine and model are separate decisions.
4. Execute, run requirement-matched verification, and keep attributable
   outcome evidence.
5. Escalate only on a named capability gap, a failed verification, a
   representative evaluation, or an explicit owner direction. Demote only on
   representative evidence of no regression.

## Stable tiers, replaceable occupants

- The rule routes by stable capability tiers; the catalog maps tiers to
  current models. Example tiers in the synthetic catalog:
  - `fast`: cheap, high-volume, tightly bounded work.
  - `balanced`: ordinary scoped work.
  - `frontier`: complex, ambiguous, or orchestration work, used when
    evidence shows the lower tiers are insufficient.
- Changing a model is a catalog edit, not a rule change. The algorithm and task
  contract stay the same.
- A newer or larger model is not evidence. Novelty never makes a tier the
  default.
- Check actual availability at dispatch time. When a harness does not expose a
  named model, the choice stays with that engine.

## Roles

- **Brain:** planning, review, judgment. Read-heavy; may be a different engine
  from the executor.
- **Executor:** changes, tests, delivery inside the admitted envelope.
- **Deterministic runner:** fixed transformations and enforcement.
- Any role may be filled by any engine that has demonstrated it. Roles, not
  vendors, are the stable identities.

## Evidence

- Record requested and actual engine and model, task class, risk, token counts
  when available, wall-clock time, outcome, verification result, and retries in
  the task's evidence owner.
- Keep prices and qualitative roles in the dated catalog. A stale catalog is a
  review signal, not a silent claim of current cost.
- Do not infer latency or quality from model size or price. Compare with
  requirement-matched tests or representative evaluations. A self-score or a
  single success is insufficient.
- Keep stable instructions and tool definitions in a reusable prefix so prompt
  caching can apply. Cache hits reduce cost; they do not show quality.

## Risk interaction

- Higher risk raises review and promotion requirements. It does not by itself
  justify a more expensive model.
- R3 work always needs an independent reviewer, which may be a different engine
  or a human, regardless of the executor tier.

## Stop or reclassify when

- the task expands beyond its envelope;
- the required capability is unavailable;
- the catalog is stale and cost matters to the decision;
- repeated attempts fail without new evidence (this is also a convergence
  signal; see `development.md`).

## Model changes

A model release or retirement triggers a focused audit of the catalog,
instructions, skills, and representative evaluations. Keep working policy
until the replacement passes; then update the tier's occupant. Do not migrate
every task because a new model exists.

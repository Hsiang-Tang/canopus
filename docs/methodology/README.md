# Methodology

These documents explain why the rules in `rules/` look the way they do. Rules
are normative and short; each document here gives the reasoning, one concrete
example, and a pointer to the rule and the tool that enforces it.

The underlying claim is simple: an AI coding agent is good at producing
activity and poor at deciding when to stop. Most failures come from that gap,
not from bad code. So the framework spends its effort on three things:

1. **Deciding what "done" means before work starts** and freezing it.
2. **Measuring progress only against that definition**, so activity cannot
   pass for progress.
3. **Enforcing the stopping rules with code**, because a model will not
   reliably follow a prose rule it can reinterpret.

## Documents

| Document | Question it answers | Rule | Tool |
|---|---|---|---|
| [north-star-and-envelope.md](north-star-and-envelope.md) | What is the task for, and what is it allowed to touch? | `rules/development.md` | `tools/canopus_task.py admit` |
| [risk-scaled-sdd.md](risk-scaled-sdd.md) | How much specification does this change need? | `rules/development.md` | `tools/validate.py` |
| [assumptions-first.md](assumptions-first.md) | What do we do with an ambiguous request? | `rules/development.md` | none, by design |
| [convergence.md](convergence.md) | When does the agent keep going, narrow, or stop? | `rules/development.md` | `tools/convergence.py` |
| [continuation-loop.md](continuation-loop.md) | How does a task survive a new session, engine, or machine? | `rules/session.md` | `tools/canopus_task.py` |
| [anti-over-engineering.md](anti-over-engineering.md) | Should we build this new component? | `rules/development.md` | none, by design |
| [deterministic-enforcement.md](deterministic-enforcement.md) | Which rules must a tool enforce instead of a prompt? | `rules/session.md` | `tools/footer_latch.py`, `tools/install_bootstrap.py` |

Related rules not covered by a separate document: parallel writers
(`rules/workstreams.md`, `tools/workstream.py`), model choice
(`rules/model-routing.md`, `tools/model_route.py`), and data boundaries
(`rules/security.md`, `rules/knowledge-promotion.md`).

## Reading order for a new adopter

1. `north-star-and-envelope.md` and `convergence.md`: the core loop.
2. `continuation-loop.md`: how state outlives the session.
3. `deterministic-enforcement.md`: how the loop is kept honest.
4. The rest as needed.

Then follow `playbooks/adopting-canopus.md`.

## What this is not

- Not an agent runtime. It never launches, schedules, or merges on its own.
- Not a productivity score. Elapsed time and token counts are budgets and
  evidence, not measures of quality.
- Not tied to one vendor. Every engine is a replaceable node; the rules and
  durable state are the stable parts.

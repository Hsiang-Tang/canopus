# Anti-over-engineering

Rule: [`rules/development.md`](../../rules/development.md) (New-component
gate; at `COMPLETE`, stop). There is deliberately no tool for this gate: the
four questions need owner judgment, and a checker would only check that
someone typed answers.

## The problem

A governance system for AI agents is itself an attractive project for AI
agents. Every friction suggests a new tool, schema, or dashboard, and each one
is quick to build. The platform grows faster than the projects it exists to
serve, and its maintenance becomes the work. Agents make this worse: they
propose architecture readily, and "a more complete design" always sounds like
progress.

## The idea

Make building a new durable component the path with more friction, and make
not building it the default.

First, classify the proposal:

- **Vendor commodity:** generic agent loops, memory, schedulers,
  orchestration, browser use. Vendors are shipping these. Do not build them;
  adopt the vendor version when it arrives.
- **Adapter:** a thin connection to an engine, forge, or notifier. Build thin,
  keep swappable, put no owner-specific logic inside.
- **Owner-specific control:** your ownership graph, rules, data boundaries,
  evidence, recovery. Nobody will ship this for you. Invest here.

Then answer four questions:

1. **Observed at least twice?** A hypothesized friction does not count.
2. **What decision or action changes?** If nothing different happens after it
   exists, it is decoration.
3. **Why not the project owner?** Most friction belongs to the project that
   has it, not to the shared platform.
4. **Unpluggable within a day** once a vendor ships the native version? If
   removal would be a migration, the coupling is too tight.

Any unanswered question means `WATCH`, `DEFER`, or `NO CHANGE`. An accepted
proposal starts as the smallest trial with a stated retirement trigger.

## The same idea inside a task

Over-engineering also happens inside ordinary tasks. The convergence rule
covers it: at `COMPLETE`, stop. Optional hardening, refactoring, and cleanup
are separate tasks that must be admitted on their own merits. Out-of-scope
review findings are deferred, not implemented.

## Example

During work on a synthetic `billing-service`, an agent proposes "a task
scheduler with a web dashboard so we can see which invoice jobs are queued."

- Class: vendor commodity (scheduler) plus a dashboard.
- Observed twice? Once: a job was stuck last week.
- Decision changed? None named; the stuck job was found from logs within
  minutes.
- Why not the project owner? It is billing-service's own operational concern.
- Unpluggable? A dashboard with its own schema is not.

Result: `NO CHANGE`. The recorded outcome is one line in the billing-service
runbook, "check the job log for stuck invoices", and a note to revisit if it
happens again.

## Signs the gate is being bypassed

- The proposal cites completeness, symmetry, or "future flexibility".
- It names a vendor term instead of a friction.
- The design diagram is more detailed than the problem statement.
- It arrives at the end of a task that has already met its acceptance.

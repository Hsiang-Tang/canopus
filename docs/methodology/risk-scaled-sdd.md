# Risk-scaled specification-driven development

Rule: [`rules/development.md`](../../rules/development.md) (Minimum delivery
contract; Risk tiers; Verification ladder). Templates:
`templates/spec-kit/spec.md`, `plan.md`, `tasks.md`, `templates/adr.md`.
Verification entry point: `python3 tools/validate.py`.

## The problem

Two failure modes pull in opposite directions:

- **Too little specification.** An agent implements its own guess of the
  request. The code is fine; it solves the wrong problem. A new session later
  cannot tell what was intended, only what was built.
- **Too much specification.** Every typo fix gets a spec, a plan, and a task
  list. The ceremony costs more than the change, people start skipping it, and
  soon it is skipped for the changes that needed it.

## The idea

Scale the artifacts to the risk of being wrong. Four tiers:

- **R0**, trivial and reversible: just the edit and fast checks.
- **R1**, local change under an existing requirement: a failing check first,
  then the fix.
- **R2**, new or cross-component behavior: `spec.md` (what and why),
  `plan.md` (how, with decisions), `tasks.md` (steps mapped to requirements
  and verifications), plus a frozen envelope.
- **R3**, boundary or irreversible impact: R2 plus an ADR when structure
  changes, an independent reviewer, a rollback path, and owner acceptance.

The tier is chosen before work starts and only goes up without a stated
reason. The three spec files use the names most SDD tooling already
recognizes, so a fresh agent finds them without being told.

## Why traceability

The part of SDD that matters most for agents is the mapping
`requirement -> task -> verification`. It lets any session answer "is this
done?" from files rather than memory, and it exposes a task that has no
requirement (scope creep) or a requirement that has no verification (an
unproven claim).

## Why a verification ladder

Running the full suite after every edit wastes time; running only unit tests
before merge misses integration breaks. The ladder assigns each gate to a
stage: the smallest disproving check while editing, component checks after a
batch, the full contract once on the merge candidate, release gates only on
the artifact that ships. Passed evidence is reused until one of its inputs
changes.

## Example

Three changes to a synthetic `billing-service`:

- Fix a misspelled log message. **R0.** Edit, run the linter, commit.
- Round invoice totals half-even instead of half-up, as the existing spec
  already requires. **R1.** Add a test with a known-bad input (2.345 should
  round to 2.34), watch it fail, fix, run the invoice tests.
- Add a new currency with different minor units. **R2.** Write
  `docs/specs/multi-currency/spec.md` with acceptance items (amounts stored in
  minor units; display matches locale; existing invoices unchanged), a plan
  recording the storage decision, and tasks mapped to each item. Freeze the
  envelope and admit the task.

If the currency change also required migrating stored invoices, it becomes
**R3**: an ADR for the storage change, a tested rollback of the migration, and
a reviewer other than the implementing session.

## Acceptance integrity

The one rule that holds at every tier: never delete or weaken a check to make
an implementation pass. A check that fails is information. If the check is
wrong, fix the check in its own reviewed change, not as a side effect of the
feature.

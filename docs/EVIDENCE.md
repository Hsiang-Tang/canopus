# Evidence map

Each behavior Canopus claims, and the file or test that proves it.

## One-sentence summary

Canopus is a framework that keeps AI coding agents delivering against a frozen
goal across sessions, engines, and machines — stopping them deterministically
when they drift, loop, or over-engineer — while keeping every project's data
inside its owner.

## What it is

- **Methodology:** risk-scaled spec-driven development, a spec kit, ADRs, a
  North Star envelope, assumptions-first for ambiguous requests, and a
  new-component gate against over-engineering
  ([`docs/methodology/`](methodology/), [`rules/`](../rules/)).
- **Tools:** standard-library Python; the core tools have unittest coverage
  ([`tools/`](../tools/), [`tests/`](../tests/)).
- **Adoption kit:** templates, a GitHub task issue form, and a 15-minute
  adoption playbook ([`templates/`](../templates/),
  [`playbooks/adopting-canopus.md`](../playbooks/adopting-canopus.md)).

## Claims and evidence

| Claim | Evidence |
| --- | --- |
| Work is bounded by a frozen envelope; activity never counts as progress. | `tools/convergence.py`; `test_activity_never_counts_as_progress` |
| Stagnation escalates deterministically `WATCH` → `REALIGN` → `CIRCUIT_BREAK`; verified progress resets it. | `test_stagnation_escalates_watch_realign_break`, `test_verified_progress_resets_stagnation` |
| Scope growth without re-admission is drift; material work during `REALIGN` breaks the circuit. | `test_scope_change_realigns_and_material_work_then_breaks` |
| Allowances never replenish; a repeated blocker family stops early; satisfied acceptance stops. | `test_allowances_never_replenish`, `test_repeated_blocker_family_breaks`, `test_complete_stops_and_ignores_later_work` |
| Task state is durable and replayable across sessions; the stored record is never partially written. | `tools/canopus_task.py`; `test_replay_matches_direct_convergence_run`, `test_leftover_temporary_file_does_not_break_resume` |
| A changed envelope cannot sneak in: it requires explicit re-admission. | `test_changed_envelope_requires_readmit`, `test_readmit_archives_round_and_carries_surviving_acceptance` |
| "Complete" cannot be claimed unless the evaluator agrees. | `test_complete_requires_convergence_complete` |
| Admission and the footer latch happen in one call; the agent learns its session id from a `SessionStart` hook. | `test_admit_can_latch_session_atomically`, `test_session_start_tells_the_agent_its_session_id` |
| A Claude Code `Stop` hook blocks a latched turn that does not end with the Owner Footer, and never blocks twice. | `tools/footer_latch.py`; `test_latched_session_without_footer_is_blocked`, `test_never_blocks_twice_in_one_turn` |
| The latch is one-way and fails closed for a latched session with missing evidence. | `test_set_is_one_way_and_idempotent`, `test_missing_transcript_fails_closed_for_latched_session` |
| Bootstrap installation is dry-run by default, idempotent, reversible byte-for-byte, and never clobbers user settings. | `tools/install_bootstrap.py`; `test_dry_run_is_default_and_writes_nothing`, `test_remove_restores_original_bytes`, `test_hooks_merge_without_clobbering_existing_settings` |
| Model routing is recommendation-only: cheapest adequate tier, escalation path, evidence can disqualify a tier. | `tools/model_route.py`; `test_output_is_recommendation_only`, `test_poor_evidence_disqualifies_a_tier` |
| Parallel workstreams are checked for scope collisions and one-writer violations. | `tools/workstream.py`; `test_scope_collision`, `test_multiple_writers_is_a_one_writer_violation` |
| Knowledge candidates are rejected if they keep identifiers or template placeholders; a pass still requires human review. | `tools/check_knowledge_candidate.py`; `test_identifiers_are_rejected`, `test_pass_still_requires_human_review` |
| Machine paths and inventories stay out of Git; the workspace doctor is read-only. | `tools/workspace_doctor.py`, `rules/workspace.md` |
| Publication is audited for secrets, personal paths, emails, and artifacts. | `tools/audit_publication.py`, `tests/test_audit_publication.py` |

## Verify in about one minute

Python 3.11 or newer, standard library only:

```sh
python3 tools/convergence_demo.py --all      # replay four synthetic agent runs
python3 tools/validate.py                    # validators, audit, and the full test suite
```

## Where to read next

1. [`docs/methodology/README.md`](methodology/README.md) — the ideas.
2. [`rules/index.md`](../rules/index.md) — the normative rules agents load.
3. [`playbooks/adopting-canopus.md`](../playbooks/adopting-canopus.md) — adoption.

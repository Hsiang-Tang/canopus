# Verification contract

## Required commands

Run from the repository root:

```sh
python3 tools/validate.py
```

Before public delivery, also run the audit with a local, untracked denylist
translated into repeated `--deny` arguments and use an independently installed
secret scanner when available:

```sh
python3 tools/validate.py --deny internal-codename
```

## Requirement traceability

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| REF-001 closed configuration | `control-plane.toml`, `canopus.toml`, `tools/check_control_plane.py` | positive and known-bad validator tests |
| REF-002 scoped registration | `tools/register_machine.py` | environment precedence, apply, remove, preservation tests |
| REF-003 manifest governance | `tools/workspace_doctor.py` | synthetic success and invalid-governance tests |
| REF-004 Git and remote safety | `tools/workspace_doctor.py` | unknown-repository, identity, fetch/push scope tests |
| REF-005 privacy boundary | `rules/security.md`, `tools/audit_publication.py` | token, path, email, and artifact negative fixtures |
| REF-006 synthetic-only example | `examples/` | doctor returns zero findings |
| CONV-001 to CONV-011 bounded convergence | `tools/convergence.py`, `tools/convergence_demo.py`, `examples/scenarios/` | `tests/test_convergence.py` (21 tests) and scenario replay |
| FW-001 durable task records | `tools/canopus_task.py` | `tests/test_canopus_task.py` |
| FW-002 harness enforcement | `tools/footer_latch.py` | `tests/test_footer_latch.py` |
| FW-003 reversible bootstrap | `tools/install_bootstrap.py` | `tests/test_install_bootstrap.py` |
| FW-004 recommendation-only routing | `tools/model_route.py`, `routing/catalog.toml` | `tests/test_model_route.py` |
| FW-005 workstream safety | `tools/workstream.py`, `examples/workstreams/` | `tests/test_workstream.py` |
| FW-006 knowledge gate | `tools/check_knowledge_candidate.py` | `tests/test_check_knowledge_candidate.py` |
| FW-007 adoptable kit | `rules/`, `docs/methodology/`, `templates/`, `playbooks/` | CLI cross-check and publication audit at delivery |
| REF-007 clean delivery | Git audit and clean-checkout run | tracked-files review and fresh-clone evidence at delivery |

## Acceptance interpretation

- Validator and test failures block delivery.
- Workspace warnings must be explained and resolved when they concern this
  repository.
- A clean publication audit is defense in depth, not a publication decision.
- The fresh-checkout run must use the exact pushed commit.
- Public visibility, license, disabled Pages, releases, deployments,
  collaborators, and repository security settings must be checked after
  delivery.

## Evidence invalidation

Any source, rule, schema, manifest, workflow, test-selection, remote, or
visibility change invalidates the corresponding evidence. Documentation-only
changes still require the validator, publication audit, tests, and diff check
because documentation is part of the disclosure surface.

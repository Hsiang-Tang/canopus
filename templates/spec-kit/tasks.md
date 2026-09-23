# <Feature name> tasks

<!--
Save as docs/specs/<slug>/tasks.md. One line per independently verifiable step.
Each task names the acceptance item it moves, so progress is measured by
closed acceptance, not by the number of boxes ticked. Tick a box only with the
evidence recorded next to it.
-->

- [ ] **<PREFIX>-TASK-001** Confirm identity, remote, branch, worktree, spec,
  relevant ADRs, and verification contract. — evidence: `<git status / commands>`
- [ ] **<PREFIX>-TASK-002** <smallest change that closes `AC1`>. — moves: `AC1`
  — evidence: `<test or command>`
- [ ] **<PREFIX>-TASK-003** <change that closes `AC2`>. — moves: `AC2`
  — evidence: `<test or command>`
- [ ] **<PREFIX>-TASK-004** <change that closes `AC3`>. — moves: `AC3`
  — evidence: `<test or command>`
- [ ] **<PREFIX>-TASK-005** Run the merge-candidate gate and fix failures
  inside scope. — evidence: `<full command>`
- [ ] **<PREFIX>-TASK-006** Update `docs/STATUS.md`, record deferred findings
  on the task Issue, commit, and close the task. — evidence: `<commit sha>`

## Deferred

<!-- Out-of-scope findings land here as proposals. They are not work. -->

- <finding> — proposed as: `<new issue | ADR | discard>`

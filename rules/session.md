# Session protocol

A session is a replaceable execution node. Task identity, state, and evidence
live in durable owners (the task's Issue, the durable task record, and the
target repository), never in the chat.

Background: `docs/methodology/continuation-loop.md`,
`docs/methodology/deterministic-enforcement.md`.

## Bootstrap order

Run once per new session that involves local development, before any material
change. The managed block written by `tools/install_bootstrap.py --apply` into
the global Claude Code and Codex instruction files points here.

1. Resolve the control-plane root from the environment variable, then the
   global Git config key, both declared under `[registration]` in
   `control-plane.toml`. Never guess or search for the path.
2. If the root is unavailable, stop before material changes and say that
   `python3 tools/register_machine.py --apply` must be run once from a clone.
3. Inspect the control-plane worktree. If it is clean and tracks its approved
   remote, run `git pull --ff-only`. If it is dirty or the pull fails, keep
   every change, report the condition, and do not claim the rules are current.
4. Run `python3 tools/check_control_plane.py` and read files in the order
   declared by `control-plane.toml` `session.read_order`.
5. Resolve the workspace manifest pointer the same way (environment, then Git
   config). If one is registered, the file must exist; run
   `python3 tools/workspace_doctor.py --manifest <path>` and report every
   error:
   - an error on the current task's target path blocks that work until fixed
     or explicitly authorized around;
   - an error on an unrelated path is reported but does not block an
     independent, already-scoped task;
   - a manifest that cannot be parsed blocks everything.
6. At the target project root, read `AGENTS.md`. A project `CLAUDE.md` must
   import it with `@AGENTS.md` and add only Claude-specific settings.
7. Use the project rules as the routing map: README, architecture, ADR index,
   active spec or task, verification contract, and status, as relevant.
8. Inspect Git identity, remote, branch, and worktree state. Fetch before using
   local state as evidence about what exists; report ahead/behind counts rather
   than asserting absence from a stale checkout.
9. Classify the interaction (task admission, below).

Keep the startup report to failures, stale state, and safety-relevant
conditions.

## Task admission

- Classify the interaction as **substantial** or **non-substantial**.
  - Substantial: materially executes, advances, reconciles, or changes durable
    task, workstream, or governance state. This includes a zero-file change that
    closes, reopens, or reclassifies tasks from evidence.
  - Non-substantial: questions, explanations, quick read-only inspection, advice,
    and chat that make no durable task decision. These are never admitted.
- For a substantial task, resolve its durable identity: a stable Issue
  reference such as `acme/billing-service/issues/42`. Never a machine path,
  session ID, or transient label.
- Freeze the envelope (North Star, acceptance IDs, scope, allowances,
  thresholds; see `development.md`) into a JSON file, then admit and latch in
  one step before substantive work:

  ```sh
  python3 tools/canopus_task.py admit --task <id> --envelope <envelope.json> \
    --latch-session <session-id>
  ```

  In Claude Code the `SessionStart` hook (`footer_latch.py session-start`)
  prints the session id into the agent's context, so the agent never guesses
  it. Admission and latching happen in the same call; there is no way to admit
  without latching.

- `admit` is idempotent. Admitting an existing identity resumes it: elapsed time
  accumulates across sessions and the stored envelope is not replaced.
- A bounded round with its own owner-stated limit is a distinct child identity
  (for example `acme/billing-service/issues/42/round-2`), not the parent
  reused with a narrower limit.
- A stop before any mutation (bootstrap found a blocking gate) is still
  substantial when the blocked task has a durable Issue. Admit it, record the
  blocker, and render the footer honestly with `0 / <real total>`.

## Owner Footer

The Owner Footer is the human-facing projection of the task state. Render it,
never handwrite it:

```sh
python3 tools/canopus_task.py footer --task <id> [--lang en|zh-TW]
```

It begins with the header `Canopus · <task>` and contains these rows in order:

| English    | 繁體中文 | Meaning                                                |
|------------|---------|--------------------------------------------------------|
| `Goal`     | `主線`   | The frozen North Star                                  |
| `Progress` | `進度`   | Accepted items over the frozen denominator, with a bar |
| `Loop`     | `循環`   | Convergence state and stalled-cycle count              |
| `Align`    | `對齊`   | On target, or drifted                                  |
| `Blocker`  | `卡點`   | Open blocker families, or none                         |
| `Next`     | `後續`   | The one bounded next action                            |
| `Decision` | `決策`   | `CONTINUE` / `CONTINUE, NARROW` / `ALIGN ONLY` / `STOP, OWNER DECIDES` / `STOP, DONE` |

- `Deferred` (`延後`) appears only when out-of-scope findings were deferred.
  `Reason` (`原因`) appears only when the state has a stop or watch reason.
- A progress bar needs a real frozen denominator. Never invent a percentage.
- Unknown instrumentation stays absent or `UNAVAILABLE`; never estimate it.
- English is the default; `--lang zh-TW` renders the Traditional Chinese view
  from the same state. Engine or machine never changes the layout.
- The footer is a projection and continuity check. It is not an authorization
  record and not a task database.

## Agent Handoff

The Agent Handoff is the machine-to-machine projection for the next session:

```sh
python3 tools/canopus_task.py handoff --task <id>
```

- It carries task, state, North Star, remaining acceptance, frozen scope,
  allowance usage, stagnation counters, activity, deferred findings, the
  successor permission, the stop reason, and the next action.
- Include it in the final response when continuation or control state is
  material, immediately before the Owner Footer.
- Persist it (or a pointer to the durable record) in the task's Issue at every
  handoff. Use `templates/handoff.md` for the Issue comment.
- Do not paste the full machine JSON into every response.

## Footer-last closeout

For every response in an admitted task that yields control to the owner
(progress update, question, link to a PR, blocked or error report, completion):

1. Optional prose summary.
2. The Agent Handoff, when material.
3. The Owner Footer, as the final block. Nothing follows it.

- Writing the footer into an Issue or PR comment satisfies the durable record
  but never replaces the final-response footer.
- In a non-latched session where a substantial operation's state cannot be
  rendered, end with `FOOTER_UNAVAILABLE: <concrete reason>`. While the latch is
  set the task record exists, so render the footer.

## One-way latch

- `tools/footer_latch.py set` moves the session from `CHAT` to
  `MANAGED_TASK`. Nothing moves it back before the session ends.
- The Claude Code `Stop` hook runs `tools/footer_latch.py stop` on every turn
  end. If the session is latched and the final assistant message does not end
  with a Canopus Owner Footer, it returns `{"decision":"block","reason":...}` and
  the model must add the footer.
- The hook never blocks twice in one turn: when `stop_hook_active` is true it
  allows the stop and logs the degrade instead of looping.
- The `SessionEnd` hook runs `tools/footer_latch.py end`, which clears the
  latch. A new session starts exempt until it admits a task.
- Missing telemetry never clears the latch or exempts a response.
- Install the hooks with `python3 tools/install_bootstrap.py --apply
  --claude-hooks`. Check with `python3 tools/footer_latch.py status`.

## During work

- An explicit request to change, fix, build, or finish authorizes the whole
  reversible delivery chain inside the confirmed project: inspect, edit, test,
  build, commit, and push to an already-authorized remote. Do not re-ask for
  each ordinary step.
- Stop for the human only when a password, one-time code, account, legal, or
  purchase decision is needed; the platform requires confirmation; scope
  materially expands; the step creates new public exposure or uses an
  unapproved remote; or an external action has no verified recovery path.
- Record each bounded event with
  `python3 tools/canopus_task.py event --task <id> --json '<event>'` and close
  each cycle with `python3 tools/canopus_task.py checkpoint --task <id>`. Obey the
  resulting state before the next mutation (`development.md`).
- One writer per checkout. A second agent is read-only, or gets its own branch
  and worktree under `workstreams.md`.
- Keep durable decisions in the target repository. Keep rule candidates in
  Issues until adopted.

## Resuming from durable state

A fresh session resumes from the task's Issue and durable task record, never
from an old chat, a copied transcript, or a compacted summary.

1. Read the Issue (North Star, envelope, latest handoff comment).
2. Run `python3 tools/canopus_task.py status --task <id>` and
   `python3 tools/canopus_task.py handoff --task <id>`.
3. Admit the same identity again (it resumes) and set the latch.
   Task records live under `$CANOPUS_STATE_DIR` on one machine. On a
   different machine there is no record yet: admit with the envelope recorded
   in the Issue, then replay the accepted items and open blockers listed in the
   latest handoff comment as events before continuing. The Issue is the
   portable state; the local record is a cache of it.
4. Obey the successor permission: `CONTINUE` allows only the authorized next
   action; `ALIGNMENT ONLY` forbids material mutation; `STOP` forbids all
   execution until the owner re-admits.
5. Confirm the Git checkpoint named in the handoff matches the branch before
   editing.

- A new session, engine, device, or machine never resets `REALIGN`,
  `CIRCUIT_BREAK`, or spent allowances.
- If durable state is missing, say so. Do not reconstruct a task list from
  memory.

## Token and context hygiene

- Treat budgets as stop conditions, never as completion criteria.
- Defaults, per session (a project may set its own):
  - **Soft:** 80k current input tokens, 90 minutes, or 60 tool steps. Narrow
    the task and write a checkpoint.
  - **Hard:** 140k current input tokens, 180 minutes, or 120 tool steps. Stop
    expanding, persist the handoff, and continue in a fresh session.
- Apply thresholds to each session independently. Never add two sessions'
  context into one percentage.
- Compaction is activity, not progress, and not a handoff.
- Load rules, playbooks, and knowledge on demand from their indexes. Read the
  section you need, not the whole file.
- Reference files by path instead of pasting them. Never copy transcripts into
  Git.
- A budget stop preserves the original objective. It never turns partial work
  into a completion claim or skips verification.

## Closeout

For a task that changed architecture, policy, release or recovery behavior,
or crossed a session budget, record in its durable owner:

1. **Mental model:** the causal model or decision a fresh session needs, or
   "no new model".
2. **Reusable mechanism:** rule, playbook, knowledge note, project decision, or
   skill candidate (`knowledge-promotion.md`), or none.
3. **Verification evidence:** what distinguishes success from a plausible
   claim.
4. **Stop boundary:** unresolved work, deliberate deferrals, and what would
   justify reopening.

Then: run the verification required by the risk tier; update changed specs,
ADRs, and status; record unresolved work in an Issue; commit with the correct
identity; push only to an authorized remote; leave a clean worktree or report
every remaining change. Finish with:

```sh
python3 tools/canopus_task.py close --task <id> --outcome complete|handoff|blocked|abandoned
```

At `COMPLETE`, close and stop. Deferred findings go back to the owner as
proposals, not follow-up execution.

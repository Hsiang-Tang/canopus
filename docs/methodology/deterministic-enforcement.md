# Deterministic enforcement over prompt rules

Rule: [`rules/session.md`](../../rules/session.md) (Bootstrap order;
Footer-last closeout; One-way latch). Tools: `tools/footer_latch.py`
(Claude Code hook entrypoints), `tools/install_bootstrap.py` (managed
instruction blocks and hook installation), `tools/convergence.py`
(`footer_last_gate`).

## The problem

Every rule in `rules/` is text a model reads and chooses to follow. That works
most of the time. It fails in the cases that matter: late in a long session,
after compaction, under a confusing instruction, or when a model decides this
response is an exception. "Always end with the Owner Footer" is followed
reliably for the first few turns and then quietly dropped on the one response
that reports a blocker, which is exactly when the owner most needs the state.

A prose rule can make a violation detectable afterwards. It cannot prevent the
violation.

## The idea

When a rule is safety- or continuity-critical and mechanically checkable,
move it out of the prompt and into code that runs outside the model:

- **Checkable:** a program can decide pass or fail from observable data
  (the final message text, a file path, a remote URL).
- **Critical:** a violation loses state, crosses a boundary, or misleads the
  owner.

Rules that need judgment stay in prose. Rules that are both checkable and
critical get a hook or a validator.

## The footer latch

The Owner Footer rule is enforced by a one-way, per-session latch:

1. At session start, the `SessionStart` hook (`footer_latch.py session-start`)
   prints the session id into the agent's context. At task admission the agent
   runs `python3 tools/canopus_task.py admit --task <task> --envelope <file>
   --latch-session <id>`, which admits and latches in one call. The session is
   now `MANAGED_TASK`. Nothing sets it back to `CHAT` before the
   session ends.
2. On every turn end, Claude Code's `Stop` hook runs
   `python3 tools/footer_latch.py stop`, which reads the hook's JSON on stdin.
   If the session is latched and the final assistant message does not end with
   a Canopus Owner Footer, the hook prints
   `{"decision":"block","reason":"..."}` and the model must add it.
3. If `stop_hook_active` is true (the model is already responding to a block),
   the hook lets the turn end rather than loop forever, and the degrade is
   logged.
4. The `SessionEnd` hook runs `python3 tools/footer_latch.py end` to clear the
   latch.

Why one-way: the decision "is this a managed task?" is made once, with full
context, at admission. It is not re-made on every turn by a model that may
have lost that context. Why never twice: a hook that can block forever is its
own failure mode.

## Bootstrap as installed code

The session protocol only works if every new session reads it. Rather than
trusting each person to paste instructions, `tools/install_bootstrap.py`
writes one managed block into the global instruction files:

```sh
python3 tools/install_bootstrap.py                         # dry run: show the diff
python3 tools/install_bootstrap.py --apply                 # write the managed blocks
python3 tools/install_bootstrap.py --apply --claude-hooks  # also add Stop/SessionEnd hooks
python3 tools/install_bootstrap.py --remove                # remove only managed content
```

The block sits between `<!-- canopus:bootstrap:start -->` and
`<!-- canopus:bootstrap:end -->` in `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`.
Reinstalling is idempotent; unrelated content and existing settings are kept.
Project rules stay in the project's `AGENTS.md`, which `CLAUDE.md` imports with
`@AGENTS.md`, so both engines read one canonical file.

## Engine coverage

The hard guarantee exists only where the engine exposes a hook that can refuse
to end a turn. Today that is Claude Code (`SessionStart`, `Stop`,
`SessionEnd`). Codex has no equivalent hook, so its bootstrap asks the agent to
render the footer as a self-check before ending a turn. That is a prompt rule,
with the weaknesses this document describes. Treat Codex sessions as
unenforced and check their footers in review.

## Example

A synthetic `billing-service` task is admitted and latched. Three turns later
the executor hits a failing fixture and replies "Blocked on the fixture; see
the PR link." with no footer. The `Stop` hook blocks the turn with the reason
"latched session: final message must end with the Canopus Owner Footer". The
model renders `python3 tools/canopus_task.py footer --task ...` and appends it.
The owner now sees `Blocker │ flaky-fixture` and `Decision │ CONTINUE, NARROW`
instead of a bare link.

## Limits

- A hook enforces only what it can see. It checks that a footer is present and
  last; it cannot check that the task record behind it is honest. The
  convergence evaluator and review cover that.
- A blocking hook needs a known-bad test as well as a known-good one, and must
  fail open on its own internal errors.
- Hook and instruction files are part of the attack surface. Review changes to
  them like code (`rules/security.md`, Harness integrity).
- Engines without a hook mechanism fall back to the prose rule plus the
  `footer_last_gate` self-check in `tools/convergence.py`. Say so rather than
  claim enforcement that does not exist.

# Adopting Canopus in your own repositories

## Purpose

Get from zero to one bounded, footer-enforced agent task in about 15 minutes:
install the bootstrap once per machine, add two files to a project, open a
task Issue, admit it, work, and close it.

## Prerequisites

- Python 3.11 or newer and Git. No other dependencies.
- Claude Code, Codex, or both.
- Optional: the GitHub CLI (`gh`) for creating Issues from the terminal.

Every command below that writes outside the Canopus checkout has a dry run or a
`--remove`. Nothing is installed as a service.

## 1. Clone and validate (2 min)

```sh
git clone https://github.com/<owner>/canopus.git ~/src/canopus
cd ~/src/canopus
python3 tools/validate.py
```

The last line must read `local validation pipeline: OK`.

## 2. Register this machine (1 min)

```sh
python3 tools/register_machine.py            # shows current pointers, changes nothing
python3 tools/register_machine.py --apply    # sets git config --global canopus.root
```

This stores one path pointer in your global Git config. Agents resolve the
Canopus root from it (or from `CANOPUS_ROOT`) and never guess a path.

## 3. Install the global bootstrap (2 min)

```sh
python3 tools/install_bootstrap.py                         # dry run: prints the planned changes
python3 tools/install_bootstrap.py --apply                 # writes the managed blocks
python3 tools/install_bootstrap.py --apply --claude-hooks  # also adds Stop/SessionEnd hooks
```

What `--apply` does:

- Writes a block between `<!-- canopus:bootstrap:start -->` and
  `<!-- canopus:bootstrap:end -->` into `~/.claude/CLAUDE.md` and
  `~/.codex/AGENTS.md`. Content outside the markers is untouched, and
  rerunning replaces the block instead of duplicating it. The block text comes
  from [`global-claude-bootstrap.md`](../templates/global-claude-bootstrap.md)
  and [`global-codex-bootstrap.md`](../templates/global-codex-bootstrap.md).
- With `--claude-hooks`, merges three hooks into `~/.claude/settings.json`,
  preserving your existing settings: `SessionStart` (`footer_latch.py
  session-start`, tells the agent its session id), `Stop` (`footer_latch.py
  stop`, enforces the footer), and `SessionEnd` (`footer_latch.py end`, clears
  the latch).

Check it:

```sh
grep -c "canopus:bootstrap" ~/.claude/CLAUDE.md ~/.codex/AGENTS.md   # 2 each
python3 tools/footer_latch.py status                             # no active latches
```

## 4. Add Canopus to a project (3 min)

From the root of the repository you want to govern (for example
`acme-notes`):

```sh
cp ~/src/canopus/templates/project-AGENTS.md AGENTS.md
cp ~/src/canopus/templates/project-CLAUDE.md CLAUDE.md          # contains only @AGENTS.md
mkdir -p .github/ISSUE_TEMPLATE
cp ~/src/canopus/.github/ISSUE_TEMPLATE/canopus-task.md .github/ISSUE_TEMPLATE/
```

Edit `AGENTS.md`: fill in owner, approved remote, data class, default risk,
and the four verification commands. Delete sections that do not apply. Commit:

```sh
git add AGENTS.md CLAUDE.md .github/ISSUE_TEMPLATE/canopus-task.md
git commit -m "Adopt Canopus agent rules"
```

`AGENTS.md` is canonical for every engine; `CLAUDE.md` imports it with
`@AGENTS.md` so the rules exist once.

## 5. Open a task Issue (3 min)

Open a new Issue with the **Canopus task** template (or
`gh issue create --title "NOTES-1: export notes as Markdown" --body-file ~/src/canopus/templates/task-issue.md`
and edit it). Fill in the North Star, three acceptance items, scope,
non-goals, and allowances. If the request was vague, add 3-5 assumptions with
the cost of each being wrong. Save the Issue's envelope block locally:

```json
{
  "task_ref": "NOTES-1",
  "north_star": "Users can export any note as a Markdown file",
  "acceptance": ["AC1 export command", "AC2 front matter preserved", "AC3 empty note exports"],
  "scope": ["note export"],
  "corrective_limit": 2,
  "review_limit": 2,
  "realign_after": 2,
  "circuit_break_after": 3
}
```

## 6. Admit the task (1 min)

Start a Claude Code or Codex session in the project and ask it to work on the
Issue. The bootstrap tells the agent to admit it; you can also do it yourself:

```sh
P=$(git config --global --get canopus.root)
python3 $P/tools/canopus_task.py admit --task NOTES-1 --envelope envelope.json
```

Admission is idempotent: running it again resumes the existing record. State
is stored as JSON under `$CANOPUS_STATE_DIR` (default `~/.canopus/state`), outside
every repository.

In Claude Code the agent admits and latches in one call, using the session id
the `SessionStart` hook printed at startup:

```sh
python3 $P/tools/canopus_task.py admit --task NOTES-1 --envelope envelope.json \
  --latch-session <session-id>
```

From then until the session ends, the `Stop` hook blocks a turn whose final
block is not a Canopus Owner Footer and asks for it (once per turn, so it can
never loop). The latch is one-way: the agent cannot
turn it off mid-session.

## 7. Work (the task itself)

The agent records outcomes, not activity counts, as progress:

```sh
python3 $P/tools/canopus_task.py event --task NOTES-1 --json '{"kind":"accept","item":"AC1 export command"}'
python3 $P/tools/canopus_task.py event --task NOTES-1 --json '{"kind":"activity","what":"tests","count":5}'
python3 $P/tools/canopus_task.py event --task NOTES-1 --json '{"kind":"finding","summary":"PDF export too","in_scope":false}'
python3 $P/tools/canopus_task.py checkpoint --task NOTES-1 --note "Cover the empty-note case next."
```

Event kinds: `accept`, `activity`, `corrective`, `review`, `finding`,
`blocker`, `resolve_blocker`, `scope_change`, `checkpoint`. What they cause:

| State | Trigger | What the agent may do |
| --- | --- | --- |
| `WATCH` | a checkpoint with no accepted progress | continue, carefully |
| `REALIGN` | `realign_after` stalled checkpoints, a scope change, or an unlisted acceptance item | alignment work only |
| `CIRCUIT_BREAK` | `circuit_break_after` stalls, an exhausted allowance, a repeated blocker, or material work during `REALIGN` | stop; owner decides |
| `COMPLETE` | every acceptance item accepted | stop; do not polish |

The out-of-scope finding above is kept as a deferred proposal. It never
becomes work in this task.

## 8. Footer every substantial response

```sh
python3 $P/tools/canopus_task.py footer --task NOTES-1              # English
python3 $P/tools/canopus_task.py footer --task NOTES-1 --lang zh-TW # Traditional Chinese
```

The Owner Footer is the last block of the agent's reply: goal, progress bar,
loop state, blocker, next action, and decision. Codex has no Stop hook, so its
bootstrap makes rendering the footer a self-check before ending a turn.

To move to a new session, engine, or machine:

```sh
python3 $P/tools/canopus_task.py handoff --task NOTES-1
```

Paste that into [`handoff.md`](../templates/handoff.md) on the Issue and start
the next session with [`session-starter.md`](../templates/session-starter.md).
It resumes from the record, not the chat.

## 9. Close (1 min)

```sh
python3 $P/tools/canopus_task.py status --task NOTES-1
python3 $P/tools/canopus_task.py close --task NOTES-1 --outcome complete
```

Outcomes: `complete`, `handoff`, `blocked`, `abandoned`. The record keeps
admission and close timestamps and elapsed time. Post the final footer on the
Issue, list deferred findings as proposed follow-up Issues, and close it. To
widen a finished or stopped task, open a new Issue and admit it; never edit
the old envelope.

## Undo

```sh
python3 tools/install_bootstrap.py --remove   # removes only the managed blocks and Canopus hooks
python3 tools/register_machine.py --remove    # removes the git config pointers
rm -rf ~/.canopus/state                          # optional: delete local task records
```

## Troubleshooting

- **The agent says the Canopus root is unavailable.** Step 2 was skipped or ran
  from a different clone; rerun `register_machine.py --apply`.
- **Claude Code keeps refusing to stop.** The session is latched and the reply
  does not end with the footer. Ask it to render `canopus_task.py footer` as the
  final block. The hook does not block twice in the same turn.
- **Two agents edited the same files.** Use separate worktrees and declare
  scopes: see [`parallel-workstreams.md`](parallel-workstreams.md).
- **The task hit `CIRCUIT_BREAK`.** This is the intended outcome of a loop.
  Read the reason in the footer, then decide: narrow scope, fix access, or
  admit a new task with different acceptance.

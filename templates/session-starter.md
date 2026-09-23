# Session starter

<!--
Paste the quoted prompt into a fresh session when the global bootstrap is not
installed, or when resuming a task on a new engine or machine. Replace only the
<placeholders>. Never paste secrets, private inventories, or old transcripts.
-->

> This is a new, stateless development session. Git and the task Issue are
> the source of truth, not any earlier chat. Resolve the Canopus root from
> `CANOPUS_ROOT` or `git config --global --get canopus.root`, pull
> it if clean, run `python3 tools/check_control_plane.py`, and read the files
> in the order `control-plane.toml` declares. Then read `<project>/AGENTS.md`,
> the active spec, relevant ADRs, and live Git state, and confirm identity,
> branch, and remote before editing.
>
> Task: `<task-id>` from Issue `<issue-url>`. Run
> `python3 <canopus-root>/tools/canopus_task.py status --task <task-id>` and
> `python3 <canopus-root>/tools/canopus_task.py handoff --task <task-id>`. If the task
> is not yet admitted, admit it from the Issue's envelope. A new session does
> not clear `REALIGN`, `CIRCUIT_BREAK`, or an exhausted allowance: obey the
> handoff's successor instruction.
>
> Work only inside the frozen scope. Record accepted items and blockers as
> events, checkpoint each cycle, defer out-of-scope findings, and end every
> substantial response with the Owner Footer from `canopus_task.py footer`.

## Handoff before leaving a long session

When context is getting heavy, or before switching engine or machine, run
`canopus_task.py checkpoint --task <task-id> --note "<next action>"` and fill
[`handoff.md`](handoff.md). The next session starts from this prompt plus that
handoff, not from a summary of the old chat.

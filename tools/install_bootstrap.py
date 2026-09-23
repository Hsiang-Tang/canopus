#!/usr/bin/env python3
"""Install the Canopus bootstrap into global Claude Code and Codex instructions.

One command makes every new agent session start from the control plane:

* a managed block between ``<!-- canopus:bootstrap:start -->`` and
  ``<!-- canopus:bootstrap:end -->`` in ``~/.claude/CLAUDE.md`` and
  ``~/.codex/AGENTS.md``;
* with ``--claude-hooks``, Stop and SessionEnd hook entries for
  ``tools/footer_latch.py`` merged into ``~/.claude/settings.json``.

Safety contract:

* dry-run by default: prints the plan and a diff, writes nothing;
* ``--apply`` is idempotent: a second run reports ``unchanged``;
* content outside the managed block, and every settings key or hook this
  tool did not create, is preserved byte-for-byte or value-for-value;
* an existing file is copied to ``<name>.canopus-backup-<UTC stamp>`` before
  it is modified;
* ``--remove`` deletes only managed content;
* malformed markers or unparsable settings stop the run before any write.

Block text comes from ``templates/global-claude-bootstrap.md`` and
``templates/global-codex-bootstrap.md`` when present (``{{CANOPUS_ROOT}}`` is
replaced with this checkout's path; if the template itself contains the
markers, only the text between them is used), otherwise from a built-in
default.
"""

from __future__ import annotations

import argparse
import difflib
import json
import shlex
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- canopus:bootstrap:start -->"
END = "<!-- canopus:bootstrap:end -->"
HOOK_EVENTS = {"SessionStart": "session-start", "Stop": "stop", "SessionEnd": "end"}
DEFAULT_BLOCK = """# Canopus bootstrap (managed block; edit the template, not this copy)

Control plane: {{CANOPUS_ROOT}}

1. Read `{{CANOPUS_ROOT}}/AGENTS.md`, then the rules it routes to.
2. At the target project root, read `AGENTS.md`; it is canonical.
3. Admit formal work with `python3 {{CANOPUS_ROOT}}/tools/canopus_task.py admit` and
   resume from durable task state, never from chat history.
4. One writer per checkout; parallel writers use separate branches and worktrees.
5. End every turn of an admitted task with the Owner Footer as the final block.
"""


class BootstrapError(RuntimeError):
    """A condition that makes any write unsafe."""


@dataclass
class Change:
    path: Path
    action: str  # create | update | unchanged | remove | absent
    before: str
    after: str


def block_text(template: Path, root: Path) -> str:
    body = template.read_text(encoding="utf-8") if template.is_file() else DEFAULT_BLOCK
    if START in body and END in body:  # a template may document itself outside the markers
        body = body.split(START, 1)[1].split(END, 1)[0]
    return f"{START}\n{body.replace('{{CANOPUS_ROOT}}', str(root)).strip()}\n{END}\n"


def split_managed(text: str, path: Path) -> tuple[str, str] | None:
    """Return (before, after) around the managed block, or None if absent."""
    starts, ends = text.count(START), text.count(END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1 or text.index(START) > text.index(END):
        raise BootstrapError(f"{path}: malformed Canopus markers; fix by hand before rerunning")
    head, rest = text.split(START, 1)
    tail = rest.split(END, 1)[1]
    return head, tail[1:] if tail.startswith("\n") else tail


def plan_markdown(path: Path, block: str | None) -> Change:
    """block=None means remove the managed block."""
    before = path.read_text(encoding="utf-8") if path.is_file() else ""
    parts = split_managed(before, path)
    if block is None:
        if parts is None:
            return Change(path, "absent", before, before)
        head, tail = parts[0].rstrip("\n"), parts[1].lstrip("\n")
        after = f"{head}\n\n{tail}" if head and tail else (f"{head}\n" if head else tail)
        return Change(path, "remove", before, after)
    if parts is None:
        separator = "" if not before.strip() else ("\n" if before.endswith("\n") else "\n\n")
        after = (before + separator if before.strip() else "") + block
    else:
        head, tail = parts
        after = head + block + tail
    if after == before:
        return Change(path, "unchanged", before, after)
    return Change(path, "update" if path.exists() else "create", before, after)


def hook_command(root: Path, verb: str) -> str:
    return f"python3 {shlex.quote(str(root / 'tools' / 'footer_latch.py'))} {verb}"


def _is_managed(hook: object, verb: str) -> bool:
    command = hook.get("command", "") if isinstance(hook, dict) else ""
    return isinstance(command, str) and "python3" in command and command.endswith(f"footer_latch.py {verb}")


def plan_settings(path: Path, root: Path, remove: bool) -> Change:
    before = path.read_text(encoding="utf-8") if path.is_file() else ""
    try:
        settings = json.loads(before) if before.strip() else {}
    except json.JSONDecodeError as error:
        raise BootstrapError(f"{path}: not valid JSON ({error}); nothing was changed") from error
    if not isinstance(settings, dict) or not isinstance(settings.get("hooks", {}), dict):
        raise BootstrapError(f"{path}: expected a JSON object with an object 'hooks' key")
    original = json.loads(json.dumps(settings))
    hooks = settings.setdefault("hooks", {})
    for event, verb in HOOK_EVENTS.items():
        groups = hooks.get(event, [])
        if not isinstance(groups, list):
            raise BootstrapError(f"{path}: hooks.{event} must be a list")
        wanted = None if remove else hook_command(root, verb)
        found, kept = False, []
        for group in groups:
            if isinstance(group, dict) and isinstance(group.get("hooks"), list):
                inner = []
                for hook in group["hooks"]:
                    if not _is_managed(hook, verb):
                        inner.append(hook)
                    elif hook.get("command") == wanted and not found:
                        inner.append(hook)  # already installed here: keep its position
                        found = True
                if not inner:
                    continue  # the group held only stale managed hooks
                group = {**group, "hooks": inner}
            kept.append(group)
        if wanted and not found:
            kept.append({"hooks": [{"type": "command", "command": wanted}]})
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    if not hooks:
        settings.pop("hooks")
    if settings == original:
        return Change(path, "absent" if remove else "unchanged", before, before)
    after = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
    return Change(path, "remove" if remove else ("update" if path.exists() else "create"), before, after)


def build_plan(home: Path, root: Path, *, claude_md: Path | None = None, codex_md: Path | None = None,
               settings: Path | None = None, hooks: bool = False, remove: bool = False) -> list[Change]:
    claude_md = claude_md or home / ".claude" / "CLAUDE.md"
    codex_md = codex_md or home / ".codex" / "AGENTS.md"
    settings = settings or home / ".claude" / "settings.json"
    templates = root / "templates"
    changes = [
        plan_markdown(claude_md, None if remove else block_text(templates / "global-claude-bootstrap.md", root)),
        plan_markdown(codex_md, None if remove else block_text(templates / "global-codex-bootstrap.md", root)),
    ]
    if hooks or (remove and settings.is_file()):
        changes.append(plan_settings(settings, root, remove))
    return changes


def apply(changes: list[Change], now: datetime | None = None) -> list[Path]:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    backups = []
    for change in changes:
        if change.action in {"unchanged", "absent"}:
            continue
        if change.path.is_file():
            backup = change.path.with_name(f"{change.path.name}.canopus-backup-{stamp}")
            shutil.copy2(change.path, backup)
            backups.append(backup)
        change.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = change.path.with_name(change.path.name + ".canopus-tmp")
        temporary.write_text(change.after, encoding="utf-8")
        temporary.replace(change.path)
    return backups


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install or remove the Canopus global bootstrap.")
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    parser.add_argument("--remove", action="store_true", help="remove only managed content")
    parser.add_argument("--claude-hooks", action="store_true", help="merge SessionStart/Stop/SessionEnd hooks")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--root", type=Path, default=ROOT, help="control-plane checkout to point at")
    parser.add_argument("--claude-md", type=Path)
    parser.add_argument("--codex-agents", type=Path)
    parser.add_argument("--settings", type=Path)
    args = parser.parse_args(argv)

    home = args.home.expanduser()
    resolve = lambda value: None if value is None else (value if value.is_absolute() else home / value)  # noqa: E731
    try:
        changes = build_plan(home, args.root.resolve(), claude_md=resolve(args.claude_md),
                             codex_md=resolve(args.codex_agents), settings=resolve(args.settings),
                             hooks=args.claude_hooks, remove=args.remove)
    except BootstrapError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2
    for change in changes:
        print(f"{change.action:<10} {change.path}")
        if change.action not in {"unchanged", "absent"} and not args.apply:
            sys.stdout.writelines(difflib.unified_diff(
                change.before.splitlines(True), change.after.splitlines(True),
                str(change.path), f"{change.path} (planned)"))
    if not args.apply:
        print("dry run: nothing written; rerun with --apply")
        return 0
    for backup in apply(changes):
        print(f"backup     {backup}")
    print("applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

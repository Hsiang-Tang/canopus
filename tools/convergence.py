#!/usr/bin/env python3
"""Bounded convergence for AI-executed tasks.

A task is admitted with a frozen execution envelope: its acceptance items,
its scope, finite corrective/review allowances, and stagnation thresholds.
Execution then reports events. Only accepted outcomes and resolved blockers
count as progress; commits, tests, reviews, and new findings are activity.
The evaluator turns that evidence into one of five states:

    HEALTHY        progress is being made inside the envelope
    WATCH          a cycle ended without progress
    REALIGN        work drifted from the envelope; only alignment work allowed
    CIRCUIT_BREAK  loop or exhaustion detected; stop and return to the owner
    COMPLETE       every frozen acceptance item is satisfied; stop

The same state is rendered as an Owner Footer for the human and an Agent
Handoff for the next session, so any replaceable engine can resume from
durable state instead of chat history.

Standard library only. All data in this repository is synthetic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


STATES = ("HEALTHY", "WATCH", "REALIGN", "CIRCUIT_BREAK", "COMPLETE")
STOPPING_STATES = {"CIRCUIT_BREAK", "COMPLETE"}
EVENT_KINDS = {
    "accept",
    "activity",
    "corrective",
    "review",
    "finding",
    "blocker",
    "resolve_blocker",
    "scope_change",
    "checkpoint",
}


class ConvergenceError(ValueError):
    """Raised for an invalid envelope or event."""


@dataclass(frozen=True)
class Envelope:
    """The frozen admission contract. Nothing downstream may widen it."""

    task_ref: str
    north_star: str
    acceptance: tuple[str, ...]
    scope: tuple[str, ...]
    corrective_limit: int
    review_limit: int
    realign_after: int
    circuit_break_after: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Envelope":
        required = {
            "task_ref", "north_star", "acceptance", "scope", "corrective_limit",
            "review_limit", "realign_after", "circuit_break_after",
        }
        missing = required - set(data)
        if missing:
            raise ConvergenceError(f"envelope is missing: {', '.join(sorted(missing))}")
        acceptance = tuple(data["acceptance"])
        if not acceptance or len(set(acceptance)) != len(acceptance):
            raise ConvergenceError("acceptance must be a non-empty list of unique IDs")
        for name in ("corrective_limit", "review_limit", "realign_after", "circuit_break_after"):
            if not isinstance(data[name], int) or data[name] < 0:
                raise ConvergenceError(f"{name} must be a non-negative integer")
        if not 0 < data["realign_after"] < data["circuit_break_after"]:
            raise ConvergenceError("require 0 < realign_after < circuit_break_after")
        return cls(
            task_ref=str(data["task_ref"]),
            north_star=str(data["north_star"]),
            acceptance=acceptance,
            scope=tuple(data["scope"]),
            corrective_limit=data["corrective_limit"],
            review_limit=data["review_limit"],
            realign_after=data["realign_after"],
            circuit_break_after=data["circuit_break_after"],
        )


@dataclass
class TaskState:
    envelope: Envelope
    state: str = "HEALTHY"
    accepted: list[str] = field(default_factory=list)
    correctives_used: int = 0
    reviews_used: int = 0
    stagnation_cycles: int = 0
    progress_this_cycle: bool = False
    open_blockers: dict[str, int] = field(default_factory=dict)
    blocker_history: dict[str, int] = field(default_factory=dict)
    deferred_findings: list[str] = field(default_factory=list)
    activity: dict[str, int] = field(default_factory=dict)
    reason: str = ""
    next_action: str = ""
    log: list[str] = field(default_factory=list)

    @property
    def remaining(self) -> list[str]:
        return [item for item in self.envelope.acceptance if item not in self.accepted]


def _stop(task: TaskState, state: str, reason: str) -> None:
    task.state = state
    task.reason = reason
    task.log.append(f"{state}: {reason}")


def apply_event(task: TaskState, event: dict[str, Any]) -> TaskState:
    """Apply one event. A stopped task rejects further execution events."""
    kind = event.get("kind")
    if kind not in EVENT_KINDS:
        raise ConvergenceError(f"unknown event kind: {kind!r}")
    if task.state in STOPPING_STATES:
        task.log.append(f"ignored {kind}: task already {task.state}")
        return task
    envelope = task.envelope
    if task.state == "REALIGN" and kind in {"corrective", "scope_change"}:
        # REALIGN permits alignment work only; material change escalates.
        _stop(task, "CIRCUIT_BREAK", f"{kind} attempted while REALIGN allows alignment only")
        return task
    note = event.get("note", "")
    if note:
        task.next_action = note

    if kind == "accept":
        item = event["item"]
        if item not in envelope.acceptance:
            # Satisfying something outside the frozen list is drift, not progress.
            _stop(task, "REALIGN", f"{item} is not a frozen acceptance item")
            return task
        if item not in task.accepted:
            task.accepted.append(item)
            task.progress_this_cycle = True
            task.log.append(f"accepted {item}")
        if not task.remaining:
            _stop(task, "COMPLETE", "every frozen acceptance item is satisfied")
            task.next_action = "Close out; deferred findings go back to the owner as proposals."

    elif kind == "activity":
        what = event.get("what", "work")
        task.activity[what] = task.activity.get(what, 0) + int(event.get("count", 1))
    elif kind == "corrective":
        if task.correctives_used >= envelope.corrective_limit:
            _stop(task, "CIRCUIT_BREAK", "corrective allowance exhausted")
            return task
        task.correctives_used += 1
        task.activity["correctives"] = task.activity.get("correctives", 0) + 1
    elif kind == "review":
        if task.reviews_used >= envelope.review_limit:
            _stop(task, "CIRCUIT_BREAK", "review allowance exhausted")
            return task
        task.reviews_used += 1
        task.activity["reviews"] = task.activity.get("reviews", 0) + 1
    elif kind == "finding":
        summary = event.get("summary", "finding")
        if event.get("in_scope", False):
            # An inside-envelope defect may enter the finite corrective path.
            task.log.append(f"in-scope finding queued for correction: {summary}")
        else:
            # Outside-envelope findings are evidence, never new work.
            task.deferred_findings.append(summary)
            task.log.append(f"deferred out-of-scope finding: {summary}")
    elif kind == "blocker":
        family = event["family"]
        task.blocker_history[family] = task.blocker_history.get(family, 0) + 1
        task.open_blockers[family] = task.open_blockers.get(family, 0) + 1
        if task.blocker_history[family] >= 2:
            _stop(task, "CIRCUIT_BREAK", f"blocker family '{family}' repeated")
    elif kind == "resolve_blocker":
        family = event["family"]
        if task.open_blockers.pop(family, None) is not None:
            task.progress_this_cycle = True
            task.log.append(f"resolved blocker {family}")
    elif kind == "scope_change":
        # The envelope is frozen; widening it needs a new owner admission.
        _stop(task, "REALIGN", "scope change requested without re-admission")
    elif kind == "checkpoint":
        _close_cycle(task)
    return task


def _close_cycle(task: TaskState) -> None:
    envelope = task.envelope
    if task.progress_this_cycle:
        task.stagnation_cycles = 0
        if task.state in {"WATCH", "REALIGN"}:
            task.log.append(f"{task.state} cleared by verified progress")
        task.state = "HEALTHY"
        task.reason = ""
    else:
        task.stagnation_cycles += 1
        if task.stagnation_cycles >= envelope.circuit_break_after:
            _stop(task, "CIRCUIT_BREAK", f"{task.stagnation_cycles} cycles without accepted progress")
        elif task.stagnation_cycles >= envelope.realign_after:
            _stop(task, "REALIGN", f"{task.stagnation_cycles} cycles without accepted progress")
        else:
            task.state = "WATCH"
            task.reason = "cycle ended without accepted progress"
    task.progress_this_cycle = False


def run(envelope_data: dict[str, Any], events: list[dict[str, Any]]) -> TaskState:
    task = TaskState(envelope=Envelope.from_dict(envelope_data))
    for event in events:
        apply_event(task, event)
    return task


# ---------------------------------------------------------------- rendering

DECISIONS = {
    "HEALTHY": ("CONTINUE", "繼續"),
    "WATCH": ("CONTINUE, NARROW", "繼續並縮小範圍"),
    "REALIGN": ("ALIGN ONLY", "只做對齊"),
    "CIRCUIT_BREAK": ("STOP, OWNER DECIDES", "停止，交回決定"),
    "COMPLETE": ("STOP, DONE", "完成並停止"),
}

LABELS = {
    "en": {
        "goal": "Goal", "progress": "Progress", "loop": "Loop", "align": "Align",
        "blocker": "Blocker", "deferred": "Deferred", "next": "Next",
        "decision": "Decision", "none": "none", "ok": "on target",
        "drift": "drifted", "cycles": "stalled cycles",
    },
    "zh-TW": {
        "goal": "主線", "progress": "進度", "loop": "循環", "align": "對齊",
        "blocker": "卡點", "deferred": "延後", "next": "後續",
        "decision": "決策", "none": "無", "ok": "目標 ✓ · 範圍 ✓",
        "drift": "偏離", "cycles": "無進度輪數",
    },
}


def _bar(done: int, total: int, cells: int = 10) -> str:
    filled = round(cells * done / total)
    return "■" * filled + "□" * (cells - filled)


def render_owner(task: TaskState, lang: str = "en") -> str:
    if lang not in LABELS:
        raise ConvergenceError(f"unsupported language: {lang}")
    text = LABELS[lang]
    envelope = task.envelope
    total = len(envelope.acceptance)
    done = len(task.accepted)
    decision_en, decision_zh = DECISIONS[task.state]
    decision = decision_zh if lang == "zh-TW" else decision_en
    align = text["drift"] if task.state == "REALIGN" else text["ok"]
    loop = f"{task.state} · {text['cycles']} {task.stagnation_cycles}"
    blockers = ", ".join(sorted(task.open_blockers)) or text["none"]
    rows = [
        f"Canopus · {envelope.task_ref}",
        "─" * 20,
        f"{text['goal']} │ {envelope.north_star}",
        f"{text['progress']} │ {_bar(done, total)} {done} / {total}",
        f"{text['loop']} │ {loop}",
        f"{text['align']} │ {align}",
        f"{text['blocker']} │ {blockers}",
    ]
    if task.deferred_findings:
        rows.append(f"{text['deferred']} │ {len(task.deferred_findings)}")
    if task.reason:
        rows.append(f"{'原因' if lang == 'zh-TW' else 'Reason'} │ {task.reason}")
    rows.append(f"{text['next']} │ {task.next_action or text['none']}")
    rows.append(f"{text['decision']} │ {decision}")
    return "\n".join(rows)


def render_agent(task: TaskState) -> str:
    envelope = task.envelope
    successor = {
        "HEALTHY": "CONTINUE | mutation allowed",
        "WATCH": "CONTINUE NARROWED | mutation allowed",
        "REALIGN": "ALIGNMENT ONLY | material mutation blocked",
        "CIRCUIT_BREAK": "STOP | mutation blocked until owner re-admission",
        "COMPLETE": "STOP | no further execution",
    }[task.state]
    activity = ", ".join(f"{k}={v}" for k, v in sorted(task.activity.items())) or "none"
    lines = [
        "CANOPUS AGENT HANDOFF",
        f"Task: {envelope.task_ref} | state {task.state}",
        f"North Star: {envelope.north_star}",
        f"Acceptance: {len(task.accepted)}/{len(envelope.acceptance)} | remaining {', '.join(task.remaining) or 'none'}",
        f"Scope (frozen): {', '.join(envelope.scope)}",
        f"Allowances: corrective {task.correctives_used}/{envelope.corrective_limit} | review {task.reviews_used}/{envelope.review_limit}",
        f"Stagnation: {task.stagnation_cycles} (realign at {envelope.realign_after}, break at {envelope.circuit_break_after})",
        f"Activity (not progress): {activity}",
        f"Deferred findings: {len(task.deferred_findings)}",
        f"Successor: {successor}",
    ]
    if task.reason:
        lines.append(f"Stop reason: {task.reason}")
    if task.next_action:
        lines.append(f"Next: {task.next_action}")
    return "\n".join(lines)


def footer_last_gate(response: str, footer: str) -> str:
    """Return PASS only when the response ends with the exact rendered footer.

    This mirrors a stop-hook check: an agent may not end a substantial turn
    without handing the owner the current state.
    """
    return "PASS" if response.rstrip().endswith(footer.rstrip()) else "BLOCK"

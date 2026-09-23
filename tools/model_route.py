#!/usr/bin/env python3
"""Recommend a model tier for a task. Recommendation only: launches nothing.

Inputs are a task class, a risk level (R0-R3), optional capability needs,
and optional outcome evidence. The catalog (routing/catalog.toml) describes
synthetic, vendor-neutral tiers. The rule is "cheapest adequate tier":

1. required capability = max(risk floor, task-class minimum);
2. a tier is eligible when its capability meets that bar (unless it is
   exempt from the risk floor), its max_risk covers the task risk, it offers
   every requested need, and it serves the task class if it lists classes;
3. evidence can disqualify a tier: with at least ``--min-samples`` recorded
   outcomes for this task class and a pass rate under 50%, it is rejected;
4. eligible tiers are ranked by relative cost, then by capability;
   the next more capable eligible tier is named as the escalation path.

Engines are replaceable: the output names a tier, and the owner maps tiers
to concrete engines outside this repository.

    python3 tools/model_route.py --task-class implementation --risk R2 \\
        [--need long-context] [--evidence outcomes.json] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _toml  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "routing" / "catalog.toml"
RISKS = ("R0", "R1", "R2", "R3")


class RouteError(ValueError):
    """Invalid catalog or request."""


@dataclass
class Verdict:
    tier: str
    eligible: bool
    capability: int
    relative_cost: float
    reasons: list[str] = field(default_factory=list)


def load_catalog(path: Path = CATALOG) -> dict[str, Any]:
    try:
        data = _toml.read_toml(path)
    except (OSError, ValueError) as error:
        raise RouteError(f"cannot read catalog {path}: {error}") from error
    if data.get("version") != 1:
        raise RouteError("catalog version must be 1")
    tiers, classes, floors = data.get("tier"), data.get("task_class"), data.get("risk_floor")
    if not isinstance(tiers, list) or not tiers:
        raise RouteError("catalog needs at least one [[tier]]")
    if not isinstance(classes, dict) or not classes:
        raise RouteError("catalog needs [task_class.*] entries")
    if not isinstance(floors, dict) or set(floors) != set(RISKS):
        raise RouteError(f"risk_floor must define exactly {', '.join(RISKS)}")
    seen = set()
    for tier in tiers:
        tier_id = tier.get("id") if isinstance(tier, dict) else None
        if not isinstance(tier_id, str) or tier_id in seen:
            raise RouteError(f"tier ids must be unique strings (got {tier_id!r})")
        seen.add(tier_id)
        if not isinstance(tier.get("capability"), int) or not isinstance(tier.get("relative_cost"), (int, float)):
            raise RouteError(f"tier {tier_id}: capability (int) and relative_cost (number) are required")
        if tier.get("max_risk") not in RISKS:
            raise RouteError(f"tier {tier_id}: max_risk must be one of {', '.join(RISKS)}")
        for name in ("capabilities", "task_classes"):
            if not isinstance(tier.get(name, []), list):
                raise RouteError(f"tier {tier_id}: {name} must be a list")
        unknown = set(tier.get("task_classes", [])) - set(classes)
        if unknown:
            raise RouteError(f"tier {tier_id}: unknown task classes {sorted(unknown)}")
    return data


def pass_rates(evidence: list[dict[str, Any]], task_class: str) -> dict[str, tuple[int, int]]:
    """Return {tier: (passes, total)} for this task class."""
    rates: dict[str, tuple[int, int]] = {}
    for record in evidence:
        if not isinstance(record, dict) or record.get("task_class") != task_class:
            continue
        if record.get("outcome") not in {"pass", "fail"}:
            raise RouteError(f"evidence outcome must be 'pass' or 'fail': {record}")
        passes, total = rates.get(record.get("tier"), (0, 0))
        rates[record.get("tier")] = (passes + (record["outcome"] == "pass"), total + 1)
    return rates


def route(catalog: dict[str, Any], task_class: str, risk: str, needs: list[str] | None = None,
          evidence: list[dict[str, Any]] | None = None, min_samples: int = 3) -> dict[str, Any]:
    if task_class not in catalog["task_class"]:
        raise RouteError(f"unknown task class {task_class!r}; known: {', '.join(sorted(catalog['task_class']))}")
    if risk not in RISKS:
        raise RouteError(f"risk must be one of {', '.join(RISKS)}")
    needs = sorted(set(needs or []))
    required = max(catalog["risk_floor"][risk], catalog["task_class"][task_class].get("min_capability", 0))
    rates = pass_rates(evidence or [], task_class)
    verdicts = []
    for tier in catalog["tier"]:
        verdict = Verdict(tier["id"], True, tier["capability"], tier["relative_cost"])
        exempt = tier.get("exempt_from_risk_floor", False)
        bar = catalog["task_class"][task_class].get("min_capability", 0) if exempt else required
        classes = tier.get("task_classes")
        if classes and task_class not in classes:
            verdict.eligible = False
            verdict.reasons.append(f"serves only {', '.join(classes)}")
        if tier["capability"] < bar:
            verdict.eligible = False
            verdict.reasons.append(f"capability {tier['capability']} < required {bar}")
        if RISKS.index(risk) > RISKS.index(tier["max_risk"]):
            verdict.eligible = False
            verdict.reasons.append(f"max risk {tier['max_risk']} < {risk}")
        missing = [need for need in needs if need not in tier.get("capabilities", [])]
        if missing:
            verdict.eligible = False
            verdict.reasons.append(f"lacks {', '.join(missing)}")
        passes, total = rates.get(tier["id"], (0, 0))
        if total >= min_samples and passes * 2 < total:
            verdict.eligible = False
            verdict.reasons.append(f"evidence {passes}/{total} passes for {task_class}")
        elif total:
            verdict.reasons.append(f"evidence {passes}/{total} passes")
        if verdict.eligible and not verdict.reasons[:1]:
            verdict.reasons.insert(0, "adequate")
        verdicts.append(verdict)
    ranked = sorted((v for v in verdicts if v.eligible), key=lambda v: (v.relative_cost, -v.capability))
    rejected = [v for v in verdicts if not v.eligible]
    top = ranked[0] if ranked else None
    escalation = next((v for v in ranked[1:] if top and v.capability > top.capability), None)
    return {
        "task_class": task_class, "risk": risk, "needs": needs, "required_capability": required,
        "recommendation": top.tier if top else None,
        "escalate_to": escalation.tier if escalation else None,
        "ranked": [vars(v) for v in ranked], "rejected": [vars(v) for v in rejected],
        "note": "recommendation only; nothing was launched",
    }


def render(result: dict[str, Any]) -> str:
    lines = [f"task {result['task_class']} · risk {result['risk']} · needs "
             f"{', '.join(result['needs']) or 'none'} · required capability {result['required_capability']}"]
    if result["recommendation"]:
        lines.append(f"recommend: {result['recommendation']}"
                     + (f" (escalate to {result['escalate_to']} if it fails verification)"
                        if result["escalate_to"] else ""))
    else:
        lines.append("recommend: none eligible; the owner decides (split the task or add a tier)")
    for index, verdict in enumerate(result["ranked"], 1):
        lines.append(f"  {index}. {verdict['tier']:<14} cost {verdict['relative_cost']:<4} "
                     f"{'; '.join(verdict['reasons'])}")
    for verdict in result["rejected"]:
        lines.append(f"  -  {verdict['tier']:<14} rejected: {'; '.join(verdict['reasons'])}")
    lines.append(result["note"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recommend a model tier (never launches anything).")
    parser.add_argument("--task-class", required=True)
    parser.add_argument("--risk", required=True, choices=RISKS)
    parser.add_argument("--need", action="append", default=[], help="required capability; repeatable")
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--evidence", type=Path, help="JSON list of {tier, task_class, outcome}")
    parser.add_argument("--min-samples", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        evidence = None
        if args.evidence:
            try:
                evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise RouteError(f"cannot read evidence: {error}") from error
            if not isinstance(evidence, list):
                raise RouteError("evidence must be a JSON list")
        result = route(load_catalog(args.catalog), args.task_class, args.risk, args.need,
                       evidence, args.min_samples)
    except RouteError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0 if result["recommendation"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

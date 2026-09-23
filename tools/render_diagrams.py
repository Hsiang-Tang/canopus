#!/usr/bin/env python3
"""Render the README diagrams as light and dark SVG files.

    python3 tools/render_diagrams.py            # write docs/assets/*.svg
    python3 tools/render_diagrams.py --check    # fail if committed SVGs are stale

Standard library only. GitHub strips scripts and external fonts from SVG, so
every diagram uses inline shapes and a system font stack.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

THEMES = {
    "light": {
        "bg": "#ffffff", "surface": "#f6f8fa", "border": "#d0d7de", "text": "#1f2328",
        "muted": "#59636e", "line": "#8c959f", "blue": "#0969da", "blue_bg": "#ddf4ff",
        "green": "#1a7f37", "green_bg": "#dafbe1", "amber": "#9a6700", "amber_bg": "#fff8c5",
        "red": "#cf222e", "red_bg": "#ffebe9", "purple": "#8250df", "purple_bg": "#fbefff",
    },
    "dark": {
        "bg": "#0d1117", "surface": "#161b22", "border": "#30363d", "text": "#e6edf3",
        "muted": "#9198a1", "line": "#6e7681", "blue": "#4493f8", "blue_bg": "#0c2d6b",
        "green": "#3fb950", "green_bg": "#0f3d1e", "amber": "#d29922", "amber_bg": "#3d2e00",
        "red": "#f85149", "red_bg": "#4a1113", "purple": "#ab7df8", "purple_bg": "#2e1a55",
    },
}


class Canvas:
    def __init__(self, width: int, height: int, theme: dict[str, str]) -> None:
        self.w, self.h, self.t = width, height, theme
        self.parts: list[str] = []

    def rect(self, x, y, w, h, fill, stroke, radius=10, width=1.5, dash=False):
        extra = ' stroke-dasharray="5 4"' if dash else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"{extra}/>'
        )

    def text(self, x, y, value, size=14, color=None, weight=400, anchor="middle", mono=False):
        family = MONO if mono else FONT
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color or self.t["text"]}" '
            f'text-anchor="{anchor}">{escape(value)}</text>'
        )

    def node(self, x, y, w, h, title, subtitle, accent, accent_bg):
        self.rect(x, y, w, h, accent_bg, accent)
        self.text(x + w / 2, y + h / 2 - 4, title, 15, weight=600)
        self.text(x + w / 2, y + h / 2 + 15, subtitle, 12, self.t["muted"])

    def arrow(self, d, color=None, label=None, lx=0, ly=0, dash=False, anchor="middle"):
        color = color or self.t["line"]
        extra = ' stroke-dasharray="6 5"' if dash else ""
        marker = "url(#head-" + color.lstrip("#") + ")"
        self.parts.append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8"{extra} '
            f'marker-end="{marker}"/>'
        )
        self.markers.add(color)
        if label:
            self.text(lx, ly, label, 12, self.t["muted"], anchor=anchor)

    markers: set[str]

    def svg(self, title: str) -> str:
        defs = "".join(
            f'<marker id="head-{c.lstrip("#")}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
            for c in sorted(self.markers)
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" role="img" aria-label="{escape(title)}">'
            f"<title>{escape(title)}</title><defs>{defs}</defs>"
            f'<rect width="{self.w}" height="{self.h}" rx="14" fill="{self.t["bg"]}" '
            f'stroke="{self.t["border"]}"/>' + "".join(self.parts) + "</svg>\n"
        )


def continuation_loop(theme: dict[str, str]) -> str:
    t = theme
    c = Canvas(1150, 500, t)
    c.markers = set()
    c.text(28, 38, "The continuation loop", 18, weight=700, anchor="start")
    c.text(28, 60, "Replaceable agents work one frozen goal; a deterministic gate decides whether they continue.",
           13, t["muted"], anchor="start")

    y = 170
    c.node(28, y, 138, 70, "Owner", "intent · decisions", t["purple"], t["purple_bg"])
    c.node(206, y - 8, 190, 86, "Frozen envelope", "acceptance · scope", t["blue"], t["blue_bg"])
    c.text(301, y + 64, "finite allowances", 12, t["muted"])
    c.node(436, y, 150, 70, "Brain", "plan · review · judge", t["blue"], t["surface"])
    c.node(626, y, 150, 70, "Executor", "change · test · deliver", t["blue"], t["surface"])
    c.arrow(f"M166,{y + 35} H200")
    c.arrow(f"M396,{y + 35} H430")
    c.arrow(f"M586,{y + 25} H620")
    c.arrow(f"M626,{y + 47} H592")

    gx, gy = 884, y + 35
    c.parts.append(
        f'<polygon points="{gx},{gy - 60} {gx + 80},{gy} {gx},{gy + 60} {gx - 80},{gy}" '
        f'fill="{t["amber_bg"]}" stroke="{t["amber"]}" stroke-width="1.5"/>'
    )
    c.text(gx, gy - 4, "Convergence", 14, weight=600)
    c.text(gx, gy + 14, "gate", 14, weight=600)
    c.arrow(f"M776,{gy} H798")

    pills = [
        (104, "COMPLETE", "stop at done", t["green"], t["green_bg"]),
        (172, "REALIGN", "alignment work only", t["amber"], t["amber_bg"]),
        (240, "CIRCUIT_BREAK", "stop · owner decides", t["red"], t["red_bg"]),
    ]
    for py, name, sub, color, bg in pills:
        c.rect(976, py, 146, 50, bg, color, radius=25)
        c.text(1049, py + 22, name, 13, color, weight=700, mono=True)
        c.text(1049, py + 39, sub, 11, t["muted"])
    c.arrow(f"M{gx + 44},{gy - 30} L970,129", t["green"])
    c.arrow(f"M{gx + 82},{gy} H970", t["amber"])
    c.arrow(f"M{gx + 44},{gy + 30} L970,265", t["red"])
    c.arrow(f"M1122,265 H1134 V88 H97 V{y - 6}", t["red"], "blocked or looping → back to the owner", 600, 82, dash=True)

    fy = 330
    c.rect(300, fy, 760, 146, t["surface"], t["border"], radius=12)
    c.text(318, fy + 26, "Task Footer · one state, three views", 14, weight=600, anchor="start")
    c.arrow(f"M{gx},{gy + 60} V{fy - 4}", t["green"], "progress", gx + 10, gy + 92, anchor="start")
    cards = [
        (318, "Machine state", "full structured evidence", "validated JSON"),
        (566, "Agent Handoff", "for the next session", "any engine resumes"),
        (814, "Owner Footer", "for the human", "English or zh-TW"),
    ]
    for x, title, sub, tag in cards:
        c.rect(x, fy + 42, 228, 86, t["bg"], t["border"], radius=10)
        c.text(x + 114, fy + 72, title, 15, weight=600)
        c.text(x + 114, fy + 92, sub, 12, t["muted"])
        c.text(x + 114, fy + 114, tag, 12, t["blue"], mono=True)
    c.arrow(f"M680,{fy + 42} V{fy + 18} Q680,{fy - 20} 560,{fy - 20} H511 V{y + 76}", t["blue"],
            "next session resumes from durable state", 520, fy - 30, dash=True, anchor="start")
    c.arrow(f"M300,{fy + 110} H97 V{y + 76}", t["purple"], "owner sees state", 110, fy + 100, anchor="start")
    return c.svg("Canopus continuation loop")


def convergence_states(theme: dict[str, str]) -> str:
    t = theme
    c = Canvas(1120, 330, t)
    c.markers = set()
    c.text(28, 38, "Bounded convergence", 18, weight=700, anchor="start")
    c.text(28, 60, "Only accepted outcomes and resolved blockers are progress. Commits, tests, and reviews are activity.",
           13, t["muted"], anchor="start")
    states = [
        (28, "HEALTHY", t["blue"], t["blue_bg"], "progress this cycle"),
        (300, "WATCH", t["amber"], t["amber_bg"], "a cycle ended with no outcome"),
        (572, "REALIGN", t["amber"], t["amber_bg"], "stall ≥ realign · scope change"),
        (844, "CIRCUIT_BREAK", t["red"], t["red_bg"], "stall ≥ break · allowance spent"),
    ]
    y = 150
    for x, name, color, bg, trig in states:
        c.rect(x, y, 248, 66, bg, color, radius=12)
        c.text(x + 124, y + 30, name, 16, color, weight=700, mono=True)
        c.text(x + 124, y + 50, trig, 12, t["muted"])
    for x in (276, 548, 820):
        c.arrow(f"M{x},{y + 33} H{x + 20}")
    c.arrow(f"M686,{y} Q686,{y - 46} 400,{y - 46} Q152,{y - 46} 152,{y - 4}", t["green"],
            "verified progress resets the stall counter", 420, y - 54, dash=True)
    c.rect(28, 256, 248, 50, t["green_bg"], t["green"], radius=25)
    c.text(152, 278, "COMPLETE", 15, t["green"], weight=700, mono=True)
    c.text(152, 296, "every frozen item accepted → stop", 11, t["muted"])
    c.arrow(f"M152,{y + 66} V250", t["green"])
    notes = [
        (300, "Out-of-scope findings are deferred, never executed."),
        (300, "Allowances only decrease; a repeated blocker family breaks early."),
        (300, "Material work during REALIGN escalates to CIRCUIT_BREAK."),
    ]
    for i, (x, line) in enumerate(notes):
        c.text(x, 262 + i * 20, "•  " + line, 13, t["muted"], anchor="start")
    return c.svg("Canopus bounded convergence states")


def framework_map(theme: dict[str, str]) -> str:
    t = theme
    c = Canvas(1150, 360, t)
    c.markers = set()
    c.text(28, 38, "What is in the framework", 18, weight=700, anchor="start")
    c.text(28, 60, "Five layers, each backed by a tested tool.", 13, t["muted"], anchor="start")
    columns = [
        ("Method", t["purple"], t["purple_bg"], ["risk-scaled SDD", "spec kit · ADRs", "North Star envelope", "assumptions first", "anti-over-engineering"], "rules/ · docs/methodology/"),
        ("Bootstrap", t["blue"], t["blue_bg"], ["one-command install", "Claude Code + Codex", "AGENTS.md canonical", "CLAUDE.md imports it", "dry-run by default"], "install_bootstrap.py"),
        ("Task loop", t["green"], t["green_bg"], ["admit · event · close", "convergence gate", "Owner Footer", "Agent Handoff", "durable across sessions"], "canopus_task.py · convergence.py"),
        ("Enforcement", t["red"], t["red_bg"], ["Stop hook latch", "footer-last gate", "one-way per session", "no silent exit", "never blocks twice"], "footer_latch.py"),
        ("Coordination", t["amber"], t["amber_bg"], ["model routing", "parallel workstreams", "one writer per checkout", "scope collisions", "workspace doctor"], "model_route.py · workstream.py"),
    ]
    x, w, gap = 28, 210, 12
    for title, color, bg, items, tool in columns:
        c.rect(x, 86, w, 250, t["surface"], t["border"], radius=12)
        c.rect(x, 86, w, 44, bg, color, radius=12)
        c.text(x + w / 2, 114, title, 16, color, weight=700)
        for i, item in enumerate(items):
            c.text(x + 16, 162 + i * 30, "›  " + item, 13, anchor="start")
        c.text(x + w / 2, 316, tool, 11, t["muted"], mono=True)
        x += w + gap
    return c.svg("Canopus framework map")


DIAGRAMS = {
    "continuation-loop": continuation_loop,
    "convergence-states": convergence_states,
    "framework-map": framework_map,
}


def render_all() -> dict[Path, str]:
    return {
        ASSETS / f"{name}-{theme_name}.svg": build(theme)
        for name, build in DIAGRAMS.items()
        for theme_name, theme in THEMES.items()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = render_all()
    if args.check:
        stale = [p for p, body in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != body]
        for path in stale:
            print(f"stale diagram: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1 if stale else 0
    ASSETS.mkdir(parents=True, exist_ok=True)
    for path, body in outputs.items():
        path.write_text(body, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

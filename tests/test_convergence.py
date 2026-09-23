import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import convergence  # noqa: E402
import convergence_demo  # noqa: E402


def envelope(**overrides):
    data = {
        "task_ref": "TEST-1",
        "north_star": "Synthetic goal",
        "acceptance": ["AC1", "AC2"],
        "scope": ["synthetic scope"],
        "corrective_limit": 1,
        "review_limit": 1,
        "realign_after": 2,
        "circuit_break_after": 3,
    }
    data.update(overrides)
    return data


def cycles(count, *events):
    out = []
    for _ in range(count):
        out.extend(events)
        out.append({"kind": "checkpoint"})
    return out


class EnvelopeTests(unittest.TestCase):
    def test_rejects_missing_fields(self):
        data = envelope()
        del data["scope"]
        with self.assertRaises(convergence.ConvergenceError):
            convergence.Envelope.from_dict(data)

    def test_rejects_duplicate_or_empty_acceptance(self):
        for acceptance in ([], ["AC1", "AC1"]):
            with self.assertRaises(convergence.ConvergenceError):
                convergence.Envelope.from_dict(envelope(acceptance=acceptance))

    def test_thresholds_must_be_ordered(self):
        with self.assertRaises(convergence.ConvergenceError):
            convergence.Envelope.from_dict(envelope(realign_after=3, circuit_break_after=3))

    def test_unknown_event_is_rejected(self):
        with self.assertRaises(convergence.ConvergenceError):
            convergence.run(envelope(), [{"kind": "celebrate"}])


class ConvergenceRuleTests(unittest.TestCase):
    def test_complete_stops_and_ignores_later_work(self):
        task = convergence.run(envelope(), [
            {"kind": "accept", "item": "AC1"},
            {"kind": "accept", "item": "AC2"},
            {"kind": "corrective"},
            {"kind": "scope_change"},
        ])
        self.assertEqual(task.state, "COMPLETE")
        self.assertEqual(task.correctives_used, 0)
        self.assertTrue(any("ignored" in line for line in task.log))

    def test_activity_never_counts_as_progress(self):
        busy = {"kind": "activity", "what": "commits", "count": 50}
        task = convergence.run(envelope(), cycles(3, busy, {"kind": "activity", "what": "tests", "count": 500}))
        self.assertEqual(task.state, "CIRCUIT_BREAK")
        self.assertEqual(task.activity["commits"], 150)
        self.assertEqual(task.accepted, [])

    def test_stagnation_escalates_watch_realign_break(self):
        task = convergence.TaskState(envelope=convergence.Envelope.from_dict(envelope()))
        seen = []
        for _ in range(3):
            convergence.apply_event(task, {"kind": "checkpoint"})
            seen.append(task.state)
        self.assertEqual(seen, ["WATCH", "REALIGN", "CIRCUIT_BREAK"])

    def test_verified_progress_resets_stagnation(self):
        task = convergence.run(envelope(), [
            {"kind": "checkpoint"},
            {"kind": "accept", "item": "AC1"},
            {"kind": "checkpoint"},
        ])
        self.assertEqual(task.state, "HEALTHY")
        self.assertEqual(task.stagnation_cycles, 0)

    def test_resolving_a_blocker_is_progress(self):
        task = convergence.run(envelope(), [
            {"kind": "blocker", "family": "access"},
            {"kind": "checkpoint"},
            {"kind": "resolve_blocker", "family": "access"},
            {"kind": "checkpoint"},
        ])
        self.assertEqual(task.state, "HEALTHY")
        self.assertEqual(task.open_blockers, {})

    def test_allowances_never_replenish(self):
        task = convergence.run(envelope(), [
            {"kind": "corrective"},
            {"kind": "accept", "item": "AC1"},
            {"kind": "checkpoint"},
            {"kind": "corrective"},
        ])
        self.assertEqual(task.state, "CIRCUIT_BREAK")
        self.assertIn("corrective allowance", task.reason)

    def test_review_allowance_is_finite(self):
        task = convergence.run(envelope(review_limit=0), [{"kind": "review"}])
        self.assertEqual(task.state, "CIRCUIT_BREAK")

    def test_out_of_scope_finding_is_deferred_not_executed(self):
        task = convergence.run(envelope(), [
            {"kind": "finding", "summary": "nice extra", "in_scope": False},
        ])
        self.assertEqual(task.state, "HEALTHY")
        self.assertEqual(task.deferred_findings, ["nice extra"])
        self.assertEqual(task.envelope.acceptance, ("AC1", "AC2"))

    def test_scope_change_realigns_and_material_work_then_breaks(self):
        task = convergence.run(envelope(), [{"kind": "scope_change"}])
        self.assertEqual(task.state, "REALIGN")
        convergence.apply_event(task, {"kind": "corrective"})
        self.assertEqual(task.state, "CIRCUIT_BREAK")

    def test_accepting_unfrozen_item_is_drift(self):
        task = convergence.run(envelope(), [{"kind": "accept", "item": "AC99"}])
        self.assertEqual(task.state, "REALIGN")
        self.assertEqual(task.accepted, [])

    def test_repeated_blocker_family_breaks(self):
        task = convergence.run(envelope(), [
            {"kind": "blocker", "family": "access"},
            {"kind": "checkpoint"},
            {"kind": "blocker", "family": "access"},
        ])
        self.assertEqual(task.state, "CIRCUIT_BREAK")


class RenderingTests(unittest.TestCase):
    def test_owner_footer_has_every_row_in_both_languages(self):
        task = convergence.run(envelope(), [{"kind": "accept", "item": "AC1"}])
        english = convergence.render_owner(task, "en")
        for label in ("Goal │", "Progress │", "Loop │", "Align │", "Blocker │", "Next │", "Decision │"):
            self.assertIn(label, english)
        chinese = convergence.render_owner(task, "zh-TW")
        for label in ("主線 │", "進度 │", "循環 │", "對齊 │", "卡點 │", "後續 │", "決策 │"):
            self.assertIn(label, chinese)
        self.assertIn("1 / 2", english)

    def test_agent_handoff_blocks_mutation_after_break(self):
        task = convergence.run(envelope(), cycles(3))
        handoff = convergence.render_agent(task)
        self.assertIn("state CIRCUIT_BREAK", handoff)
        self.assertIn("mutation blocked", handoff)
        self.assertIn("Activity (not progress)", handoff)

    def test_footer_last_gate(self):
        task = convergence.run(envelope(), [])
        footer = convergence.render_owner(task)
        self.assertEqual(convergence.footer_last_gate(f"Summary.\n\n{footer}\n", footer), "PASS")
        self.assertEqual(convergence.footer_last_gate(f"{footer}\n\nOne more thing.", footer), "BLOCK")
        self.assertEqual(convergence.footer_last_gate("No footer at all.", footer), "BLOCK")

    def test_unsupported_language_is_rejected(self):
        task = convergence.run(envelope(), [])
        with self.assertRaises(convergence.ConvergenceError):
            convergence.render_owner(task, "fr")


class ScenarioTests(unittest.TestCase):
    EXPECTED = {
        "clean-delivery.json": "COMPLETE",
        "runaway-fix-loop.json": "CIRCUIT_BREAK",
        "scope-drift.json": "REALIGN",
        "repeated-blocker.json": "CIRCUIT_BREAK",
    }

    def test_bundled_scenarios_reach_their_documented_state(self):
        paths = sorted((ROOT / "examples" / "scenarios").glob("*.json"))
        self.assertEqual({path.name for path in paths}, set(self.EXPECTED))
        for path in paths:
            data = json.loads(path.read_text(encoding="utf-8"))
            task = convergence.run(data["envelope"], data["events"])
            self.assertEqual(task.state, self.EXPECTED[path.name], path.name)

    def test_demo_cli_replays_all_scenarios(self):
        buffer = StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(convergence_demo.main(["--all", "--no-trace"]), 0)
        output = buffer.getvalue()
        self.assertEqual(output.count("CANOPUS AGENT HANDOFF"), 4)
        self.assertIn("STOP, OWNER DECIDES", output)


if __name__ == "__main__":
    unittest.main()

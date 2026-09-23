import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import convergence  # noqa: E402
import footer_latch  # noqa: E402
import canopus_task  # noqa: E402

T0 = datetime(2030, 1, 1, 9, 0, tzinfo=timezone.utc)


def envelope(**overrides):
    data = {
        "task_ref": "DEMO-7",
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


class IsolatedStateTest(unittest.TestCase):
    """Every test gets a temporary HOME and state directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.state = self.tmp / "state"
        patcher = mock.patch.dict(os.environ, {"HOME": str(self.tmp / "home"),
                                               "CANOPUS_STATE_DIR": str(self.state)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = canopus_task.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def envelope_file(self, data=None):
        path = self.tmp / "envelope.json"
        path.write_text(json.dumps(data or envelope()), encoding="utf-8")
        return str(path)


class AdmissionTests(IsolatedStateTest):
    def test_admit_creates_record_under_state_dir(self):
        result, record = canopus_task.admit("t1", envelope(), now=T0)
        self.assertEqual(result, "admitted")
        self.assertTrue((self.state / "tasks" / "t1.json").is_file())
        self.assertEqual(record["admitted_at"], "2030-01-01T09:00:00Z")
        self.assertIsNone(record["closed_at"])

    def test_admit_is_idempotent_and_keeps_original_timestamp(self):
        canopus_task.admit("t1", envelope(), now=T0)
        result, record = canopus_task.admit("t1", envelope(), now=T0 + timedelta(hours=2))
        self.assertEqual(result, "resumed")
        self.assertEqual(record["admitted_at"], "2030-01-01T09:00:00Z")

    def test_changed_envelope_requires_readmit(self):
        canopus_task.admit("t1", envelope())
        with self.assertRaises(canopus_task.TaskError):
            canopus_task.admit("t1", envelope(acceptance=["AC1", "AC2", "AC3"]))

    def test_readmit_archives_round_and_carries_surviving_acceptance(self):
        canopus_task.admit("t1", envelope())
        canopus_task.add_event("t1", {"kind": "accept", "item": "AC1"})
        canopus_task.add_event("t1", {"kind": "accept", "item": "AC2"})
        result, record = canopus_task.admit("t1", envelope(acceptance=["AC1", "AC3"]), readmit=True)
        self.assertEqual(result, "readmitted")
        self.assertEqual(len(record["rounds"]), 1)
        state = canopus_task.replay(canopus_task.load("t1"))
        self.assertEqual(state.accepted, ["AC1"])
        self.assertEqual(state.state, "HEALTHY")

    def test_invalid_envelope_writes_nothing(self):
        with self.assertRaises(convergence.ConvergenceError):
            canopus_task.admit("t1", envelope(acceptance=[]))
        self.assertFalse((self.state / "tasks" / "t1.json").exists())

    def test_task_id_cannot_escape_state_dir(self):
        for bad in ("../x", "a/b", "", ".hidden", "x" * 65):
            with self.assertRaises(canopus_task.TaskError, msg=bad):
                canopus_task.admit(bad, envelope())

    def test_admit_accepts_scenario_file_shape(self):
        scenario = ROOT / "examples" / "scenarios" / "clean-delivery.json"
        code, out, _ = self.cli("admit", "--task", "demo", "--envelope", str(scenario))
        self.assertEqual(code, 0)
        self.assertIn("admitted demo", out)

    def test_admit_can_latch_session_atomically(self):
        code, out, _ = self.cli("admit", "--task", "t1", "--envelope", self.envelope_file(),
                                "--latch-session", "sess-1")
        self.assertEqual(code, 0)
        self.assertEqual(footer_latch.read_latch("sess-1")["tasks"], ["t1"])


class EventTests(IsolatedStateTest):
    def setUp(self):
        super().setUp()
        canopus_task.admit("t1", envelope(), now=T0)

    def test_replay_matches_direct_convergence_run(self):
        events = [{"kind": "accept", "item": "AC1"}, {"kind": "checkpoint"},
                  {"kind": "finding", "summary": "later", "in_scope": False}]
        for event in events:
            canopus_task.add_event("t1", event)
        direct = convergence.run(envelope(), events)
        stored = canopus_task.replay(canopus_task.load("t1"))
        self.assertEqual(convergence.render_agent(stored), convergence.render_agent(direct))

    def test_unknown_event_is_rejected_and_not_stored(self):
        with self.assertRaises(canopus_task.TaskError):
            canopus_task.add_event("t1", {"kind": "celebrate"})
        self.assertEqual(canopus_task.load("t1")["events"], [])

    def test_event_missing_required_field_is_rejected(self):
        with self.assertRaises(canopus_task.TaskError):
            canopus_task.add_event("t1", {"kind": "accept"})
        self.assertEqual(canopus_task.load("t1")["events"], [])

    def test_stopped_task_refuses_more_events(self):
        canopus_task.add_event("t1", {"kind": "blocker", "family": "flaky-ci"})
        state = canopus_task.add_event("t1", {"kind": "blocker", "family": "flaky-ci"})
        self.assertEqual(state.state, "CIRCUIT_BREAK")
        with self.assertRaises(canopus_task.TaskError):
            canopus_task.add_event("t1", {"kind": "activity"})

    def test_checkpoint_note_becomes_next_action(self):
        state = canopus_task.checkpoint("t1", "Write the boundary test.")
        self.assertEqual(state.state, "WATCH")
        self.assertIn("Write the boundary test.", canopus_task.handoff("t1"))

    def test_cli_rejects_invalid_json(self):
        code, _, err = self.cli("event", "--task", "t1", "--json", "{not json")
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)

    def test_unadmitted_task_is_an_error(self):
        code, _, err = self.cli("event", "--task", "nope", "--json", '{"kind": "activity"}')
        self.assertEqual(code, 2)
        self.assertIn("not admitted", err)


class RenderingTests(IsolatedStateTest):
    def setUp(self):
        super().setUp()
        canopus_task.admit("t1", envelope(), now=T0)

    def test_footer_keeps_decision_row_last_and_passes_latch_check(self):
        text = canopus_task.footer("t1", now=T0 + timedelta(minutes=95))
        lines = text.splitlines()
        self.assertTrue(lines[0].startswith("Canopus · DEMO-7"))
        self.assertTrue(lines[-1].startswith("Decision │"))
        self.assertIn("Elapsed │ 1h 35m", text)
        self.assertTrue(footer_latch.footer_is_final_block("Done.\n\n" + text)[0])

    def test_zh_tw_footer(self):
        text = canopus_task.footer("t1", "zh-TW", now=T0 + timedelta(seconds=75))
        self.assertIn("耗時 │ 1m 15s", text)
        self.assertTrue(text.splitlines()[-1].startswith("決策 │"))
        self.assertTrue(footer_latch.footer_is_final_block(text)[0])

    def test_handoff_includes_resume_instruction(self):
        text = canopus_task.handoff("t1", now=T0)
        self.assertTrue(text.startswith("CANOPUS AGENT HANDOFF"))
        self.assertIn("Resume: python3 tools/canopus_task.py status --task t1", text)

    def test_status_lists_tasks_and_json(self):
        canopus_task.admit("t2", envelope(task_ref="DEMO-8"))
        code, out, _ = self.cli("status")
        self.assertEqual(code, 0)
        self.assertIn("t1", out)
        self.assertIn("t2", out)
        code, out, _ = self.cli("status", "--task", "t1", "--json")
        self.assertEqual(json.loads(out)["remaining"], ["AC1", "AC2"])

    def test_status_with_no_tasks(self):
        (self.state / "tasks" / "t1.json").unlink()
        code, out, _ = self.cli("status")
        self.assertEqual((code, out.strip()), (0, "no admitted tasks"))


class CloseAndRecoveryTests(IsolatedStateTest):
    def setUp(self):
        super().setUp()
        canopus_task.admit("t1", envelope(), now=T0)

    def test_complete_requires_convergence_complete(self):
        with self.assertRaises(canopus_task.TaskError):
            canopus_task.close("t1", "complete")
        canopus_task.add_event("t1", {"kind": "accept", "item": "AC1"})
        canopus_task.add_event("t1", {"kind": "accept", "item": "AC2"})
        record = canopus_task.close("t1", "complete", now=T0 + timedelta(minutes=30))
        self.assertEqual(record["closed_at"], "2030-01-01T09:30:00Z")
        self.assertEqual(canopus_task.elapsed_seconds(record, now=T0 + timedelta(days=9)), 1800)

    def test_close_is_idempotent_but_not_rewritable(self):
        canopus_task.close("t1", "handoff")
        self.assertEqual(canopus_task.close("t1", "handoff")["outcome"], "handoff")
        with self.assertRaises(canopus_task.TaskError):
            canopus_task.close("t1", "abandoned")

    def test_closed_task_rejects_events_and_plain_admit(self):
        canopus_task.close("t1", "blocked")
        with self.assertRaises(canopus_task.TaskError):
            canopus_task.add_event("t1", {"kind": "activity"})
        with self.assertRaises(canopus_task.TaskError):
            canopus_task.admit("t1", envelope())
        self.assertIn("Closed │ blocked", canopus_task.footer("t1"))

    def test_corrupt_record_is_reported_not_overwritten(self):
        path = self.state / "tasks" / "t1.json"
        path.write_text("{truncated", encoding="utf-8")
        code, _, err = self.cli("footer", "--task", "t1")
        self.assertEqual(code, 2)
        self.assertIn("corrupt", err)
        with self.assertRaises(canopus_task.TaskError):
            canopus_task.admit("t1", envelope())
        self.assertEqual(path.read_text(encoding="utf-8"), "{truncated")

    def test_leftover_temporary_file_does_not_break_resume(self):
        (self.state / "tasks" / "t1.json.tmp").write_text("partial", encoding="utf-8")
        self.assertEqual(canopus_task.admit("t1", envelope())[0], "resumed")
        self.assertEqual(canopus_task.list_tasks(), ["t1"])

    def test_default_state_dir_is_under_home(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CANOPUS_STATE_DIR")
            self.assertEqual(canopus_task.state_dir(), self.tmp / "home" / ".canopus" / "state")


if __name__ == "__main__":
    unittest.main()

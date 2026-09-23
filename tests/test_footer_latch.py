import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import footer_latch  # noqa: E402

FOOTER = "\n".join([
    "Canopus · DEMO-7",
    "─" * 20,
    "Goal │ Synthetic goal",
    "Progress │ ■■■■■□□□□□ 1 / 2",
    "Next │ Write the boundary test.",
    "Decision │ CONTINUE",
])
ZH_FOOTER = "Canopus · DEMO-7\n主線 │ 目標\n決策 │ 繼續"


class LatchTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.env = {"HOME": str(self.tmp / "home"), "CANOPUS_STATE_DIR": str(self.tmp / "state")}
        patcher = mock.patch.dict(os.environ, self.env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)

    def run_hook(self, command, payload):
        """Run the real CLI as Claude Code would: JSON on stdin."""
        stdin = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run([sys.executable, str(ROOT / "tools" / "footer_latch.py"), command],
                              input=stdin, capture_output=True, text=True,
                              env={**os.environ, **self.env}, check=False)


class FooterDetectionTests(unittest.TestCase):
    def check(self, text):
        return footer_latch.footer_is_final_block(text)[0]

    def test_footer_as_final_block_passes(self):
        self.assertTrue(self.check("Implemented the export.\n\n" + FOOTER))
        self.assertTrue(self.check(ZH_FOOTER + "\n\n"))

    def test_fenced_footer_passes(self):
        self.assertTrue(self.check("Summary.\n\n```text\n" + FOOTER + "\n```\n"))

    def test_text_after_footer_fails(self):
        self.assertFalse(self.check(FOOTER + "\n\nLet me know if you need anything else."))

    def test_missing_header_or_decision_fails(self):
        self.assertFalse(self.check(FOOTER.replace("Canopus · ", "Status: ")))
        self.assertFalse(self.check(FOOTER.rsplit("\n", 1)[0]))
        self.assertFalse(self.check("Canopus · DEMO-7\nDecision │"))

    def test_blank_line_inside_block_breaks_it(self):
        broken = FOOTER.replace("Next │", "\nNext │")
        self.assertFalse(self.check(broken))

    def test_empty_and_none(self):
        self.assertFalse(self.check(""))
        self.assertFalse(self.check(None))
        self.assertFalse(self.check("```\n```"))

    def test_bare_header_prefix_is_not_enough(self):
        self.assertFalse(self.check("Canopus · \nDecision │ CONTINUE"))


class LatchStateTests(LatchTestCase):
    def test_set_is_one_way_and_idempotent(self):
        first = footer_latch.set_latch("s1", "t1")
        again = footer_latch.set_latch("s1", "t1")
        self.assertEqual(first["set_at"], again["set_at"])
        self.assertEqual(again["tasks"], ["t1"])
        self.assertEqual(footer_latch.set_latch("s1", "t2")["tasks"], ["t1", "t2"])
        self.assertTrue((self.tmp / "state" / "latches" / "s1.json").is_file())

    def test_invalid_session_ids_are_rejected(self):
        for bad in ("../escape", "a/b", "", ".x"):
            with self.assertRaises(footer_latch.LatchError):
                footer_latch.set_latch(bad, "t1")

    def test_corrupt_latch_still_counts_as_latched(self):
        path = self.tmp / "state" / "latches" / "s1.json"
        path.parent.mkdir(parents=True)
        path.write_text("{oops", encoding="utf-8")
        self.assertIsNotNone(footer_latch.read_latch("s1"))
        decision = footer_latch.handle_stop({"session_id": "s1", "last_assistant_message": "hi"})
        self.assertEqual(decision["decision"], "block")
        self.assertEqual(footer_latch.set_latch("s1", "t1")["tasks"], ["t1"])  # recovery

    def test_set_cli_uses_environment_session(self):
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"CANOPUS_SESSION_ID": "env-session"}), redirect_stdout(out):
            code = footer_latch.main(["set", "--task", "t9"])
        self.assertEqual(code, 0)
        self.assertEqual(footer_latch.read_latch("env-session")["tasks"], ["t9"])

    def test_set_cli_without_session_fails(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CANOPUS_SESSION_ID", None)
            with redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
                self.assertEqual(footer_latch.main(["set", "--task", "t1"]), 2)


class StopHookTests(LatchTestCase):
    def test_unlatched_session_is_never_blocked(self):
        result = self.run_hook("stop", {"session_id": "chat", "last_assistant_message": "hello"})
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_latched_session_without_footer_is_blocked(self):
        footer_latch.set_latch("s1", "t1")
        result = self.run_hook("stop", {"session_id": "s1", "stop_hook_active": False,
                                        "last_assistant_message": "All done!"})
        self.assertEqual(result.returncode, 0)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("t1", decision["reason"])

    def test_latched_session_with_footer_passes(self):
        footer_latch.set_latch("s1", "t1")
        result = self.run_hook("stop", {"session_id": "s1", "last_assistant_message": "Done.\n\n" + FOOTER})
        self.assertEqual(result.stdout, "")

    def test_never_blocks_twice_in_one_turn(self):
        footer_latch.set_latch("s1", "t1")
        result = self.run_hook("stop", {"session_id": "s1", "stop_hook_active": True,
                                        "last_assistant_message": "still no footer"})
        self.assertEqual(result.stdout, "")

    def test_payload_message_wins_over_stale_transcript(self):
        footer_latch.set_latch("s1", "t1")
        transcript = self.tmp / "t.jsonl"
        transcript.write_text(json.dumps({"type": "assistant", "message": {
            "role": "assistant", "content": [{"type": "text", "text": "stale, no footer"}]}}) + "\n")
        decision = footer_latch.handle_stop({"session_id": "s1", "transcript_path": str(transcript),
                                             "last_assistant_message": FOOTER})
        self.assertIsNone(decision)

    def test_transcript_fallback_when_message_absent(self):
        footer_latch.set_latch("s1", "t1")
        transcript = self.tmp / "t.jsonl"
        lines = [
            {"type": "user", "message": {"role": "user", "content": "go"}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Bash"}]}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "Done."}, {"type": "text", "text": FOOTER}]}},
            {"type": "system", "subtype": "noise"},
        ]
        transcript.write_text("\n".join(json.dumps(line) for line in lines) + "\nnot json\n")
        self.assertIsNone(footer_latch.handle_stop({"session_id": "s1", "transcript_path": str(transcript)}))
        transcript.write_text(json.dumps(lines[1]) + "\n" + json.dumps(
            {"message": {"role": "assistant", "content": "plain text reply"}}) + "\n")
        self.assertIsNotNone(footer_latch.handle_stop({"session_id": "s1", "transcript_path": str(transcript)}))

    def test_missing_transcript_fails_closed_for_latched_session(self):
        footer_latch.set_latch("s1", "t1")
        decision = footer_latch.handle_stop({"session_id": "s1", "transcript_path": str(self.tmp / "nope")})
        self.assertEqual(decision["decision"], "block")

    def test_malformed_payloads_fail_open(self):
        footer_latch.set_latch("s1", "t1")
        for payload in ("{not json", "", "[1, 2]", json.dumps({"session_id": "../bad"})):
            result = self.run_hook("stop", payload)
            self.assertEqual((result.returncode, result.stdout), (0, ""), payload)


class SessionStartTests(LatchTestCase):
    def test_session_start_tells_the_agent_its_session_id(self):
        result = self.run_hook("session-start", {"session_id": "abc-123"})
        self.assertEqual(result.returncode, 0)
        self.assertIn("abc-123", result.stdout)
        self.assertIn("--latch-session abc-123", result.stdout)

    def test_session_start_ignores_missing_or_invalid_ids(self):
        for payload in ({}, {"session_id": "../escape"}, "not json"):
            result = self.run_hook("session-start", payload)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")


class SessionEndTests(LatchTestCase):
    def test_end_clears_latch_from_hook_payload(self):
        footer_latch.set_latch("s1", "t1")
        result = self.run_hook("end", {"session_id": "s1", "reason": "exit"})
        self.assertEqual(result.returncode, 0)
        self.assertIsNone(footer_latch.read_latch("s1"))
        after = self.run_hook("stop", {"session_id": "s1", "last_assistant_message": "hi"})
        self.assertEqual(after.stdout, "")

    def test_end_never_fails(self):
        for payload in ("", "{bad", json.dumps({"session_id": "../x"}), json.dumps({"session_id": "gone"})):
            self.assertEqual(self.run_hook("end", payload).returncode, 0)

    def test_status_reports_latches(self):
        out = io.StringIO()
        with redirect_stdout(out):
            footer_latch.main(["status"])
        self.assertIn("no latched sessions", out.getvalue())
        footer_latch.set_latch("s1", "t1")
        out = io.StringIO()
        with redirect_stdout(out):
            footer_latch.main(["status"])
        self.assertIn("s1: MANAGED_TASK t1", out.getvalue())


if __name__ == "__main__":
    unittest.main()

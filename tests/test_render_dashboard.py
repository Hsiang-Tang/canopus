import io
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.request
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import canopus_task  # noqa: E402
import convergence  # noqa: E402
import render_dashboard  # noqa: E402

SCENARIOS = ROOT / "examples" / "scenarios"
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


class ScenarioDashboardTest(unittest.TestCase):
    def test_all_scenarios_render_with_final_state_and_progress(self):
        page = render_dashboard.render(render_dashboard.records_from_scenarios(SCENARIOS))
        for path in sorted(SCENARIOS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            state = convergence.run(data["envelope"], data["events"])
            self.assertIn(data["envelope"]["task_ref"], page)
            self.assertIn(f">{state.state}</span></h2>", page)
            total = len(data["envelope"]["acceptance"])
            self.assertIn(f"{len(state.accepted)} / {total} accepted", page)

    def test_timeline_has_one_row_per_event_with_state_after(self):
        record = render_dashboard.records_from_scenarios(SCENARIOS)[0]
        rows = render_dashboard.timeline(record)
        self.assertEqual(len(rows), len(record["events"]))
        self.assertEqual(rows[-1][2], canopus_task.replay(record).state)
        page = render_dashboard.render_task(record)
        self.assertEqual(page.count('<td class="num">'), len(record["events"]))

    def test_render_is_deterministic(self):
        records = render_dashboard.records_from_scenarios(SCENARIOS)
        self.assertEqual(render_dashboard.render(records), render_dashboard.render(records))
        self.assertNotIn("generated", render_dashboard.render(records))
        self.assertIn("generated 2030-01-01", render_dashboard.render(records, generated_at="2030-01-01"))

    def test_page_is_self_contained_and_escaped(self):
        record = {"task_id": "x", "title": "", "envelope": envelope(north_star="<script>alert(1)</script>"),
                  "events": [{"at": None, "event": {"kind": "checkpoint", "note": "<b>bold</b>"}}],
                  "admitted_at": None, "closed_at": None, "outcome": None}
        page = render_dashboard.render([record])
        self.assertNotIn("<script", page)
        self.assertNotIn("<b>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)

    def test_sample_page_matches_scenarios(self):
        sample = ROOT / "docs" / "assets" / "dashboard-sample.html"
        expected = render_dashboard.render(render_dashboard.records_from_scenarios(SCENARIOS),
                                           title="Canopus tasks: synthetic scenarios")
        self.assertEqual(sample.read_text(encoding="utf-8"), expected)


class StateDashboardTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        patcher = mock.patch.dict(os.environ, {"CANOPUS_STATE_DIR": str(self.root)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.temp.cleanup)

    def test_admitted_task_matches_summary(self):
        canopus_task.admit("demo-7", envelope(), now=T0)
        canopus_task.add_event("demo-7", {"kind": "accept", "item": "AC1"}, now=T0)
        summary = canopus_task.summary("demo-7", now=T0)
        page = render_dashboard.render(render_dashboard.records_from_state())
        self.assertIn(f">{summary['state']}</span></h2>", page)
        self.assertIn(f"{summary['accepted']} / {summary['total']} accepted", page)
        self.assertIn("2030-01-01T09:00:00Z", page)

    def test_cli_writes_out_file(self):
        canopus_task.admit("demo-7", envelope(), now=T0)
        out = self.root / "page.html"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(render_dashboard.main(["--out", str(out)]), 0)
        self.assertIn("DEMO-7", out.read_text(encoding="utf-8"))

    def test_empty_state_renders(self):
        self.assertIn("No tasks.", render_dashboard.render(render_dashboard.records_from_state()))


class ServeTest(unittest.TestCase):
    def test_serve_answers_get_root(self):
        server = render_dashboard.make_server(lambda: "<!DOCTYPE html><p>live</p>", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.assertEqual(server.server_address[0], "127.0.0.1")
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_address[1]}/") as response:
            self.assertEqual(response.status, 200)
            self.assertIn("live", response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()

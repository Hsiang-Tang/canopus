import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import model_route  # noqa: E402

CATALOG = model_route.load_catalog()


def route(task_class, risk, needs=None, evidence=None):
    return model_route.route(CATALOG, task_class, risk, needs, evidence)


class ShippedCatalogTests(unittest.TestCase):
    def test_catalog_is_synthetic_and_valid(self):
        tiers = [tier["id"] for tier in CATALOG["tier"]]
        self.assertEqual(tiers, ["deterministic", "fast", "balanced", "frontier"])
        text = (ROOT / "routing" / "catalog.toml").read_text(encoding="utf-8").lower()
        for vendor_term in ("usd", "$", "price per", "gpt", "opus", "sonnet", "gemini"):
            self.assertNotIn(vendor_term, text)

    def test_cheapest_adequate_tier_wins(self):
        self.assertEqual(route("implementation", "R1")["recommendation"], "fast")
        self.assertEqual(route("implementation", "R2")["recommendation"], "balanced")
        self.assertEqual(route("architecture", "R0")["recommendation"], "frontier")

    def test_mechanical_work_prefers_a_deterministic_tool_at_any_risk(self):
        for risk in model_route.RISKS:
            self.assertEqual(route("mechanical", risk)["recommendation"], "deterministic", risk)

    def test_risk_floor_boundary(self):
        r1 = route("implementation", "R1")
        r2 = route("implementation", "R2")
        self.assertEqual((r1["required_capability"], r2["required_capability"]), (1, 2))
        rejected = {v["tier"]: v["reasons"] for v in r2["rejected"]}
        self.assertIn("max risk R1 < R2", rejected["fast"])

    def test_needs_filter_tiers(self):
        result = route("implementation", "R1", ["vision"])
        self.assertEqual(result["recommendation"], "frontier")
        self.assertIsNone(result["escalate_to"])

    def test_escalation_names_next_more_capable_tier(self):
        self.assertEqual(route("implementation", "R1")["escalate_to"], "balanced")

    def test_unsatisfiable_need_recommends_nothing(self):
        result = route("implementation", "R1", ["time-travel"])
        self.assertIsNone(result["recommendation"])
        self.assertEqual(result["ranked"], [])

    def test_output_is_recommendation_only(self):
        self.assertIn("nothing was launched", route("review", "R2")["note"])


class EvidenceTests(unittest.TestCase):
    def outcomes(self, tier, passes, fails, task_class="implementation"):
        return ([{"tier": tier, "task_class": task_class, "outcome": "pass"}] * passes
                + [{"tier": tier, "task_class": task_class, "outcome": "fail"}] * fails)

    def test_poor_evidence_disqualifies_a_tier(self):
        result = route("implementation", "R1", evidence=self.outcomes("fast", 1, 3))
        self.assertEqual(result["recommendation"], "balanced")
        rejected = {v["tier"]: v["reasons"] for v in result["rejected"]}
        self.assertIn("evidence 1/4 passes for implementation", rejected["fast"])

    def test_too_few_samples_do_not_disqualify(self):
        result = route("implementation", "R1", evidence=self.outcomes("fast", 0, 2))
        self.assertEqual(result["recommendation"], "fast")

    def test_exactly_half_passes_is_kept(self):
        result = route("implementation", "R1", evidence=self.outcomes("fast", 2, 2))
        self.assertEqual(result["recommendation"], "fast")

    def test_evidence_for_other_task_class_is_ignored(self):
        result = route("implementation", "R1", evidence=self.outcomes("fast", 0, 9, "review"))
        self.assertEqual(result["recommendation"], "fast")

    def test_bad_outcome_value_is_rejected(self):
        with self.assertRaises(model_route.RouteError):
            route("implementation", "R1", evidence=[{"tier": "fast", "task_class": "implementation",
                                                     "outcome": "meh"}])


class CatalogValidationTests(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.toml"
            path.write_text(text, encoding="utf-8")
            return model_route.load_catalog(path)

    BASE = ('version = 1\n[risk_floor]\nR0 = 0\nR1 = 1\nR2 = 2\nR3 = 3\n'
            '[task_class.implementation]\nmin_capability = 1\n')
    TIER = '[[tier]]\nid = "x"\ncapability = 1\nrelative_cost = 1\nmax_risk = "R1"\n'

    def test_minimal_catalog_loads(self):
        self.assertEqual(self.load(self.BASE + self.TIER)["tier"][0]["id"], "x")

    def test_invalid_catalogs_are_rejected(self):
        broken = [
            self.BASE.replace("version = 1", "version = 2") + self.TIER,
            self.BASE,
            self.BASE + self.TIER + self.TIER,
            self.BASE + self.TIER.replace('"R1"', '"R9"'),
            self.BASE + self.TIER.replace("capability = 1", 'capability = "high"'),
            self.BASE + self.TIER + 'task_classes = ["nonexistent"]\n',
            self.BASE.replace("R3 = 3\n", "") + self.TIER,
            "not = [valid",
        ]
        for text in broken:
            with self.assertRaises(model_route.RouteError, msg=text):
                self.load(text)

    def test_unknown_task_class_and_risk(self):
        with self.assertRaises(model_route.RouteError):
            route("poetry", "R1")
        with self.assertRaises(model_route.RouteError):
            route("implementation", "R7")


class CommandLineTests(unittest.TestCase):
    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = model_route.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_text_and_json_output(self):
        code, out, _ = self.cli("--task-class", "implementation", "--risk", "R2")
        self.assertEqual(code, 0)
        self.assertIn("recommend: balanced", out)
        code, out, _ = self.cli("--task-class", "implementation", "--risk", "R2", "--json")
        self.assertEqual(json.loads(out)["recommendation"], "balanced")

    def test_no_eligible_tier_exits_1(self):
        code, out, _ = self.cli("--task-class", "implementation", "--risk", "R1", "--need", "time-travel")
        self.assertEqual(code, 1)
        self.assertIn("none eligible", out)

    def test_evidence_file_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.json"
            path.write_text('{"not": "a list"}', encoding="utf-8")
            code, _, err = self.cli("--task-class", "review", "--risk", "R1", "--evidence", str(path))
            self.assertEqual(code, 2)
            self.assertIn("JSON list", err)


if __name__ == "__main__":
    unittest.main()

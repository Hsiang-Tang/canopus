import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_knowledge_candidate as ck  # noqa: E402

TEMPLATE = """# Portable knowledge candidate

## Generic problem

Describe the recurring problem without identifying its source.

## Reusable lesson

State the abstract technique or decision rule.

## Boundary confirmation

- [ ] No identifiers.
- [ ] Reviewed by the owner.
"""

GOOD = """# Retry budgets beat retry loops

## Generic problem

Flaky integration tests get retried until they pass, hiding real defects.

## Reusable lesson

Give each test job a fixed retry budget and record every retry as a finding.
See https://docs.example.com/retries and ask {ops}; staging is 192.0.2.10.
Hash with SHA-256 and store timestamps as ISO-8601.

## Boundary confirmation

- [x] No identifiers.
- [X] Reviewed by the owner.
""".format(ops="ops" + "@example.org")


def screen(text, template=TEMPLATE, terms=None):
    return ck.screen(text, template, terms)


class StructureTests(unittest.TestCase):
    def test_clean_candidate_passes(self):
        self.assertEqual(screen(GOOD), [])

    def test_missing_and_empty_sections(self):
        text = GOOD.replace("## Reusable lesson", "## Something else")
        self.assertIn("missing section '## Reusable lesson'", screen(text))
        empty = GOOD.split("## Reusable lesson")[0] + "## Reusable lesson\n\n## Boundary confirmation\n\n- [x] ok\n"
        self.assertIn("section '## Reusable lesson' is empty", screen(empty))

    def test_untouched_template_guidance_is_rejected(self):
        problems = screen(TEMPLATE)
        self.assertIn("section '## Generic problem' still holds the template guidance text", problems)
        self.assertEqual(sum("unticked boundary check" in p for p in problems), 2)

    def test_unticked_checkbox_is_rejected(self):
        problems = screen(GOOD.replace("- [x] No identifiers.", "- [ ] No identifiers."))
        self.assertEqual(problems, ["unticked boundary check in '## Boundary confirmation': No identifiers."])

    def test_placeholders_are_rejected(self):
        for marker in ("TODO", "TBD", "<describe the fix>"):
            self.assertIn("unfilled placeholder (TODO, TBD, or <...>)", screen(GOOD + f"\n{marker}\n"), marker)

    def test_default_sections_without_template(self):
        problems = ck.screen(GOOD, None)
        self.assertIn("missing section '## Applies when'", problems)
        self.assertNotIn("missing section '## Generic problem'", problems)

    def test_default_sections_match_shipped_template_when_present(self):
        template = ROOT / "templates" / "portable-knowledge-candidate.md"
        if not template.is_file():
            self.skipTest("template not present in this checkout")
        text = template.read_text(encoding="utf-8")
        self.assertTrue(ck.sections(text))
        self.assertTrue(ck.screen(text, text), "an unfilled template must never pass")


class DenylistTests(unittest.TestCase):
    def hits(self, line):
        return [p for p in ck.denylist_findings(line, []) if p.startswith("line 1:")]

    def test_identifiers_are_rejected(self):
        home = "/" + "home/dev/project"
        mac = "/" + "Users/dev/project"
        win = "C:" + "\\" + "Users\\dev\\project"
        cases = {
            "URL": "see https://wiki.internal.test/page",
            "SSH remote": "clone " + "git" + "@git.internal.test:team/repo.git",
            "email address": "mail " + "dev" + "@corp.test",
            "IPv4 address": "host 10.1.2.3",
            "Windows path": "open " + win,
            "home path": "open " + home,
            "ticket id": "fixed in PROJ-123",
            "issue reference": "fixed in " + "#" + "42",
            "private key": "-----BEGIN RSA " + "PRIVATE KEY-----",
            "token": "token " + "ghp_" + "a" * 30,
        }
        for label, line in cases.items():
            self.assertIn(f"line 1: {label}", self.hits(line), label)
        self.assertIn("line 1: home path", self.hits("`" + mac + "`"))

    def test_documentation_reserved_values_pass(self):
        for line in ("https://api.example.com/v1", "you" + "@example.com", "http://build.invalid/x",
                     "git" + "@git.example:org/repo", "203.0.113.7", "SHA-256 and UTF-8",
                     "use ~/.config for settings", "heading & #anchor", "HTTP-2 push"):
            self.assertEqual(self.hits(line), [], line)

    def test_example_lookalike_domains_are_rejected(self):
        self.assertTrue(self.hits("https://example.com.attacker.test/"))
        self.assertTrue(self.hits("https://notexample.com/"))

    def test_denied_terms_are_case_insensitive_with_line_numbers(self):
        problems = ck.denylist_findings("fine\nWe used AcmeCorp tooling\n", ["acmecorp", " "])
        self.assertEqual(problems, ["line 2: denied term 'acmecorp'"])


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.template = self.tmp / "template.md"
        self.template.write_text(TEMPLATE, encoding="utf-8")

    def cli(self, text, *argv):
        candidate = self.tmp / "candidate.md"
        candidate.write_text(text, encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = ck.main([str(candidate), "--template", str(self.template), *argv])
        return code, out.getvalue(), err.getvalue()

    def test_pass_still_requires_human_review(self):
        code, out, _ = self.cli(GOOD)
        self.assertEqual(code, 0)
        self.assertIn("human ownership and disclosure review still required", out)

    def test_reject_exit_code(self):
        code, out, _ = self.cli(GOOD, "--deny", "retry budget")
        self.assertEqual(code, 1)
        self.assertIn("REJECT line 1: denied term 'retry budget'", out)

    def test_deny_file_ignores_comments_and_blanks(self):
        terms = self.tmp / "terms.txt"
        terms.write_text("# local only\n\nflaky\n", encoding="utf-8")
        code, out, _ = self.cli(GOOD, "--deny-file", str(terms))
        self.assertEqual(code, 1)
        self.assertEqual(out.count("denied term 'flaky'"), 1)

    def test_unreadable_input(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = ck.main([str(self.tmp / "missing.md")])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

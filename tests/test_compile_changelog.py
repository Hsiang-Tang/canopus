import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import compile_changelog as cc  # noqa: E402


class ChangelogTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.fragments = self.root / "changelog.d"
        self.fragments.mkdir()
        (self.fragments / "README.md").write_text("# Fragments\n", encoding="utf-8")
        self.changelog = self.root / "CHANGELOG.md"
        self.addCleanup(self._tmp.cleanup)

    def fragment(self, name, text):
        (self.fragments / name).write_text(text, encoding="utf-8")

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cc.main(["--root", str(self.root), *argv])
        return code, out.getvalue(), err.getvalue()

    def remaining(self):
        return sorted(p.name for p in self.fragments.iterdir())


class CompileTests(ChangelogTest):
    def test_creates_changelog_when_missing(self):
        self.fragment("csv.added.md", "- Export reports as CSV.\n")
        code, out, _ = self.cli()
        self.assertEqual(code, 0)
        self.assertEqual(self.changelog.read_text(encoding="utf-8"),
                         "# Changelog\n\n## Unreleased\n\n### Added\n\n- Export reports as CSV.\n")
        self.assertEqual(self.remaining(), ["README.md"])

    def test_appends_into_existing_subsection_and_keeps_releases(self):
        self.changelog.write_text(
            "# Changelog\n\n## Unreleased\n\n### Added\n\n- Earlier item.\n\n## 1.0.0\n\n- First release.\n",
            encoding="utf-8")
        self.fragment("b-second.added.md", "- Second item.\n")
        self.fragment("a-first.added.md", "- First item\n  wrapped onto two lines.\n")
        self.fragment("bug.fixed.md", "- Fixed the empty-week export.\n")
        self.cli()
        self.assertEqual(self.changelog.read_text(encoding="utf-8"), (
            "# Changelog\n\n## Unreleased\n\n### Added\n\n- Earlier item.\n- First item\n"
            "  wrapped onto two lines.\n- Second item.\n\n### Fixed\n\n- Fixed the empty-week export.\n\n"
            "## 1.0.0\n\n- First release.\n"))

    def test_inserts_unreleased_above_latest_release(self):
        self.changelog.write_text("# Changelog\n\n## 1.0.0\n\n- First release.\n", encoding="utf-8")
        self.fragment("x.security.md", "- Rotate the signing key on install.\n")
        self.cli()
        self.assertEqual(self.changelog.read_text(encoding="utf-8"), (
            "# Changelog\n\n## Unreleased\n\n### Security\n\n- Rotate the signing key on install.\n\n"
            "## 1.0.0\n\n- First release.\n"))

    def test_no_fragments_is_a_no_op(self):
        self.changelog.write_text("# Changelog\n", encoding="utf-8")
        code, out, _ = self.cli()
        self.assertEqual((code, out.strip()), (0, "no pending changelog fragments"))
        self.assertEqual(self.changelog.read_text(encoding="utf-8"), "# Changelog\n")

    def test_missing_fragment_directory_is_a_no_op(self):
        (self.fragments / "README.md").unlink()
        self.fragments.rmdir()
        self.assertEqual(self.cli()[0], 0)

    def test_dry_run_changes_nothing(self):
        self.fragment("csv.added.md", "- Export reports as CSV.\n")
        code, out, _ = self.cli("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("- Export reports as CSV.", out)
        self.assertFalse(self.changelog.exists())
        self.assertIn("csv.added.md", self.remaining())

    def test_check_reports_pending(self):
        self.assertEqual(self.cli("--check")[0], 0)
        self.fragment("csv.added.md", "- Export reports as CSV.\n")
        self.assertEqual(self.cli("--check")[0], 1)


class ValidationTests(ChangelogTest):
    def test_bad_fragment_blocks_everything(self):
        self.changelog.write_text("# Changelog\n", encoding="utf-8")
        self.fragment("good.added.md", "- Fine.\n")
        self.fragment("bad.added.md", "Not a bullet.\n")
        code, _, err = self.cli()
        self.assertEqual(code, 2)
        self.assertIn("bad.added.md", err)
        self.assertEqual(self.changelog.read_text(encoding="utf-8"), "# Changelog\n")
        self.assertEqual(self.remaining(), ["README.md", "bad.added.md", "good.added.md"])

    def test_fragment_name_rules(self):
        for name in ("nocategory.md", "x.improved.md", ".added.md", "a.b.added.md"):
            with self.subTest(name=name):
                path = self.fragments / name
                path.write_text("- ok\n", encoding="utf-8")
                with self.assertRaises(cc.FragmentError):
                    cc.parse_fragment(path)
                path.unlink()

    def test_fragment_content_rules(self):
        for text in ("", "\n\n", "- ok\n## Heading\n", "- ok\nunindented continuation\n"):
            with self.subTest(text=text):
                self.fragment("x.changed.md", text)
                with self.assertRaises(cc.FragmentError):
                    cc.parse_fragment(self.fragments / "x.changed.md")

    def test_check_also_validates(self):
        self.fragment("bad.md", "- no category\n")
        self.assertEqual(self.cli("--check")[0], 2)


if __name__ == "__main__":
    unittest.main()

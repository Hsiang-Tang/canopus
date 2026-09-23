import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import workstream  # noqa: E402


def declaration(ws_id, **overrides):
    data = {
        "id": ws_id, "owner_role": "executor", "writer": f"agent-{ws_id}", "status": "active",
        "branch": f"ws/{ws_id}", "worktree": f"../wt-{ws_id}",
        "mutation_scope": [f"src/{ws_id}/**"], "depends_on": [],
    }
    data.update(overrides)
    return data


def to_toml(data):
    lines = []
    for key, value in data.items():
        lines.append(f"{key} = {json.dumps(value)}")
    return "\n".join(lines) + "\n"


class WorkstreamDirTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name) / "workstreams"
        self.dir.mkdir()
        self.addCleanup(self._tmp.cleanup)

    def write(self, *declarations):
        for data in declarations:
            (self.dir / f"{data['id']}.toml").write_text(to_toml(data), encoding="utf-8")

    def errors(self):
        streams, errors = workstream.load(self.dir)
        return errors + workstream.check(streams)

    def cli(self, *argv, stdin=""):
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("sys.stdin", io.StringIO(stdin)):
            code = workstream.main(["--dir", str(self.dir), *argv])
        return code, out.getvalue()


class GlobOverlapTests(unittest.TestCase):
    def test_overlap_cases(self):
        cases = [
            ("src/api/**", "src/api/handlers.py", True),
            ("src/api/**", "src/web/**", False),
            ("src/**", "src/api/**", True),
            ("**/*.md", "docs/guide.md", True),
            ("**/*.md", "src/app.py", False),
            ("docs/*.md", "docs/api/x.md", False),
            ("docs/", "docs/a/b.md", True),
            ("src/*.py", "src/*.txt", True),  # two wildcards: conservatively assumed to meet
            ("README.md", "README.md", True),
            ("README.md", "readme.md", False),
            ("src/api", "src/api/**", True),
            ("./src/x.py", "src/x.py", True),
        ]
        for a, b, expected in cases:
            self.assertEqual(workstream.globs_overlap(a, b), expected, (a, b))
            self.assertEqual(workstream.globs_overlap(b, a), expected, (b, a))


class CheckTests(WorkstreamDirTest):
    def test_shipped_example_is_clean(self):
        streams, errors = workstream.load(ROOT / "examples" / "workstreams")
        self.assertEqual(errors + workstream.check(streams), [])
        self.assertEqual(len(streams), 2)

    def test_independent_workstreams_pass(self):
        self.write(declaration("api"), declaration("web"))
        self.assertEqual(self.errors(), [])

    def test_scope_collision(self):
        self.write(declaration("api"), declaration("shared", mutation_scope=["src/**"]))
        errors = self.errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("scope collision api / shared", errors[0])

    def test_finished_workstreams_do_not_collide(self):
        self.write(declaration("api"), declaration("old", mutation_scope=["src/**"], status="done"))
        self.assertEqual(self.errors(), [])

    def test_shared_branch_and_worktree(self):
        self.write(declaration("a"), declaration("b", branch="ws/a", worktree="../wt-a/"))
        errors = self.errors()
        self.assertTrue(any("shared branch 'ws/a'" in e for e in errors))
        self.assertTrue(any("one-writer violation: worktree" in e for e in errors))

    def test_multiple_writers_is_a_one_writer_violation(self):
        self.write(declaration("a", writer=["agent-x", "agent-y"]))
        self.assertIn("one-writer violation: writer lists 2 names", self.errors()[0])

    def test_dependency_problems(self):
        self.write(declaration("a", depends_on=["ghost"]),
                   declaration("b", depends_on=["dead"]),
                   declaration("dead", status="abandoned"))
        errors = self.errors()
        self.assertIn("a: depends on missing workstream 'ghost'", errors)
        self.assertIn("b: depends on abandoned workstream 'dead'", errors)

    def test_dependency_cycle_reported_once(self):
        self.write(declaration("a", depends_on=["b"]), declaration("b", depends_on=["c"]),
                   declaration("c", depends_on=["a"]), declaration("d", depends_on=["d"]))
        cycles = [e for e in self.errors() if e.startswith("dependency cycle")]
        self.assertEqual(len(cycles), 2)
        self.assertIn("dependency cycle: a -> b -> c -> a", cycles)
        self.assertIn("dependency cycle: d -> d", cycles)

    def test_invalid_declarations(self):
        self.write(declaration("a", status="paused"),
                   declaration("b", mutation_scope=[]),
                   declaration("c", mutation_scope=["../outside/**"]),
                   declaration("d", mutation_scope=["/abs/**"]),
                   declaration("e", branch=""),
                   declaration("f", depends_on="a"))
        del_owner = declaration("g")
        del del_owner["owner_role"]
        self.write(del_owner)
        (self.dir / "broken.toml").write_text("id = [", encoding="utf-8")
        errors = self.errors()
        for fragment in ("a.toml: status", "b.toml: mutation_scope must not be empty",
                         "c.toml: mutation_scope entry", "d.toml: mutation_scope entry",
                         "e.toml: branch", "f.toml: depends_on", "g.toml: owner_role",
                         "broken.toml: invalid TOML"):
            self.assertTrue(any(fragment in e for e in errors), fragment)

    def test_duplicate_ids(self):
        self.write(declaration("a"))
        (self.dir / "copy.toml").write_text(to_toml(declaration("a", branch="ws/other", worktree="../o")))
        self.assertIn("duplicate workstream id 'a'", self.errors())

    def test_missing_directory(self):
        streams, errors = workstream.load(self.dir / "nope")
        self.assertEqual(streams, [])
        self.assertIn("not found", errors[0])


class FilesAndCliTests(WorkstreamDirTest):
    def setUp(self):
        super().setUp()
        self.write(declaration("api", mutation_scope=["src/api/**", "tests/api/"]))

    def test_changed_files_inside_scope(self):
        code, out = self.cli("files", "--id", "api", "src/api/a.py", "tests/api/test_a.py")
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_changed_files_outside_scope_from_stdin(self):
        code, out = self.cli("files", "--id", "api", stdin="src/api/a.py\nREADME.md\n\n")
        self.assertEqual(code, 1)
        self.assertIn("README.md is outside the declared mutation_scope", out)

    def test_unknown_workstream(self):
        self.assertEqual(self.cli("files", "--id", "ghost", "x")[0], 1)

    def test_check_json_and_list(self):
        code, out = self.cli("--json", "check")
        self.assertEqual((code, json.loads(out)["ok"]), (0, True))
        code, out = self.cli("list")
        self.assertIn("api", out)


if __name__ == "__main__":
    unittest.main()

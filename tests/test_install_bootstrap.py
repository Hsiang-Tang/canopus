import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import install_bootstrap as ib  # noqa: E402


class BootstrapTestCase(unittest.TestCase):
    """All tests run against a temporary HOME; the real home is never read or written."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name) / "home"
        self.home.mkdir()
        self.root = Path(self._tmp.name) / "control-plane"
        (self.root / "tools").mkdir(parents=True)
        patcher = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)
        self.claude_md = self.home / ".claude" / "CLAUDE.md"
        self.codex_md = self.home / ".codex" / "AGENTS.md"
        self.settings = self.home / ".claude" / "settings.json"

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = ib.main(["--home", str(self.home), "--root", str(self.root), *argv])
        return code, out.getvalue(), err.getvalue()

    def snapshot(self):
        return {str(p.relative_to(self.home)): p.read_bytes() for p in self.home.rglob("*") if p.is_file()}

    def backups(self):
        return sorted(p.name for p in self.home.rglob("*.canopus-backup-*"))


class MarkdownBlockTests(BootstrapTestCase):
    def test_dry_run_is_default_and_writes_nothing(self):
        self.claude_md.parent.mkdir()
        self.claude_md.write_text("# Mine\n", encoding="utf-8")
        before = self.snapshot()
        code, out, _ = self.cli("--claude-hooks")
        self.assertEqual(code, 0)
        self.assertIn("dry run", out)
        self.assertIn("+" + ib.START, out)
        self.assertEqual(self.snapshot(), before)

    def test_apply_creates_blocks_in_both_files(self):
        code, out, _ = self.cli("--apply")
        self.assertEqual(code, 0)
        for path in (self.claude_md, self.codex_md):
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(ib.START))
            self.assertIn(str(self.root), text)
            self.assertNotIn("{{CANOPUS_ROOT}}", text)
        self.assertEqual(self.backups(), [])  # nothing pre-existed, so nothing to back up

    def test_apply_is_idempotent(self):
        self.cli("--apply", "--claude-hooks")
        before = self.snapshot()
        code, out, _ = self.cli("--apply", "--claude-hooks")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("unchanged"), 3)
        self.assertEqual(self.snapshot(), before)

    def test_existing_content_is_preserved_and_backed_up(self):
        self.claude_md.parent.mkdir()
        original = "# My rules\n\nAlways be kind.\n"
        self.claude_md.write_text(original, encoding="utf-8")
        self.cli("--apply")
        text = self.claude_md.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(original))
        self.assertEqual(len(self.backups()), 1)
        self.assertEqual(next(self.home.rglob("CLAUDE.md.canopus-backup-*")).read_text(encoding="utf-8"), original)

    def test_update_replaces_only_the_block(self):
        self.claude_md.parent.mkdir()
        self.claude_md.write_text(f"top\n\n{ib.START}\nold managed text\n{ib.END}\n\nbottom\n", encoding="utf-8")
        self.cli("--apply")
        text = self.claude_md.read_text(encoding="utf-8")
        self.assertNotIn("old managed text", text)
        self.assertTrue(text.startswith("top\n\n" + ib.START))
        self.assertTrue(text.endswith(ib.END + "\n\nbottom\n"))

    def test_remove_restores_original_bytes(self):
        self.claude_md.parent.mkdir()
        for original in ("# Mine\n", "no trailing newline", ""):
            self.claude_md.write_text(original, encoding="utf-8")
            self.cli("--apply")
            self.cli("--apply", "--remove")
            expected = original if original.endswith("\n") or not original else original + "\n"
            self.assertEqual(self.claude_md.read_text(encoding="utf-8"), expected, repr(original))

    def test_remove_keeps_content_on_both_sides(self):
        self.claude_md.parent.mkdir()
        self.claude_md.write_text(f"top\n\n{ib.START}\nx\n{ib.END}\n\nbottom\n", encoding="utf-8")
        self.cli("--apply", "--remove")
        self.assertEqual(self.claude_md.read_text(encoding="utf-8"), "top\n\nbottom\n")

    def test_malformed_markers_stop_before_any_write(self):
        self.claude_md.parent.mkdir()
        for broken in (f"{ib.START}\nno end\n", f"{ib.END}\n{ib.START}\n", f"{ib.START}\n{ib.END}\n{ib.START}\n{ib.END}\n"):
            self.claude_md.write_text(broken, encoding="utf-8")
            before = self.snapshot()
            code, _, err = self.cli("--apply")
            self.assertEqual(code, 2)
            self.assertIn("malformed", err)
            self.assertEqual(self.snapshot(), before)

    def test_template_is_used_and_its_own_markers_scope_the_block(self):
        (self.root / "templates").mkdir()
        (self.root / "templates" / "global-claude-bootstrap.md").write_text(
            f"# About this template\n\n{ib.START}\nRead {{{{CANOPUS_ROOT}}}}/AGENTS.md first.\n{ib.END}\n",
            encoding="utf-8")
        self.cli("--apply")
        text = self.claude_md.read_text(encoding="utf-8")
        self.assertEqual(text, f"{ib.START}\nRead {self.root.resolve()}/AGENTS.md first.\n{ib.END}\n")
        self.assertIn("One writer per checkout", self.codex_md.read_text(encoding="utf-8"))  # default

    def test_path_overrides_are_home_relative(self):
        self.cli("--apply", "--claude-md", "alt/CLAUDE.md", "--codex-agents", "alt/AGENTS.md")
        self.assertTrue((self.home / "alt" / "CLAUDE.md").is_file())
        self.assertFalse(self.claude_md.exists())


class SettingsHookTests(BootstrapTestCase):
    def write_settings(self, data):
        self.settings.parent.mkdir(exist_ok=True)
        self.settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def commands(self, event):
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        return [hook["command"] for group in data.get("hooks", {}).get(event, []) for hook in group["hooks"]]

    def test_hooks_merge_without_clobbering_existing_settings(self):
        user_stop = {"matcher": "", "hooks": [{"type": "command", "command": "notify-send done"}]}
        self.write_settings({"model": "some-model", "permissions": {"allow": ["Bash(ls)"]},
                             "hooks": {"Stop": [user_stop], "PreToolUse": [{"matcher": "Bash", "hooks": []}]}})
        code, out, _ = self.cli("--apply", "--claude-hooks")
        self.assertEqual(code, 0)
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(data["model"], "some-model")
        self.assertEqual(data["permissions"], {"allow": ["Bash(ls)"]})
        self.assertIn("PreToolUse", data["hooks"])
        self.assertEqual(self.commands("Stop")[0], "notify-send done")
        self.assertTrue(self.commands("Stop")[1].endswith("footer_latch.py stop"))
        self.assertTrue(self.commands("SessionEnd")[0].endswith("footer_latch.py end"))
        self.assertTrue(self.commands("SessionStart")[0].endswith("footer_latch.py session-start"))
        self.assertEqual(len(list(self.home.rglob("settings.json.canopus-backup-*"))), 1)

    def test_hook_command_is_executable_against_the_root(self):
        self.cli("--apply", "--claude-hooks")
        command = self.commands("Stop")[0]
        self.assertIn(str(self.root / "tools" / "footer_latch.py"), command)
        self.assertTrue(command.startswith("python3 "))

    def test_moved_checkout_updates_stale_hook_in_place(self):
        self.cli("--apply", "--claude-hooks")
        moved = Path(self._tmp.name) / "moved"
        (moved / "tools").mkdir(parents=True)
        out = io.StringIO()
        with redirect_stdout(out):
            ib.main(["--home", str(self.home), "--root", str(moved), "--apply", "--claude-hooks"])
        stops = self.commands("Stop")
        self.assertEqual(len(stops), 1)
        self.assertIn(str(moved), stops[0])

    def test_invalid_settings_json_is_never_overwritten(self):
        self.settings.parent.mkdir()
        self.settings.write_text("{ not json", encoding="utf-8")
        code, _, err = self.cli("--apply", "--claude-hooks")
        self.assertEqual(code, 2)
        self.assertEqual(self.settings.read_text(encoding="utf-8"), "{ not json")
        self.assertFalse(self.claude_md.exists())  # the whole run aborted before writing

    def test_non_object_hooks_is_rejected(self):
        self.write_settings({"hooks": []})
        self.assertEqual(self.cli("--apply", "--claude-hooks")[0], 2)

    def test_remove_strips_only_managed_hooks(self):
        user_stop = {"hooks": [{"type": "command", "command": "notify-send done"}]}
        self.write_settings({"theme": "dark", "hooks": {"Stop": [user_stop]}})
        self.cli("--apply", "--claude-hooks")
        self.cli("--apply", "--remove")
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(data, {"theme": "dark", "hooks": {"Stop": [user_stop]}})

    def test_remove_drops_empty_hooks_table_it_created(self):
        self.write_settings({"theme": "dark"})
        self.cli("--apply", "--claude-hooks")
        self.cli("--apply", "--remove")
        self.assertEqual(json.loads(self.settings.read_text(encoding="utf-8")), {"theme": "dark"})

    def test_remove_on_clean_home_is_a_no_op(self):
        code, out, _ = self.cli("--apply", "--remove")
        self.assertEqual(code, 0)
        self.assertEqual(self.snapshot(), {})
        self.assertIn("absent", out)


class CommandLineTests(BootstrapTestCase):
    def test_subprocess_uses_home_environment_by_default(self):
        env = {**os.environ, "HOME": str(self.home)}
        result = subprocess.run([sys.executable, str(ROOT / "tools" / "install_bootstrap.py"), "--apply"],
                                capture_output=True, text=True, env=env, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.claude_md.is_file())
        self.assertTrue(self.codex_md.is_file())


if __name__ == "__main__":
    unittest.main()

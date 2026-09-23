from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import workspace_doctor  # noqa: E402


class WorkspaceDoctorTests(unittest.TestCase):
    def git(self, root: Path, *args: str) -> None:
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)

    def test_checked_in_synthetic_manifest_is_clean(self) -> None:
        findings = workspace_doctor.audit(ROOT / "examples" / "workspace.toml")
        self.assertEqual(findings, [])

    def test_large_pending_tree_is_an_error(self) -> None:
        finding = workspace_doctor.worktree_finding(
            "project",
            "active",
            workspace_doctor.LARGE_PENDING_PATH_THRESHOLD,
        )
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual(finding.severity, "ERROR")

    def test_missing_governance_fields_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "project").mkdir()
            manifest = root / "workspace.toml"
            manifest.write_text(
                "\n".join(
                    [
                        "version = 2",
                        'root = "."',
                        'allowed_top_levels = ["project", "workspace.toml"]',
                        "[[projects]]",
                        'id = "project"',
                        'path = "project"',
                        "git = false",
                        'remote_policy = "none"',
                    ]
                ),
                encoding="utf-8",
            )
            findings = workspace_doctor.audit(manifest)
        self.assertEqual(sum(item.check == "governance" for item in findings), 4)

    def test_unregistered_git_repository_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "unknown"
            repository.mkdir()
            self.git(repository, "init")
            manifest = root / "workspace.toml"
            manifest.write_text(
                "\n".join(
                    [
                        "version = 2",
                        'root = "."',
                        'allowed_top_levels = ["unknown", "workspace.toml"]',
                    ]
                ),
                encoding="utf-8",
            )
            findings = workspace_doctor.audit(manifest)
        self.assertTrue(any(item.check == "registry" for item in findings))

    def test_remote_fetch_and_push_urls_stay_in_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "project"
            repository.mkdir()
            self.git(repository, "init")
            self.git(repository, "remote", "add", "origin", "https://github.com/example-owner/project.git")
            self.git(repository, "remote", "set-url", "--push", "origin", "https://unexpected.example.invalid/project.git")
            manifest = root / "workspace.toml"
            manifest.write_text(
                "\n".join(
                    [
                        "version = 2",
                        'root = "."',
                        'allowed_top_levels = ["project", "workspace.toml"]',
                        "[[projects]]",
                        'id = "project"',
                        'path = "project"',
                        'lifecycle = "active"',
                        "git = true",
                        'ownership_class = "personal"',
                        'sensitivity = "private"',
                        'source_of_truth = "repository"',
                        'backup_expectation = "hosted-git"',
                        'remote_policy = "required"',
                        'allowed_remote_hosts = ["github.com"]',
                        'allowed_remote_url_prefixes = ["https://github.com/example-owner/"]',
                    ]
                ),
                encoding="utf-8",
            )
            findings = workspace_doctor.audit(manifest)
        self.assertTrue(any(item.check == "remote" for item in findings))

    def test_instruction_bridge_rejects_fenced_example(self) -> None:
        directive = "@" + "AGENTS.md"
        self.assertFalse(
            workspace_doctor.claude_imports_agents(f"```text\n{directive}\n```\n")
        )
        self.assertTrue(workspace_doctor.claude_imports_agents(f"{directive}\n"))


if __name__ == "__main__":
    unittest.main()

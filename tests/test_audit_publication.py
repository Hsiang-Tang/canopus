from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import audit_publication  # noqa: E402


class PublicationAuditTests(unittest.TestCase):
    def repository(self, root: Path) -> None:
        subprocess.run(["git", "init", str(root)], check=True, capture_output=True)

    def test_synthetic_text_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.repository(root)
            (root / "README.md").write_text(
                "Synthetic owner@example.invalid\n",
                encoding="utf-8",
            )
            self.assertEqual(audit_publication.audit(root), [])

    def test_token_pattern_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.repository(root)
            (root / "candidate.txt").write_text("ghp_" + "x" * 24, encoding="utf-8")
            findings = audit_publication.audit(root)
        self.assertTrue(any(item.rule == "github-token" for item in findings))

    def test_machine_path_and_real_email_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.repository(root)
            content = "C:" + "\\Users\\sample-user\\project\n"
            content += "person" + "@" + "example.com\n"
            (root / "candidate.txt").write_text(content, encoding="utf-8")
            rules = {item.rule for item in audit_publication.audit(root)}
        self.assertEqual(rules, {"windows-user-path", "email"})

    def test_forbidden_artifact_name_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.repository(root)
            (root / "snapshot.sqlite3").write_bytes(b"synthetic")
            findings = audit_publication.audit(root)
        self.assertTrue(any(item.rule == "forbidden-artifact" for item in findings))

    def test_extra_deny_term_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.repository(root)
            (root / "candidate.txt").write_text("InternalCodename", encoding="utf-8")
            findings = audit_publication.audit(root, ["internalcodename"])
        self.assertTrue(any(item.rule == "deny-term-1" for item in findings))

    def test_deleted_tracked_file_is_not_a_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.repository(root)
            removed = root / "removed.txt"
            removed.write_text("previous content", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "removed.txt"],
                check=True,
                capture_output=True,
            )
            removed.unlink()
            self.assertEqual(audit_publication.audit(root), [])


if __name__ == "__main__":
    unittest.main()

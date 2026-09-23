from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_control_plane  # noqa: E402


class ControlPlaneTests(unittest.TestCase):
    def copied_repository(self, destination: Path) -> Path:
        return Path(
            shutil.copytree(
                ROOT,
                destination / "candidate",
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )
        )

    def test_real_repository_is_valid(self) -> None:
        self.assertEqual(check_control_plane.validate(ROOT), [])

    def test_missing_required_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = self.copied_repository(Path(temporary))
            (candidate / "README.md").unlink()
            errors = check_control_plane.validate(candidate)
        self.assertIn("README.md: required file is missing", errors)

    def test_privacy_default_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = self.copied_repository(Path(temporary))
            config = candidate / "canopus.toml"
            config.write_text(
                config.read_text(encoding="utf-8").replace(
                    "disclose_local_paths = false",
                    "disclose_local_paths = true",
                ),
                encoding="utf-8",
            )
            errors = check_control_plane.validate(candidate)
        self.assertIn("canopus.toml: status.disclose_local_paths must be false", errors)


if __name__ == "__main__":
    unittest.main()

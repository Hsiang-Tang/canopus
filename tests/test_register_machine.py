from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import register_machine  # noqa: E402


class RegisterMachineTests(unittest.TestCase):
    def test_environment_precedes_git_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {register_machine.ROOT_ENVIRONMENT: directory},
            clear=True,
        ), patch.object(register_machine, "_git_config_get") as get_config:
            self.assertEqual(register_machine.configured_root(), str(Path(directory).resolve()))
        get_config.assert_not_called()

    def test_git_config_is_fallback(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch.object(
            register_machine,
            "_git_config_get",
            return_value="/synthetic/reference",
        ):
            self.assertEqual(register_machine.configured_root(), "/synthetic/reference")

    def test_set_pointer_is_namespaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            register_machine.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0),
        ) as run:
            register_machine.set_pointer(register_machine.ROOT_CONFIG_KEY, Path(directory))
        run.assert_called_once_with(
            [
                "git",
                "config",
                "--global",
                register_machine.ROOT_CONFIG_KEY,
                str(Path(directory).resolve()),
            ],
            check=True,
        )

    def test_remove_pointer_never_deletes_files(self) -> None:
        with patch.object(
            register_machine.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 5),
        ) as run:
            register_machine.remove_pointer(register_machine.MANIFEST_CONFIG_KEY)
        run.assert_called_once_with(
            [
                "git",
                "config",
                "--global",
                "--unset-all",
                register_machine.MANIFEST_CONFIG_KEY,
            ],
            check=False,
        )


if __name__ == "__main__":
    unittest.main()

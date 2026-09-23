#!/usr/bin/env python3
"""Register reference-control and workspace-manifest pointers.

This is a deliberately bounded machine registration
model. It changes only namespaced global Git configuration keys and never
copies a manifest into the repository.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROOT_ENVIRONMENT = "CANOPUS_ROOT"
ROOT_CONFIG_KEY = "canopus.root"
MANIFEST_ENVIRONMENT = "CANOPUS_WORKSPACE_MANIFEST"
MANIFEST_CONFIG_KEY = "canopus.workspaceManifest"


def _git_config_get(key: str) -> str | None:
    result = subprocess.run(
        ["git", "config", "--global", "--get", key],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or None


def configured_pointer(environment: str, config_key: str) -> str | None:
    """Resolve an environment override, then a global Git config pointer."""
    if override := os.environ.get(environment):
        return str(Path(override).expanduser().resolve())
    return _git_config_get(config_key)


def configured_root() -> str | None:
    return configured_pointer(ROOT_ENVIRONMENT, ROOT_CONFIG_KEY)


def configured_workspace_manifest() -> str | None:
    return configured_pointer(MANIFEST_ENVIRONMENT, MANIFEST_CONFIG_KEY)


def set_pointer(key: str, path: Path) -> None:
    subprocess.run(
        ["git", "config", "--global", key, str(path.resolve())],
        check=True,
    )


def remove_pointer(key: str) -> None:
    subprocess.run(
        ["git", "config", "--global", "--unset-all", key],
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--apply", action="store_true")
    actions.add_argument("--remove", action="store_true")
    parser.add_argument(
        "--workspace-manifest",
        type=Path,
        help="register an existing machine-local manifest without copying it",
    )
    args = parser.parse_args()

    if args.apply:
        if not (ROOT / ".git").exists():
            parser.error(f"reference root is not a Git checkout: {ROOT}")
        set_pointer(ROOT_CONFIG_KEY, ROOT)
        print(f"registered {ROOT_CONFIG_KEY}={ROOT}")
        if args.workspace_manifest is not None:
            manifest = args.workspace_manifest.expanduser().resolve()
            if not manifest.is_file():
                parser.error(f"workspace manifest does not exist: {manifest}")
            set_pointer(MANIFEST_CONFIG_KEY, manifest)
            print(f"registered {MANIFEST_CONFIG_KEY}={manifest}")
        elif current := configured_workspace_manifest():
            print(f"preserved {MANIFEST_CONFIG_KEY}={current}")
        return 0

    if args.remove:
        remove_pointer(ROOT_CONFIG_KEY)
        remove_pointer(MANIFEST_CONFIG_KEY)
        print("removed reference pointers; files were preserved")
        return 0

    print(configured_root() or "reference root: not registered")
    manifest = configured_workspace_manifest()
    print(
        f"workspace manifest: {manifest}"
        if manifest
        else "workspace manifest: not registered"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

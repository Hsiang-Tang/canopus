"""Shared TOML read helper for reference tools."""

from __future__ import annotations

import tomllib
from pathlib import Path


def read_toml(path: Path) -> dict[str, object]:
    """Read and parse a UTF-8 TOML file."""
    return tomllib.loads(path.read_text(encoding="utf-8"))

#!/usr/bin/env python3
"""Validate the reference repository's closed control-plane contract."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path, PurePosixPath

import _toml


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PRODUCT_NAME = "Canopus"
EXPECTED_READ_ORDER = [
    "AGENTS.md",
    "README.md",
    "docs/ARCHITECTURE.md",
    "rules/security.md",
    "rules/workspace.md",
    "docs/specs/reference-foundation/spec.md",
    "docs/specs/reference-foundation/plan.md",
    "docs/specs/reference-foundation/tasks.md",
    "docs/specs/bounded-convergence/spec.md",
    "docs/VERIFICATION.md",
    "docs/STATUS.md",
]


def valid_relative(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    candidate = PurePosixPath(value)
    return not candidate.is_absolute() and ".." not in candidate.parts


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        control = _toml.read_toml(root / "control-plane.toml")
        product = _toml.read_toml(root / "canopus.toml")
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [f"configuration cannot be read: {error}"]

    if control.get("version") != 1:
        errors.append("control-plane.toml: version must be 1")
    if control.get("product_name") != EXPECTED_PRODUCT_NAME:
        errors.append("control-plane.toml: unexpected product_name")

    session = control.get("session")
    read_order = session.get("read_order") if isinstance(session, dict) else None
    if read_order != EXPECTED_READ_ORDER:
        errors.append("control-plane.toml: session.read_order does not match the contract")

    validation = control.get("validation")
    required = validation.get("required_files") if isinstance(validation, dict) else None
    if not isinstance(required, list) or not required:
        errors.append("control-plane.toml: validation.required_files must be non-empty")
        required = []
    if len(required) != len(set(map(str, required))):
        errors.append("control-plane.toml: validation.required_files contains duplicates")
    for entry in required:
        if not valid_relative(entry):
            errors.append(f"control-plane.toml: invalid required path {entry!r}")
            continue
        path = root / str(entry)
        if not path.is_file():
            errors.append(f"{entry}: required file is missing")
        elif path.is_symlink():
            errors.append(f"{entry}: required file must not be a symlink")

    if product.get("version") != 1:
        errors.append("canopus.toml: version must be 1")
    if product.get("product_name") != EXPECTED_PRODUCT_NAME:
        errors.append("canopus.toml: unexpected product_name")
    state = product.get("state")
    if not isinstance(state, dict) or state.get("truth_model") != "federated":
        errors.append("canopus.toml: state.truth_model must be federated")
    if isinstance(state, dict) and state.get("chat_is_canonical") is not False:
        errors.append("canopus.toml: chat_is_canonical must be false")
    automation = product.get("automation")
    if not isinstance(automation, dict) or automation.get("unattended_mode") != "observe-and-propose":
        errors.append("canopus.toml: unattended_mode must be observe-and-propose")
    status = product.get("status")
    if not isinstance(status, dict):
        errors.append("canopus.toml: status table is required")
    else:
        for key in (
            "disclose_project_identifiers",
            "disclose_local_paths",
            "disclose_remote_urls",
            "disclose_sensitive_values",
        ):
            if status.get(key) is not False:
                errors.append(f"canopus.toml: status.{key} must be false")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print(f"control-plane validation: FAILED ({len(errors)} error(s))")
        return 1
    print("control-plane validation: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

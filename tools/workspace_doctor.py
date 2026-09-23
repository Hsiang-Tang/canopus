#!/usr/bin/env python3
"""Read-only manifest-driven workspace drift audit."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import _toml


OWNERSHIP_CLASSES = {"personal", "organization", "third-party", "generated"}
SENSITIVITIES = {"public", "private", "restricted"}
SOURCE_OWNERS = {"repository", "local-sensitive-store", "external-owner", "generated"}
BACKUP_EXPECTATIONS = {"hosted-git", "local-encrypted-backup", "external-owner", "rebuildable", "none"}
REMOTE_POLICIES = {"required", "optional", "none", "preserve"}
LARGE_PENDING_PATH_THRESHOLD = 1_000


@dataclass(frozen=True)
class Finding:
    severity: str
    check: str
    message: str


def worktree_finding(relative: str, lifecycle: str, pending: int) -> Finding | None:
    if pending <= 0:
        return None
    if pending >= LARGE_PENDING_PATH_THRESHOLD:
        return Finding(
            "ERROR",
            "worktree",
            f"{relative}: {pending} pending paths; inspect generated-output roots and ignore rules",
        )
    severity = "INFO" if lifecycle == "backup-only" else "WARN"
    return Finding(severity, "worktree", f"{relative}: {pending} pending paths")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def git_common_directory(repo: Path) -> Path:
    return Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()


def remote_host(url: str) -> str:
    if "://" in url:
        return urlparse(url).hostname or ""
    if "@" in url and ":" in url:
        return url.split("@", 1)[1].split(":", 1)[0]
    return "local"


def valid_relative(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    candidate = PurePosixPath(value)
    return not candidate.is_absolute() and ".." not in candidate.parts and value != "."


def is_excluded(relative: str, exclusions: set[str]) -> bool:
    return any(relative == item or relative.startswith(f"{item}/") for item in exclusions)


def claude_imports_agents(text: str) -> bool:
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if fence:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith("```"):
            fence = "```"
            continue
        if stripped.startswith("~~~"):
            fence = "~~~"
            continue
        if stripped == "@AGENTS.md":
            return True
    return False


def discover_git_roots(root: Path, exclusions: set[str] | None = None) -> set[str]:
    exclusions = exclusions or set()
    roots: set[str] = set()
    for current, directories, _files in os.walk(root):
        current_path = Path(current)
        kept: list[str] = []
        for name in directories:
            if name in {"node_modules", "__pycache__", ".cache"}:
                continue
            relative = (current_path / name).relative_to(root).as_posix()
            if not is_excluded(relative, exclusions):
                kept.append(name)
        directories[:] = kept
        git_marker = current_path / ".git"
        if git_marker.is_dir() or git_marker.is_file():
            roots.add(current_path.relative_to(root).as_posix())
            if ".git" in directories:
                directories.remove(".git")
    return roots


def audit(manifest_path: Path, *, include_inbox_age: bool = True) -> list[Finding]:
    findings: list[Finding] = []
    try:
        config = _toml.read_toml(manifest_path)
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [Finding("ERROR", "manifest", f"cannot read manifest: {error}")]

    if config.get("version") != 2:
        return [Finding("ERROR", "manifest", "only manifest version 2 is supported")]
    root_value = config.get("root")
    if not isinstance(root_value, str) or not root_value:
        return [Finding("ERROR", "manifest", "root must be a non-empty string")]
    root = (manifest_path.parent / root_value).resolve()

    exclusions: set[str] = set()
    for item in config.get("git_discovery_excludes", []):
        if valid_relative(item):
            exclusions.add(item)
        else:
            findings.append(Finding("ERROR", "manifest", f"invalid Git discovery exclusion: {item!r}"))

    project_items = config.get("projects", [])
    if not isinstance(project_items, list):
        return findings + [Finding("ERROR", "manifest", "projects must be an array of tables")]

    projects: dict[str, dict[str, object]] = {}
    project_ids: set[str] = set()
    for project in project_items:
        if not isinstance(project, dict):
            findings.append(Finding("ERROR", "manifest", "each project must be a table"))
            continue
        project_id = project.get("id")
        relative = project.get("path")
        if not isinstance(project_id, str) or not project_id:
            findings.append(Finding("ERROR", "manifest", "project id must be a non-empty string"))
            continue
        if project_id in project_ids:
            findings.append(Finding("ERROR", "manifest", f"duplicate project id: {project_id}"))
        project_ids.add(project_id)
        if not valid_relative(relative):
            findings.append(Finding("ERROR", "manifest", f"{project_id}: invalid project path {relative!r}"))
            continue
        assert isinstance(relative, str)
        if relative in projects:
            findings.append(Finding("ERROR", "manifest", f"duplicate project path: {relative}"))
            continue
        projects[relative] = project

        governed = {
            "ownership_class": (OWNERSHIP_CLASSES, project.get("ownership_class")),
            "sensitivity": (SENSITIVITIES, project.get("sensitivity")),
            "source_of_truth": (SOURCE_OWNERS, project.get("source_of_truth")),
            "backup_expectation": (BACKUP_EXPECTATIONS, project.get("backup_expectation")),
        }
        for field, (allowed, value) in governed.items():
            if value not in allowed:
                findings.append(Finding("ERROR", "governance", f"{relative}: invalid or missing {field}"))
        remote_policy = project.get("remote_policy", "optional")
        if remote_policy not in REMOTE_POLICIES:
            findings.append(Finding("ERROR", "manifest", f"{relative}: invalid remote policy {remote_policy!r}"))
        if remote_policy == "none" and (
            project.get("allowed_remote_hosts") or project.get("allowed_remote_url_prefixes")
        ):
            findings.append(Finding("ERROR", "manifest", f"{relative}: remote allowlists conflict with remote_policy=none"))

    if not root.is_dir():
        return findings + [Finding("ERROR", "root", "workspace root does not exist")]

    allowed_top_levels = set(config.get("allowed_top_levels", []))
    for name in sorted({item.name for item in root.iterdir()} - allowed_top_levels):
        findings.append(Finding("ERROR", "top-level", f"unregistered top-level entry: {name}"))

    registered_git = {path for path, item in projects.items() if item.get("git", False)}
    common_directories: dict[Path, dict[str, object]] = {}
    for relative in sorted(registered_git):
        path = root / relative
        if path.exists() and (path / ".git").exists():
            try:
                common_directories[git_common_directory(path)] = projects[relative]
            except RuntimeError:
                pass

    linked_worktrees: dict[str, dict[str, object]] = {}
    for relative in sorted(discover_git_roots(root, exclusions) - registered_git):
        try:
            owner = common_directories.get(git_common_directory(root / relative))
        except RuntimeError:
            owner = None
        if owner is None:
            findings.append(Finding("ERROR", "registry", f"unregistered Git repository: {relative}"))
        else:
            linked_worktrees[relative] = owner

    for relative, project in sorted(projects.items()):
        path = root / relative
        if not path.exists():
            findings.append(Finding("ERROR", "project", f"missing project path: {relative}"))
            continue
        if not project.get("git", False):
            continue
        if not (path / ".git").exists():
            findings.append(Finding("ERROR", "git", f"missing Git metadata: {relative}"))
            continue
        if (
            project.get("ownership_class") == "personal"
            and project.get("lifecycle") in {"active", "experimental"}
            and (path / "AGENTS.md").is_file()
        ):
            bridge = (path / "CLAUDE.md").read_text(encoding="utf-8") if (path / "CLAUDE.md").is_file() else ""
            if not claude_imports_agents(bridge):
                findings.append(Finding("ERROR", "instruction-bridge", f"{relative}: CLAUDE.md must import @AGENTS.md"))
        try:
            expected = project.get("expected_email")
            if expected and git(path, "config", "--local", "user.email") != expected:
                findings.append(Finding("ERROR", "identity", f"{relative}: repository identity does not match manifest"))
            remotes = git(path, "remote").splitlines()
            policy = project.get("remote_policy", "optional")
            if policy == "none" and remotes:
                findings.append(Finding("ERROR", "remote", f"{relative}: remote is forbidden"))
            if policy == "required" and not remotes:
                findings.append(Finding("ERROR", "remote", f"{relative}: required remote is missing"))
            allowed_hosts = set(project.get("allowed_remote_hosts", []))
            allowed_prefixes = tuple(project.get("allowed_remote_url_prefixes", []))
            for name in remotes:
                urls = {
                    *git(path, "remote", "get-url", "--all", name).splitlines(),
                    *git(path, "remote", "get-url", "--push", "--all", name).splitlines(),
                }
                for url in urls:
                    if allowed_hosts and remote_host(url) not in allowed_hosts:
                        findings.append(Finding("ERROR", "remote", f"{relative}: unapproved remote host"))
                    if allowed_prefixes and not url.startswith(allowed_prefixes):
                        findings.append(Finding("ERROR", "remote", f"{relative}: remote URL is outside approved scope"))
            pending = len(git(path, "status", "--porcelain=v1", "--untracked-files=all").splitlines())
            if finding := worktree_finding(relative, str(project.get("lifecycle", "unknown")), pending):
                findings.append(finding)
        except RuntimeError as error:
            findings.append(Finding("ERROR", "git", f"{relative}: {error}"))

    for relative, owner in sorted(linked_worktrees.items()):
        try:
            pending = len(git(root / relative, "status", "--porcelain=v1", "--untracked-files=all").splitlines())
            if finding := worktree_finding(relative, str(owner.get("lifecycle", "unknown")), pending):
                findings.append(finding)
        except RuntimeError as error:
            findings.append(Finding("ERROR", "git", f"{relative}: {error}"))

    inbox = root / "00_Inbox"
    max_age = int(config.get("inbox_max_age_days", 14)) * 86400
    if include_inbox_age and inbox.is_dir():
        for path in inbox.rglob("*"):
            if path.is_file() and time.time() - path.stat().st_mtime > max_age:
                findings.append(Finding("WARN", "inbox", f"stale inbox file: {path.relative_to(root)}"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip-inbox-age", action="store_true")
    args = parser.parse_args()
    findings = audit(args.manifest.resolve(), include_inbox_age=not args.skip_inbox_age)
    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity:<5} {item.check:<18} {item.message}")
    else:
        print("workspace doctor: OK")
    errors = sum(item.severity == "ERROR" for item in findings)
    warnings = sum(item.severity == "WARN" for item in findings)
    information = sum(item.severity == "INFO" for item in findings)
    if not args.json:
        print(f"summary: errors={errors} warnings={warnings} info={information}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

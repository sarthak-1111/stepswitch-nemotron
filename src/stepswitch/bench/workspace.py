"""Workspaces for bench runs: clean copies of task repositories as fresh git repositories.

Git runs without the user's or the system's configuration and without inherited `GIT_*`
variables, so hooks, signing, line-ending conversion or an outer repository never change what
a task sees.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

IDENTITY = (
    "-c",
    "user.name=stepswitch-bench",
    "-c",
    "user.email=bench@example.invalid",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "core.autocrlf=false",
    # Git for Windows stops at 260 characters, and a bench workspace sits several directories
    # deep (run, contestant, task, seed); other platforms ignore the setting.
    "-c",
    "core.longpaths=true",
)
# Pauses before retrying a copy or a delete the file system refused (`_retry`).
RETRY_PAUSES = (0.2, 0.5, 1.0, 2.0)
GENERATED = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".git", "*.pyc")


def git_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env.update(
        {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"}
    )
    return env


def git(cwd: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *IDENTITY, *args],
        cwd=cwd,
        input=stdin.encode("utf-8") if stdin is not None else None,
        capture_output=True,
        env=git_env(),
        check=True,
    )


def copy_repo(source: Path, dest: Path) -> Path:
    """Copy a task repository without generated files or version-control data."""

    def copy() -> None:
        if dest.exists():
            remove_tree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns(*GENERATED))

    _retry(copy)
    return dest


def _retry(action: Callable[[], Any]) -> Any:
    """Run `action`, again after a pause when the file system refuses with a sharing violation:
    on Windows a virus scanner or the indexer briefly opens files a moment after they are
    written, and copying or deleting them then fails (WinError 32, a PermissionError)."""
    for pause in (*RETRY_PAUSES, None):
        try:
            return action()
        except PermissionError:
            if pause is None:
                raise
            time.sleep(pause)
    return None  # pragma: no cover - the loop returns or raises


def init_repo(path: Path, message: str = "task start") -> str:
    """Make `path` a git repository with one commit of its files; return the commit."""
    git(path, "init", "-q")
    git(path, "add", "-A")
    git(path, "commit", "-q", "--no-verify", "-m", message)
    return git(path, "rev-parse", "HEAD").stdout.decode().strip()


def apply_diff(repo: Path, diff: str) -> None:
    if diff.strip():
        git(repo, "apply", "--whitespace=nowarn", "-", stdin=diff)


def _clear_readonly(func: Callable[..., Any], path: str, _exc: Any) -> None:
    # Git writes its object files read-only; Windows refuses to delete those.
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def remove_tree(path: Path) -> None:
    def remove() -> None:
        if not path.exists():
            return
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=_clear_readonly)
        else:  # pragma: no cover - Python 3.11
            shutil.rmtree(path, onerror=_clear_readonly)

    _retry(remove)


def clean(path: Path) -> bool:
    """Remove a finished run's work area; a file still held open leaves it in place (False)
    instead of stopping the bench."""
    try:
        remove_tree(path)
    except OSError:
        return False
    return True

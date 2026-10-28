"""Bench workspaces: copies and deletes the file system briefly refuses are retried, and a work
area that cannot be removed does not stop the bench."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

from stepswitch.bench import workspace


@pytest.fixture(autouse=True)
def no_pauses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(workspace, "RETRY_PAUSES", (0.0, 0.0))


def test_a_copy_refused_twice_is_retried(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    (source / "pkg").mkdir(parents=True)
    (source / "pkg" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    real = shutil.copytree
    refusals = [PermissionError(32, "in use"), PermissionError(32, "in use")]

    def flaky(*args: Any, **kwargs: Any) -> Any:
        if refusals:
            # The directory exists by the time the copy fails, as with a real refusal.
            Path(args[1]).mkdir(parents=True, exist_ok=True)
            raise refusals.pop()
        return real(*args, **kwargs)

    monkeypatch.setattr(shutil, "copytree", flaky)
    dest = workspace.copy_repo(source, tmp_path / "work" / "repo")
    assert (dest / "pkg" / "mod.py").read_text(encoding="utf-8") == "x = 1\n"
    assert not refusals


def test_a_copy_refused_every_time_still_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_args: Any, **_kwargs: Any) -> Any:
        raise PermissionError(32, "in use")

    monkeypatch.setattr(shutil, "copytree", refuse)
    with pytest.raises(PermissionError):
        workspace.copy_repo(tmp_path, tmp_path / "work" / "repo")


def test_clean_leaves_a_held_work_area_in_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    held = tmp_path / "held"
    held.mkdir()

    def refuse(*_args: Any, **_kwargs: Any) -> None:
        raise PermissionError(32, "in use")

    monkeypatch.setattr(shutil, "rmtree", refuse)
    assert workspace.clean(held) is False and held.is_dir()
    monkeypatch.undo()
    assert workspace.clean(held) is True and not held.exists()
    assert workspace.clean(held) is True

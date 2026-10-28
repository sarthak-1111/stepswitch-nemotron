"""The bench in dollars: hosted endpoints, a cap on the whole bench, interleaved runs and the
cost of each run (ADR 0044)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from stepswitch.bench import runner
from stepswitch.bench.report import MANIFEST_FILE, RESULTS_FILE
from stepswitch.bench.suites import load_suite
from stepswitch.core.task import Budgets
from tests.unit.bench_project import make_project


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return make_project(tmp_path / "project")


def read_rows(out: Path) -> list[dict[str, Any]]:
    lines = (out / RESULTS_FILE).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_the_cap_stops_the_bench_and_bounds_each_run(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    suite = load_suite("tiny", project)
    seen: list[tuple[str, int, float | None]] = []

    def fake_run_one(task: Any, contestant: Any, seed: int, **kwargs: Any) -> dict[str, Any]:
        options = kwargs["options"]
        seen.append((contestant.name, seed, options.budgets.usd))
        return {
            "task": task.id,
            "contestant": contestant.name,
            "seed": seed,
            "passed": True,
            "status": "done",
            "wall_seconds": 1.0,
            "cost_usd": 0.4,
        }

    monkeypatch.setattr(runner, "run_one", fake_run_one)
    out = project / "bench" / "results" / "capped"
    runner.run_bench(
        suite,
        runner.parse_contestants("a/one,a/two"),
        root=project,
        out_dir=out,
        options=runner.BenchOptions(
            seeds=2,
            budgets=Budgets(usd=0.5),
            budget_usd_total=1.0,
            allow_remote=True,
            interleave=True,
        ),
    )
    # Interleaved: both contestants on seed 0, then seed 1; the third run brings the bench to
    # $1.20, so the fourth never starts. Each run's budget is the per-task one or what is left.
    assert [(name, seed) for name, seed, _ in seen] == [("a/one", 0), ("a/two", 0), ("a/one", 1)]
    assert [usd for _, _, usd in seen] == [0.5, 0.5, 0.2]
    manifest = json.loads((out / MANIFEST_FILE).read_text(encoding="utf-8"))
    assert manifest["stopped"] == {
        "reason": "budget_usd_total",
        "spent_usd": 1.2,
        "runs": 3,
        "of": 4,
    }
    assert manifest["spent_usd"] == 1.2 and manifest["budget_usd_total"] == 1.0
    assert manifest["budget_usd"] == 0.5 and manifest["allow_remote"] is True
    assert len(read_rows(out)) == 3


def test_runs_follow_contestants_without_interleave(project: Path) -> None:
    suite = load_suite("tiny", project)
    contestants = runner.parse_contestants("a/one,a/two")
    order = runner._schedule(contestants, suite.tasks, runner.BenchOptions(seeds=2))
    assert [(c.name, s) for c, _t, s in order] == [
        ("a/one", 0),
        ("a/one", 1),
        ("a/two", 0),
        ("a/two", 1),
    ]


def test_the_manifest_records_the_policy_and_its_file(project: Path) -> None:
    from stepswitch.config import Config

    policy = project / "policy.toml"
    policy.write_text("[review]\nsecond_opinion = true\n", encoding="utf-8")
    record = runner.policy_file_record(policy, project)
    assert record["file"] == "policy.toml" and len(record["sha256"]) == 64
    config = Config.model_validate(
        {
            "policy": {"rules": [{"name": "r", "to": {"model": "m"}}]},
            "review": {"second_opinion": True},
            "budgets": {"usd": 0.5},
        }
    )
    assert runner.policy_record(config, record) == {
        "rules": [{"name": "r", "to": {"model": "m"}}],
        "review": {"second_opinion": True},
        "budgets": {"usd": 0.5},
        "file": record,
    }
    assert runner.policy_record(None) == {"rules": [], "review": {}, "budgets": {}}


def test_allow_remote_and_the_dollar_budget_reach_the_task(project: Path) -> None:
    suite = load_suite("tiny", project)
    seen: dict[str, Any] = {}

    def capture(spec: Any, **_kwargs: Any) -> Any:
        seen["spec"] = spec
        raise RuntimeError("stop here")

    out = project / "bench" / "results" / "remote"
    runner.run_bench(
        suite,
        runner.parse_contestants("router"),
        root=project,
        out_dir=out,
        options=runner.BenchOptions(allow_remote=True, budgets=Budgets(usd=0.25)),
        run_task=capture,
    )
    assert seen["spec"].allow_remote is True and seen["spec"].budgets.usd == 0.25
    row = read_rows(out)[0]
    assert row["cost_usd"] is None and row["infra_error"] is True

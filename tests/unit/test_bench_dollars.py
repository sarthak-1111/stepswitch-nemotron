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


STEP_EVENTS = [
    {"seq": 1, "type": "task_start", "spec": {"instruction": "secret plan"}},
    {
        "seq": 2,
        "type": "decision",
        "step": 1,
        "step_type": "edit",
        "chosen": "tf/super",
        "switched": False,
        "rule": "super-edits",
        "level": 2,
        "candidates": ["long"],
    },
    {
        "seq": 3,
        "type": "step",
        "step": 1,
        "step_type": "edit",
        "worker": "tf/super",
        "tool_calls": ["edit"],
        "text": "model text",
        "usage": {"input_tokens": 9},
        "cost_usd": 0.001,
        "wall_seconds": 1.5,
        "response_blob": "abc",
    },
    {
        "seq": 4,
        "type": "tool",
        "step": 1,
        "name": "edit",
        "is_error": False,
        "output": "file contents",
        "changed_files": ["calc.py"],
    },
    {
        "seq": 5,
        "type": "gates",
        "step": 1,
        "run": 1,
        "verdict": {
            "passed": False,
            "failed_gate": "full_tests",
            "report": "long report",
            "results": [
                {"name": "full_tests", "status": "failed", "seconds": 0.7, "summary": "1 failed"}
            ],
        },
    },
    {
        "seq": 6,
        "type": "escalation",
        "step": 1,
        "from": "T3",
        "to": "remote",
        "from_level": 2,
        "to_level": 3,
        "reason": "gates failed twice",
    },
    {
        "seq": 7,
        "type": "review",
        "step": 2,
        "reviewer": "tf/gpt-oss",
        "reviewer_family": "gpt-oss",
        "approved": True,
        "issues": [{"text": "nit"}],
        "second_opinion": True,
        "agrees": True,
        "text": "review text",
    },
    {"seq": 8, "type": "task_end", "status": "done", "stop_reason": None, "summary": "summary"},
]


def test_steps_keep_the_routing_of_each_run_and_no_text(project: Path) -> None:
    from stepswitch.core.task import TaskResult

    suite = load_suite("tiny", project)

    def fake_task(spec: Any, **_kwargs: Any) -> TaskResult:
        run_dir = project / ".stepswitch" / "runs" / "t1"
        run_dir.mkdir(parents=True, exist_ok=True)
        lines = "".join(json.dumps(event) + "\n" for event in STEP_EVENTS)
        (run_dir / "events.jsonl").write_text(lines, encoding="utf-8")
        return TaskResult(task_id="t1", status="done", run_dir=str(run_dir))

    out = project / "bench" / "results" / "steps"
    runner.run_bench(
        suite,
        runner.parse_contestants("router"),
        root=project,
        out_dir=out,
        options=runner.BenchOptions(preflight=False),
        run_task=fake_task,
    )
    lines = (out / runner.STEPS_FILE).read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    tasks = {task.id for task in suite.tasks}
    assert {r["task"] for r in records} == tasks and {r["contestant"] for r in records} == {
        "router"
    }
    first = [r for r in records if r["task"] == suite.tasks[0].id]
    assert [r["type"] for r in first] == [
        "decision",
        "step",
        "tool",
        "gates",
        "escalation",
        "review",
        "task_end",
    ]
    by_type = {r["type"]: r for r in first}
    assert by_type["step"]["worker"] == "tf/super" and by_type["step"]["cost_usd"] == 0.001
    assert by_type["gates"]["failed_gate"] == "full_tests"
    assert by_type["gates"]["results"] == [
        {"name": "full_tests", "status": "failed", "seconds": 0.7}
    ]
    assert by_type["escalation"]["to"] == "remote"
    assert by_type["review"]["issues"] == 1 and by_type["review"]["agrees"] is True
    text = json.dumps(records)
    for secret in ("secret plan", "model text", "file contents", "review text", "summary"):
        assert secret not in text

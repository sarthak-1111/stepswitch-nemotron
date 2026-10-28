"""`ssw policy check`: the routing policy checked against the configured workers, no model
called."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from stepswitch.cli import app
from stepswitch.pricing import Prices
from stepswitch.router.check import check_policy, render
from stepswitch.router.rules import parse_rules
from stepswitch.workers.base import WorkerSpec

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()

SMALL = WorkerSpec(
    id="far/small", endpoint="far", model="small", tier="t1", local=False, prices=Prices(0.1, 0.4)
)
BIG = WorkerSpec(
    id="far/big", endpoint="far", model="big", tier="remote", local=False, prices=Prices(1.0, 3.0)
)
RULES = [
    {
        "name": "small-reads",
        "when": {"step_type": ["navigate", "read", "summarize"]},
        "to": {"model": "small"},
    },
    {
        "name": "ghost-edits",
        "when": {"step_type": "edit", "escalations": 0},
        "to": {"model": "nope"},
    },
    {
        "name": "big-does-the-rest",
        "when": {"step_type": ["plan", "edit", "run", "triage", "review"]},
        "to": {"model": "big"},
    },
]


def test_a_rule_no_worker_matches_is_an_error_and_its_steps_fall_through() -> None:
    report = check_policy(parse_rules(RULES), [SMALL, BIG], budget_usd=0.5)
    assert not report.ok
    (problem,) = report.problems
    assert (
        problem.severity == "error"
        and "ghost-edits" in problem.message
        and "model = nope" in problem.message
    )
    routes = {r.step_type: r for r in report.routes}
    assert (routes["read"].first, routes["read"].first_rule) == ("far/small", "small-reads")
    # The ghost rule never applies: edits go to the next matching rule, before and after an
    # escalation.
    assert (routes["edit"].first, routes["edit"].first_rule) == ("far/big", "big-does-the-rest")
    assert routes["edit"].escalated == "far/big"
    text = "\n".join(render(report))
    assert "error: rule ghost-edits" in text and "read        far/small, rule small-reads" in text


def test_unpriced_remote_workers_and_a_missing_dollar_budget_are_warnings() -> None:
    unpriced = WorkerSpec(id="far/free", endpoint="far", model="free", tier="t2", local=False)
    report = check_policy(parse_rules(RULES[:1] + RULES[2:]), [SMALL, BIG, unpriced])
    assert report.ok
    messages = [p.message for p in report.problems]
    assert all(p.severity == "warning" for p in report.problems)
    assert any("far/free is remote and has no prices" in m for m in messages)
    assert any("no dollar budget" in m for m in messages)


def _project(tmp_path: Path, policy: str, models: list[str] | None) -> Path:
    root = tmp_path / "project"
    (root / ".stepswitch").mkdir(parents=True)
    shutil.copy(ROOT / "bench" / "policies" / policy, root / "stepswitch.toml")
    endpoint = '[[endpoints]]\nname = "tokenfactory"\npreset = "tokenfactory"\n'
    if models is not None:
        endpoint += "models = [" + ", ".join(f'"{m}"' for m in models) + "]\n"
    (root / ".stepswitch" / "local.toml").write_text("schema = 1\n\n" + endpoint, encoding="utf-8")
    return root


def test_the_cli_catches_a_policy_whose_model_the_endpoint_does_not_serve(tmp_path: Path) -> None:
    # The Nano-first demo policy with an endpoint that lists no Nano: its edits would run on Ultra.
    root = _project(
        tmp_path,
        "tokenfactory-nano-first.toml",
        [
            "nvidia/Nemotron-3_5-Lightning",
            "nvidia/Nemotron-3-Ultra-550b-a55b",
            "openai/gpt-oss-120b",
        ],
    )
    result = runner.invoke(app, ["-C", str(root), "policy", "check"])
    assert result.exit_code == 1, result.output
    assert (
        "error: rule nano-tries-the-work-first sends steps to no configured worker" in result.output
    )
    assert "edit        tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b" in result.output


def test_the_cli_passes_the_shipped_token_factory_policies(tmp_path: Path) -> None:
    for policy in ("tokenfactory-ladder.toml", "tokenfactory-nano-first.toml"):
        root = _project(tmp_path / policy, policy, None)
        result = runner.invoke(app, ["-C", str(root), "policy", "check", "--json"])
        assert result.exit_code == 0, result.output
        report = json.loads(result.output)
        assert report["ok"] and report["problems"] == []
        edit = next(r for r in report["routes"] if r["step_type"] == "edit")
        assert edit["escalated"] == "tokenfactory/nvidia/Nemotron-3-Ultra-550b-a55b"

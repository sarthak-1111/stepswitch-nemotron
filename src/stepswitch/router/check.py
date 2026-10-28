"""A static check of a project's routing policy (`ssw policy check`).

It routes one step of every step type through the real router, against the workers the
project configures, before and after an escalation, and lists what cannot work as written: a
pinning rule that matches no worker (the router skips it at every step, so its steps silently go
to the next matching rule), a step type no worker can take, and remote workers whose dollars a
budget cannot see. No model is called and nothing is billed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from stepswitch.core.task import STEP_TYPES
from stepswitch.router.escalation import Ladder, start_level
from stepswitch.router.features import TaskFeatures
from stepswitch.router.router import Decision, RouterState, route
from stepswitch.router.rules import Rule, describe_selector, unmatched_pins
from stepswitch.workers.base import WorkerSpec


@dataclass(frozen=True)
class Problem:
    severity: str  # "error" or "warning"
    message: str


@dataclass(frozen=True)
class StepRoute:
    step_type: str
    first: str | None
    first_rule: str | None
    escalated: str | None
    escalated_rule: str | None


@dataclass
class PolicyReport:
    workers: list[str]
    remote: list[str]
    start_level: int
    escalated_level: int | None
    routes: list[StepRoute] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(p.severity == "error" for p in self.problems)

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "ok": self.ok}


def check_policy(
    rules: Sequence[Rule],
    specs: Sequence[WorkerSpec],
    *,
    budget_usd: float | None = None,
    allow_remote: bool = True,
    track: str = "general",
) -> PolicyReport:
    """Route each step type once with the project's rules and workers, and list the problems."""
    usable = [s for s in specs if (s.local or allow_remote) and not s.pin_only]
    ladder = Ladder.for_levels(sorted({s.level for s in usable}))
    start, _why = start_level(TaskFeatures(), ladder, track=track)
    above = [level for level in ladder.levels if level > start]
    report = PolicyReport(
        workers=[s.id for s in specs],
        remote=[s.id for s in specs if not s.local],
        start_level=start,
        escalated_level=above[0] if above else None,
    )
    for rule in unmatched_pins(rules, specs):
        report.problems.append(
            Problem(
                "error",
                f"rule {rule.name} sends steps to no configured worker"
                f" ({describe_selector(rule.to or {})}); the router skips it at every step, so"
                " its steps go to the next matching rule. Add the model to an endpoint's"
                " `models`, or fix the selector.",
            )
        )
    for spec in specs:
        if not spec.local and spec.prices is None:
            report.problems.append(
                Problem(
                    "warning",
                    f"{spec.id} is remote and has no prices, so its calls show no dollars and a"
                    " dollar budget cannot stop it.",
                )
            )
    if report.remote and budget_usd is None:
        report.problems.append(
            Problem(
                "warning",
                "remote workers are configured but no dollar budget is set ([budgets] usd).",
            )
        )
    features = TaskFeatures()
    for step_type in STEP_TYPES:
        decisions: list[Decision | None] = []
        for escalations, level in ((0, start), (1, report.escalated_level)):
            if level is None:
                decisions.append(None)
                continue
            state = RouterState(
                step=1, level=level, allow_remote=allow_remote, track=track, escalations=escalations
            )
            decisions.append(route(features, step_type, state, specs, rules))
        first, later = decisions
        if first is None or first.chosen is None:
            report.problems.append(
                Problem("error", f"no configured worker can take {step_type} steps.")
            )
        report.routes.append(
            StepRoute(
                step_type=step_type,
                first=first.chosen if first else None,
                first_rule=first.rule if first else None,
                escalated=later.chosen if later else None,
                escalated_rule=later.rule if later else None,
            )
        )
    return report


def render(report: PolicyReport) -> list[str]:
    """The report as text lines for the terminal."""
    lines = [f"Workers: {len(report.workers)} ({len(report.remote)} remote)", ""]
    for r in report.routes:
        lines.append(f"{r.step_type:11} {_cell(r.first, r.first_rule)}")
        if report.escalated_level is None:
            continue
        if (r.escalated, r.escalated_rule) == (r.first, r.first_rule):
            lines.append(f"{'':11} after an escalation: the same")
        else:
            lines.append(f"{'':11} after an escalation: {_cell(r.escalated, r.escalated_rule)}")
    lines.append("")
    if not report.problems:
        lines.append("No problems found.")
    for problem in report.problems:
        lines.append(f"{problem.severity}: {problem.message}")
    return lines


def _cell(worker: str | None, rule: str | None) -> str:
    if worker is None:
        return "nobody"
    return f"{worker}, rule {rule}" if rule else f"{worker}, chosen by score"

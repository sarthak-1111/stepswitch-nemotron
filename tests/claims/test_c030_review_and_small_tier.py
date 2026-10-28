"""C-030: on the C-029 runs, the cross-family second opinion and the small tier's steps.

Proof: bench evidence (ADR 0044), from the step records (`steps.jsonl`) of the C-029 runs.

Reviews. In the ladder, Nemotron 3 Ultra reviews each change that passed the gates, and a model
from another family (`second`) gives a second opinion on the same change. For every task run
with both, the evidence records the two verdicts and whether they agree. Reviews run only after
the gates pass, so every reviewed change had passed the project's tests: the agreement is
agreement on changes that pass their tests, and the evidence says so.

Small tier. The ladder sends some step types to the small tier (`small`). For each of those
types (`small_step_types`), the small tier's calls in the ladder are compared with Ultra
alone's calls of the same step type on the same tasks: model calls, tool calls, tool calls that
returned an error, calls cut off at the output limit, and dollars per call. The small tier
handles a step type as well as Ultra when its share of tool errors and its share of cut-off
calls are no larger than Ultra's; the claim also needs its dollars per call under
`max_usd_per_call_percent` of Ultra's. Every step type both ran is in the evidence, the ones
the claim does not name included.

The evidence also reports the small tier alone on the same suites (`alone_runs`), if those runs
exist: task runs passed, dollars and tokens per task run. They are reported, not claimed.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pytest

from tests.claims import evidence
from tests.claims.bench_runs import RESULTS, Run, read_jsonl, runs, tokens

pytestmark = [pytest.mark.claim("C-030")]

LADDER = "router"


def steps_of(run: Run) -> dict[tuple[str, str, int], list[dict[str, Any]]]:
    by: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in read_jsonl(RESULTS / run.name / "steps.jsonl"):
        by[(str(record["contestant"]), str(record["task"]), int(record["seed"]))].append(record)
    for records in by.values():
        records.sort(key=lambda r: int(r["seq"]))
    return by


def review_pairs(events: list[dict[str, Any]], second: str) -> list[dict[str, Any]]:
    """Each second opinion with the first review it followed."""
    pairs = []
    first = None
    for event in events:
        if event["type"] != "review":
            continue
        if not event.get("second_opinion"):
            first = event
        elif event.get("reviewer") == second and first is not None:
            pairs.append(
                {
                    "first": {"reviewer": first["reviewer"], "approved": first.get("approved")},
                    "second": {"reviewer": event["reviewer"], "approved": event.get("approved")},
                    "agrees": bool(first.get("approved")) == bool(event.get("approved")),
                }
            )
    return pairs


def call_stats(
    events: list[dict[str, Any]], worker: str, totals: dict[str, dict[str, float]]
) -> None:
    """Add one task run's calls by `worker` to per-step-type totals."""
    step_type: dict[int, str] = {}
    for event in events:
        if event["type"] == "step" and event.get("worker") == worker:
            step_type[int(event["step"])] = str(event["step_type"])
            t = totals[str(event["step_type"])]
            usage = event.get("usage") or {}
            t["calls"] += 1
            t["tokens"] += int(usage.get("input_tokens") or 0) + int(
                usage.get("output_tokens") or 0
            )
            t["cost_usd"] += float(event.get("cost_usd") or 0.0)
            t["cut_off"] += event.get("finish_reason") == "length"
        elif event["type"] == "tool" and int(event["step"]) in step_type:
            t = totals[step_type[int(event["step"])]]
            t["tool_calls"] += 1
            t["tool_errors"] += bool(event.get("is_error"))


def summary(t: dict[str, float]) -> dict[str, Any]:
    calls, tools = int(t["calls"]), int(t["tool_calls"])
    return {
        "calls": calls,
        "tool_calls": tools,
        "tool_errors": int(t["tool_errors"]),
        "tool_error_percent": round(100.0 * t["tool_errors"] / tools, 1) if tools else 0.0,
        "cut_off": int(t["cut_off"]),
        "cut_off_percent": round(100.0 * t["cut_off"] / calls, 1) if calls else 0.0,
        "tokens_per_call": round(t["tokens"] / calls) if calls else None,
        "usd_per_call": round(t["cost_usd"] / calls, 6) if calls else None,
    }


def alone(found: list[Run], names: list[str], worker: str) -> dict[str, Any]:
    by_name = {run.name: run for run in found}
    out: dict[str, Any] = {}
    for name in names:
        run = by_name.get(name)
        if run is None:
            continue
        rows = [r for r in run.rows if r.get("contestant") == worker]
        n = len(rows)
        dollars = sum(float(r.get("cost_usd") or 0.0) for r in rows)
        out[run.suite] = {
            "run": name,
            "task_runs": n,
            "passed": sum(1 for r in rows if r.get("passed")),
            "cost_per_task_usd": round(dollars / n, 6) if n else None,
            "tokens_per_task": round(sum(tokens(r) for r in rows) / n) if n else None,
            "stopped": run.meta.get("stopped"),
        }
    return out


def test_the_second_opinion_agrees_and_the_small_tier_keeps_up() -> None:
    limits = evidence.thresholds("C-030")
    single, small, second = str(limits["single"]), str(limits["small"]), str(limits["second"])
    small_types = [str(t) for t in limits["small_step_types"]]
    found = runs()
    by_name = {run.name: run for run in found}
    missing = [name for name in limits["runs"] if name not in by_name]
    assert not missing, f"bench runs not found under bench/results: {missing}"

    pairs: list[dict[str, Any]] = []
    ladder_small: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    ultra_alone: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    problems: list[str] = []
    for name in limits["runs"]:
        run = by_name[name]
        by = steps_of(run)
        if not by:
            problems.append(f"{name}: no step records (steps.jsonl)")
        shared = {(t, s) for (c, t, s) in by if c == LADDER} & {
            (t, s) for (c, t, s) in by if c == single
        }
        for task, seed in sorted(shared):
            ladder_events = by[(LADDER, task, seed)]
            for pair in review_pairs(ladder_events, second):
                pairs.append({"suite": run.suite, "task": task, "seed": seed, **pair})
            call_stats(ladder_events, small, ladder_small)
            call_stats(by[(single, task, seed)], single, ultra_alone)

    agreeing = sum(1 for p in pairs if p["agrees"])
    reviews = {
        "first_reviewer": single,
        "second_reviewer": second,
        "changes": len(pairs),
        "agreeing": agreeing,
        "agreement_percent": round(100.0 * agreeing / len(pairs), 1) if pairs else None,
        "both_approved": sum(
            1 for p in pairs if p["first"]["approved"] and p["second"]["approved"]
        ),
        "both_blocked": sum(
            1 for p in pairs if not p["first"]["approved"] and not p["second"]["approved"]
        ),
        "note": "reviews run after the gates pass, so every reviewed change passed its tests",
        "pairs": pairs,
    }
    if len(pairs) < int(limits["min_changes"]):
        problems.append(
            f"{len(pairs)} changes had both reviews, fewer than {limits['min_changes']}"
        )
    if pairs and 100.0 * agreeing / len(pairs) < float(limits["min_agreement_percent"]):
        problems.append(f"the reviewers agreed on {agreeing} of {len(pairs)} changes")

    step_types: dict[str, Any] = {}
    for step_type in sorted(set(ladder_small) | set(ultra_alone)):
        mine, theirs = summary(ladder_small[step_type]), summary(ultra_alone[step_type])
        entry: dict[str, Any] = {"small": mine, "single": theirs}
        if mine["calls"] and theirs["calls"] and mine["usd_per_call"] is not None:
            share = (
                mine["usd_per_call"] / theirs["usd_per_call"] if theirs["usd_per_call"] else None
            )
            entry["usd_per_call_percent_of_single"] = (
                round(100.0 * share, 1) if share is not None else None
            )
            entry["as_well"] = (
                mine["tool_error_percent"] <= theirs["tool_error_percent"]
                and mine["cut_off_percent"] <= theirs["cut_off_percent"]
            )
        step_types[step_type] = entry
    price_cap = float(limits["max_usd_per_call_percent"])
    for step_type in small_types:
        entry = step_types.get(step_type, {})
        if not entry.get("small", {}).get("calls"):
            problems.append(f"the small tier ran no {step_type} step")
        elif not entry.get("as_well"):
            problems.append(f"{step_type}: the small tier had more tool errors or cut-offs")
        elif (entry.get("usd_per_call_percent_of_single") or 100.0) >= price_cap:
            problems.append(
                f"{step_type}: the small tier's dollars per call are not under"
                f" {price_cap}% of Ultra's"
            )

    evidence.write(
        "C-030",
        "steps",
        {
            "runs": list(limits["runs"]),
            "reviews": reviews,
            "small_tier": {"worker": small, "single": single, "step_types": step_types},
            "small_tier_alone": alone(found, list(limits.get("alone_runs") or []), small),
            "problems": problems,
            # How the runs were made; `command` is the prove command that checks them (C-018).
            "bench_command": "the C-029 runs and the small tier alone (`ssw bench run --workers"
            " <small> --allow-remote --policy bench/policies/tokenfactory-ladder.toml`, each"
            " run.json records its command)",
        },
    )
    assert not problems, problems

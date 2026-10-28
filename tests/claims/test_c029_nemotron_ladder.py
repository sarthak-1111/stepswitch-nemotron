"""C-029: on the mini suites, the Nemotron ladder on Token Factory against Nemotron 3 Ultra alone.

Proof: bench evidence (ADR 0044). The runs are named in the claim's thresholds (`runs`), one
per mini suite, each with the `router` contestant routing among the Token Factory pool with the
ladder policy (`bench/policies/tokenfactory-ladder.toml`, recorded in `run.json`) and Ultra
alone as a pinned contestant, on the same tasks and seeds, interleaved, under a dollar cap.

The comparison uses the task runs both contestants have; a task run where either side hit an
infrastructure error is left out for both and listed. For each contestant it reports the task
runs passed, dollars per task run (the ledger's cost at the workers' list prices), tokens per
task run (input with cached tokens included, plus output), uncached tokens, minutes per task
run and escalations. The ladder's dollars as a share of Ultra's carry a 95% cluster-bootstrap
interval over tasks (`stepswitch.bench.metrics.bootstrap_ratio_ci`).

The claim holds when the ladder passes at least as many task runs as Ultra alone and its
dollars' share of Ultra's, with its whole interval, lies below `cost_share_max`.

The evidence also carries the bill: the dollars every hosted bench run recorded, the stopped
and calibration runs included, so the cost of producing the claim is part of it, with the
provider console's reading next to it when `hackathon/bill.json` holds one. It also gives the
list prices the runs recorded and how the ladder's dollars split across its models.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from stepswitch.bench import metrics
from tests.claims import evidence
from tests.claims.bench_runs import ROOT, Run, runs, tokens

pytestmark = [pytest.mark.claim("C-029")]

LADDER = "router"
# The provider console's reading of the bill, entered by hand with the date it was read.
CONSOLE_BILL = ROOT / "hackathon" / "bill.json"
Key = tuple[str, str, int]
# How the runs are made; each run's run.json records its own command.
BENCH_COMMAND = (
    "uv run ssw bench run --suite <suite> --workers router,<ultra> --router-pool <pool>"
    " --allow-remote --policy bench/policies/tokenfactory-ladder.toml --interleave"
    " --budget-usd 0.5 --budget-usd-total <cap> (each run's run.json records its command)"
)


def uncached(row: dict[str, Any]) -> int:
    counts = row.get("tokens") or {}
    used = int(counts.get("input") or 0) - int(counts.get("cached_input") or 0)
    return max(0, used) + int(counts.get("output") or 0)


def cost(row: dict[str, Any]) -> float:
    """A row's dollars; runs from before rows carried `cost_usd` add up their models' costs."""
    if row.get("cost_usd") is not None:
        return float(row["cost_usd"])
    return sum(float(m.get("cost_usd") or 0.0) for m in (row.get("models") or {}).values())


def side(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    passed = sum(1 for r in rows if r.get("passed"))
    dollars = sum(cost(r) for r in rows)
    return {
        "runs": n,
        "passed": passed,
        "pass_rate_percent": round(100.0 * passed / n, 1) if n else None,
        "cost_usd": round(dollars, 6),
        "cost_per_task_usd": round(dollars / n, 6) if n else None,
        "tokens_per_task": round(sum(tokens(r) for r in rows) / n) if n else None,
        "uncached_tokens_per_task": round(sum(uncached(r) for r in rows) / n) if n else None,
        "minutes_per_task": round(sum(float(r.get("wall_seconds") or 0) for r in rows) / n / 60, 2)
        if n
        else None,
        "escalations": sum(int(r.get("escalations") or 0) for r in rows),
        "steps_per_task": round(sum(int(r.get("steps") or 0) for r in rows) / n, 1) if n else None,
    }


def key(worker: str) -> str:
    """An evidence key for a worker: its model name with every other character as `_`."""
    return re.sub(r"[^A-Za-z0-9]", "_", worker.rsplit("/", 1)[-1])


def bill(found: list[Run]) -> dict[str, Any]:
    """Dollars of every bench run that allowed hosted models, from its rows (the ledger), and
    the provider console's reading when `hackathon/bill.json` records one."""
    per_run = {}
    for run in found:
        if not run.meta.get("allow_remote") and not any(cost(r) for r in run.rows):
            continue
        per_run[run.name] = {
            "suite": run.suite,
            "task_runs": len(run.rows),
            "cost_usd": round(sum(cost(r) for r in run.rows), 6),
            "stopped": run.meta.get("stopped"),
        }
    total = round(sum(entry["cost_usd"] for entry in per_run.values()), 6)
    out: dict[str, Any] = {
        "runs": per_run,
        "total_usd": total,
        "source": "result rows (Stepswitch's ledger)",
    }
    if CONSOLE_BILL.is_file():
        out["console"] = json.loads(CONSOLE_BILL.read_text(encoding="utf-8"))
    return out


def by_model(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Where the ladder's dollars went: calls and dollars per model, and each model's share."""
    totals: dict[str, dict[str, float]] = {}
    for row in rows:
        for worker, counts in (row.get("models") or {}).items():
            t = totals.setdefault(worker, {"calls": 0, "cost_usd": 0.0})
            t["calls"] += int(counts.get("calls") or 0)
            t["cost_usd"] += float(counts.get("cost_usd") or 0.0)
    whole = sum(t["cost_usd"] for t in totals.values())
    return {
        key(worker): {
            "worker": worker,
            "calls": int(t["calls"]),
            "cost_usd": round(t["cost_usd"], 6),
            "percent": round(100.0 * t["cost_usd"] / whole, 1) if whole else None,
        }
        for worker, t in sorted(totals.items())
    }


def prices(found: list[Run], names: list[str]) -> dict[str, Any]:
    """List prices per million tokens that the runs recorded, for the models they used."""
    out: dict[str, Any] = {}
    for run in found:
        if run.name in names:
            used = set(run.meta.get("router_pool") or []) | set(run.meta.get("contestants") or [])
            for worker, price in (run.meta.get("worker_prices") or {}).items():
                if worker in used:
                    out.setdefault(key(worker), {"worker": worker, **price})
    return out


def compare(claim_id: str) -> tuple[dict[str, Any], list[str]]:
    """The ladder against the single model on the runs a claim names in its thresholds: the
    evidence section and the problems that keep the claim from holding (C-029, and C-032,
    its replication)."""
    limits = evidence.thresholds(claim_id)
    confidence = float(limits["confidence_level"])
    single = str(limits["single"])
    found = runs()
    by_name = {run.name: run for run in found}
    missing = [name for name in limits["runs"] if name not in by_name]
    assert not missing, f"bench runs not found under bench/results: {missing}"

    rows: dict[str, list[dict[str, Any]]] = {LADDER: [], single: []}
    excluded: list[str] = []
    clusters: dict[str, list[float]] = {}
    per_suite: dict[str, Any] = {}
    problems: list[str] = []
    for name in limits["runs"]:
        run = by_name[name]
        meta = run.meta
        if not meta.get("allow_remote") or set(meta.get("contestants", [])) != {LADDER, single}:
            problems.append(f"{name}: not a hosted run of the ladder against {single}")
        by: dict[str, dict[Key, dict[str, Any]]] = {LADDER: {}, single: {}}
        for row in run.rows:
            if row.get("contestant") in by:
                by[row["contestant"]][(run.suite, str(row["task"]), int(row["seed"]))] = row
        shared = sorted(set(by[LADDER]) & set(by[single]))
        kept = []
        for key in shared:
            if by[LADDER][key].get("infra_error") or by[single][key].get("infra_error"):
                excluded.append(f"{key[0]}/{key[1]} s{key[2]}")
                continue
            kept.append(key)
        suite_rows = {c: [by[c][k] for k in kept] for c in by}
        per_suite[run.suite] = {
            "run": name,
            "commit": meta.get("commit"),
            "task_runs": len(kept),
            "stopped": meta.get("stopped"),
            "results": {"ladder": side(suite_rows[LADDER]), "single": side(suite_rows[single])},
        }
        for c in by:
            rows[c] += suite_rows[c]
        for key in kept:
            cluster = clusters.setdefault(f"{key[0]}/{key[1]}", [0.0, 0.0])
            cluster[0] += cost(by[LADDER][key])
            cluster[1] += cost(by[single][key])

    ladder, ultra = side(rows[LADDER]), side(rows[single])
    pairs = [(a, b) for a, b in clusters.values()]
    share = metrics.bootstrap_ratio_ci(pairs, confidence=confidence)
    point = ladder["cost_usd"] / ultra["cost_usd"] if ultra["cost_usd"] else None
    cost_share = {
        "percent": round(100.0 * point, 1) if point is not None else None,
        "saving_percent": round(100.0 * (1.0 - point), 1) if point is not None else None,
        "interval": {
            "low": round(100.0 * share.low, 1),
            "high": round(100.0 * share.high, 1),
            "confidence": confidence,
            "method": share.method,
            "tasks": len(pairs),
        },
    }
    if ladder["passed"] < ultra["passed"]:
        problems.append(f"the ladder passed {ladder['passed']}, Ultra alone {ultra['passed']}")
    if point is None or share.high * 100.0 >= float(limits["cost_share_max_percent"]):
        problems.append(
            f"the ladder's dollars are {cost_share['percent']}% of Ultra's, interval"
            f" up to {cost_share['interval']['high']}%"
        )
    if len(excluded) > float(limits["max_excluded_share"]) * max(1, len(clusters) + len(excluded)):
        problems.append(f"{len(excluded)} task runs left out for infrastructure errors")

    data = {
        "contestants": {"ladder": LADDER, "single": single},
        "task_runs": len(rows[LADDER]),
        "tasks": len(clusters),
        "excluded": excluded,
        "results": {"ladder": ladder, "single": ultra},
        "cost_share": cost_share,
        "ladder_dollars_by_model": by_model(rows[LADDER]),
        "prices_per_million": prices(found, list(limits["runs"])),
        "per_suite": per_suite,
        "bill": bill(found),
        "problems": problems,
        # How the runs were made; `command` is the prove command that checks them (C-018).
        "bench_command": BENCH_COMMAND,
    }
    return data, problems


def test_the_ladder_passes_as_many_tasks_as_ultra_for_less() -> None:
    data, problems = compare("C-029")
    evidence.write("C-029", "comparison", data)
    assert not problems, problems

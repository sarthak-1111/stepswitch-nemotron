"""Build the demo's data from committed bench runs: `hackathon/demo/site/data.json`.

The demo is a static, read-only page (no login, no key, no model calls). It replays recorded
Token Factory runs step by step from each run's `steps.jsonl` (model, tokens, dollars, gates,
reviews, escalations) and shows the results tables from `results.jsonl`. Nothing here calls a
model; the numbers are the recorded ones.

    uv run python hackathon/demo/build.py          # writes site/data.json
    uv run python hackathon/demo/build.py --check  # fails when data.json is out of date
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "bench" / "results"
OUT = Path(__file__).resolve().parent / "site" / "data.json"

# The runs the demo shows, with their kind: the C-029 runs of both mini suites ("main"),
# Lightning alone on the same tasks ("alone"), the escalation demo ("demo"), the pilot, and
# the exploratory ladder with the work steps starting on Lightning ("explore").
RUNS = (
    ("2026-10-28-tf-mini-general", "main"),
    ("2026-10-28-tf-mini-science", "main"),
    ("2026-10-28-tf-escalation-demo-nano", "demo"),
    ("2026-10-29-tf-mini-general-lightning-first", "explore"),
    ("2026-10-29-tf-mini-science-lightning-first", "explore"),
    ("2026-10-28-tf-mini-general-lightning", "alone"),
    ("2026-10-28-tf-mini-science-lightning", "alone"),
    ("2026-10-28-tf-pilot", "pilot"),
)
ROW_KEYS = (
    "task",
    "seed",
    "contestant",
    "passed",
    "status",
    "stop_reason",
    "steps",
    "switches",
    "escalations",
    "tokens",
    "cost_usd",
    "wall_seconds",
    "tags",
)
STEP_KEYS = (
    "seq",
    "type",
    "step",
    "step_type",
    "chosen",
    "rule",
    "switched",
    "worker",
    "tool_calls",
    "effort",
    "finish_reason",
    "usage",
    "cost_usd",
    "wall_seconds",
    "name",
    "is_error",
    "changed_files",
    "run",
    "passed",
    "failed_gate",
    "results",
    "reviewer",
    "reviewer_family",
    "approved",
    "failed",
    "issues",
    "cross_family",
    "second_opinion",
    "agrees",
    "from",
    "to",
    "from_level",
    "to_level",
    "reason",
    "status",
    "stop_reason",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def model_cost(row: dict[str, Any]) -> float | None:
    """A row's dollars: `cost_usd`, or the sum over its models for runs from before the row
    carried it (the pilot)."""
    if row.get("cost_usd") is not None:
        return float(row["cost_usd"])
    costs = [m.get("cost_usd") for m in (row.get("models") or {}).values()]
    return round(sum(float(c) for c in costs if c is not None), 6) if any(costs) else None


def load_run(name: str, kind: str) -> dict[str, Any] | None:
    folder = RESULTS / name
    meta_path = folder / "run.json"
    if not meta_path.is_file():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    rows = []
    for row in read_jsonl(folder / "results.jsonl"):
        kept = {key: row.get(key) for key in ROW_KEYS}
        kept["cost_usd"] = model_cost(row)
        kept["models"] = {
            worker: {
                k: v for k, v in counts.items() if k in ("calls", "input", "output", "cost_usd")
            }
            for worker, counts in (row.get("models") or {}).items()
        }
        rows.append(kept)
    steps: dict[str, list[dict[str, Any]]] = {}
    for record in read_jsonl(folder / "steps.jsonl"):
        key = f"{record['contestant']}|{record['task']}|{record['seed']}"
        steps.setdefault(key, []).append({k: record[k] for k in STEP_KEYS if k in record})
    return {
        "name": name,
        "suite": meta.get("suite"),
        "started": meta.get("started"),
        "finished": meta.get("finished"),
        "commit": meta.get("commit"),
        "command": meta.get("command"),
        "contestants": meta.get("contestants"),
        "router_pool": meta.get("router_pool"),
        "policy": meta.get("policy"),
        "worker_prices": meta.get("worker_prices"),
        "budget_usd_total": meta.get("budget_usd_total"),
        "spent_usd": meta.get("spent_usd"),
        "stopped": meta.get("stopped"),
        "kind": kind,
        "rows": rows,
        "steps": steps,
    }


def build() -> dict[str, Any]:
    runs = [run for run in (load_run(name, kind) for name, kind in RUNS) if run is not None]
    evidence = {}
    # C-032 is the withdrawn replication of C-029; the page shows it with its registered bound.
    for claim in ("C-029", "C-030", "C-032"):
        path = ROOT / "claims" / "evidence" / f"{claim}.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            evidence[claim] = {
                "text": data.get("text"),
                "thresholds": data.get("thresholds"),
                "sections": data.get("sections"),
            }
    return {"schema": 1, "runs": runs, "evidence": evidence}


def main() -> int:
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if current != text:
            print(f"{OUT.relative_to(ROOT)} is out of date: run hackathon/demo/build.py")
            return 1
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text) // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Hosted providers, per-model prices and the dollar cost of each call (ADR 0044)."""

from __future__ import annotations

from pathlib import Path

import pytest

from stepswitch import providers
from stepswitch.config import Config, EndpointConfig
from stepswitch.core.budget import BudgetTracker
from stepswitch.core.task import Budgets
from stepswitch.ledger import Ledger, LedgerRow, by_worker, task_totals
from stepswitch.pricing import Prices, prices_from_table, row_cost
from stepswitch.state import open_project_state
from stepswitch.workers.catalog import Catalog

LADDER = (
    "nvidia/Nemotron-3_5-Lightning",
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/Nemotron-3-Ultra-550b-a55b",
)
PROVIDER = """\
schema = 1

[provider]
id = "acme"
title = "Acme Models"
url = "https://models.example.invalid/v1"
api_key_env = "ACME_KEY"
default_models = ["small", "big"]

[models.small]
family = "fam"
tier = "t1"
price_input = 0.1
price_cached_input = 0.05
price_output = 0.4

[models.big]
family = "fam"
tier = "remote"
roles = ["planner"]
price_input = 1.0
price_output = 3.0
"""


def test_cost_bills_cached_input_at_its_own_price() -> None:
    prices = Prices(input=1.0, output=3.0, cached_input=0.12)
    cost = prices.cost(input_tokens=1_000_000, cached_input_tokens=750_000, output_tokens=100_000)
    assert cost == pytest.approx(0.25 + 0.09 + 0.3)
    # Without a cached price every input token is billed at the input price.
    plain = Prices(input=1.0, output=3.0)
    assert plain.cost(
        input_tokens=1_000_000, cached_input_tokens=750_000, output_tokens=0
    ) == pytest.approx(1.0)
    # A server reporting more cached than input tokens is clamped, never negative.
    assert prices.cost(input_tokens=10, cached_input_tokens=50, output_tokens=0) == pytest.approx(
        10 * 0.12 / 1e6
    )


def test_prices_need_input_and_output() -> None:
    assert prices_from_table({"price_input": 0.3, "price_output": 0.9}) == Prices(0.3, 0.9, None)
    assert prices_from_table({"price_input": 0.3}) is None
    assert prices_from_table({"price_input": -1, "price_output": 0.9}) is None
    assert prices_from_table({"price_input": True, "price_output": 0.9}) is None
    assert prices_from_table(None) is None
    assert row_cost(None, {"input_tokens": 5}) is None
    fields = {"input_tokens": 1000, "cached_input_tokens": 0, "output_tokens": 1000}
    assert row_cost(Prices(1.0, 3.0), fields) == 0.004


def test_the_packaged_token_factory_provider_has_the_nemotron_ladder() -> None:
    provider = providers.get("tokenfactory")
    assert provider is not None
    assert provider.url.startswith("https://") and provider.api_key_env
    for model in LADDER:
        table = provider.model_table(model)
        assert table["family"] == "nemotron", model
        assert prices_from_table(table) is not None, model
    tiers = [provider.model_table(m)["tier"] for m in LADDER]
    assert tiers == ["t1", "t3", "remote"]
    reviewer = provider.model_table("openai/gpt-oss-120b")
    assert reviewer["family"] != "nemotron" and "reviewer" in reviewer["roles"]
    assert set(LADDER) <= set(provider.default_models)


def test_a_preset_fills_the_endpoint_and_the_endpoint_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "acme.toml").write_text(PROVIDER, encoding="utf-8")
    monkeypatch.setattr(providers, "provider_dirs", lambda: [tmp_path])
    endpoint = EndpointConfig.model_validate({"name": "acme", "preset": "acme"})
    assert endpoint.url == "https://models.example.invalid/v1"
    assert endpoint.auth == "bearer" and endpoint.api_key_env == "ACME_KEY"
    assert endpoint.models == ["small", "big"] and not endpoint.is_local()
    mine = EndpointConfig.model_validate({"name": "acme", "preset": "acme", "models": ["big"]})
    assert mine.models == ["big"]
    with pytest.raises(ValueError, match="unknown provider preset"):
        EndpointConfig.model_validate({"name": "x", "preset": "nope"})


def test_catalog_takes_tiers_and_prices_from_the_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "acme.toml").write_text(PROVIDER, encoding="utf-8")
    monkeypatch.setattr(providers, "provider_dirs", lambda: [tmp_path])
    config = Config.model_validate(
        {
            "endpoints": [{"name": "acme", "preset": "acme"}],
            # The user's table wins over the provider's.
            "models": {"big": {"price_output": 2.0}},
        }
    )
    catalog = Catalog.from_config(config, tmp_path, include_managed=False)
    small, big = catalog.get("acme/small").spec, catalog.get("acme/big").spec
    assert (small.tier, small.level, small.family) == ("t1", 1, "fam")
    assert (big.tier, big.level, big.roles) == ("remote", 3, ("planner",))
    assert small.prices == Prices(input=0.1, output=0.4, cached_input=0.05)
    assert big.prices == Prices(input=1.0, output=2.0, cached_input=None)
    assert small.as_dict()["prices"]["cached_input_per_million"] == 0.05
    # The same URL without the preset gets the provider's facts too.
    by_url = Config.model_validate(
        {
            "endpoints": [
                {"name": "x", "url": "https://models.example.invalid/v1/", "models": ["small"]}
            ]
        }
    )
    spec = Catalog.from_config(by_url, tmp_path, include_managed=False).get("x/small").spec
    assert spec.tier == "t1" and spec.prices is not None


def test_ledger_rows_carry_their_cost(tmp_path: Path) -> None:
    db = open_project_state(tmp_path)
    ledger = Ledger(db, "t1")
    for step, cost in ((1, 0.25), (2, None), (3, 0.5)):
        ledger.record(
            LedgerRow(
                task_id="t1",
                step=step,
                step_type="edit",
                endpoint="e",
                model="m" if cost is not None else "local",
                input_tokens=10,
                output_tokens=1,
                cost_usd=cost,
            )
        )
    db.close()
    totals = task_totals(tmp_path, "t1")
    assert totals["cost_usd"] == 0.75 and totals["priced_calls"] == 2 and totals["calls"] == 3
    assert ledger.totals() == totals
    workers = by_worker(ledger.rows)
    assert workers[("e", "m")]["cost_usd"] == 0.75 and "cost_usd" not in workers[("e", "local")]


def test_a_dollar_budget_stops_the_task() -> None:
    tracker = BudgetTracker(Budgets(usd=0.01))
    tracker.charge(tokens=10, usd=0.004)
    assert tracker.exceeded() is None and tracker.remaining()["usd"] == 0.006
    tracker.charge(usd=0.007)
    assert tracker.exceeded() == "budget_usd"
    assert BudgetTracker(Budgets()).remaining()["usd"] is None

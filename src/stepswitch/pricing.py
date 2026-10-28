"""Per-model prices and the dollar cost of a model call (ADR 0044).

Prices are US dollars per million tokens: uncached input, cached input and output. A hosted
service bills input tokens that its prompt cache served at the cached price and the rest at the
input price; output tokens (reasoning included) at the output price. A model without a cached
price bills every input token at the input price. Local models have no price, so their calls
cost nothing in dollars and their rows carry no cost.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

PRICE_KEYS = ("price_input", "price_cached_input", "price_output")


@dataclass(frozen=True)
class Prices:
    """US dollars per million tokens."""

    input: float
    output: float
    cached_input: float | None = None

    def cost(self, *, input_tokens: int, cached_input_tokens: int, output_tokens: int) -> float:
        """The dollar cost of one call. `input_tokens` includes the cached ones."""
        cached = max(0, min(int(cached_input_tokens or 0), int(input_tokens or 0)))
        uncached = max(0, int(input_tokens or 0) - cached)
        cached_price = self.input if self.cached_input is None else self.cached_input
        total = uncached * self.input + cached * cached_price + max(0, output_tokens) * self.output
        return total / 1e6

    def as_dict(self) -> dict[str, float | None]:
        return {
            "input_per_million": self.input,
            "cached_input_per_million": self.cached_input,
            "output_per_million": self.output,
        }


def _price(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if value >= 0 else None


def prices_from_table(table: Mapping[str, Any] | None) -> Prices | None:
    """Prices from a `[models."<name>"]` table or a provider's model table: `price_input` and
    `price_output` are both needed; `price_cached_input` is optional."""
    if not table:
        return None
    price_in, price_out = _price(table.get("price_input")), _price(table.get("price_output"))
    if price_in is None or price_out is None:
        return None
    return Prices(
        input=price_in, output=price_out, cached_input=_price(table.get("price_cached_input"))
    )


def row_cost(prices: Prices | None, fields: Mapping[str, Any]) -> float | None:
    """The cost of a ledger row's token columns, rounded to a millionth of a dollar."""
    if prices is None:
        return None
    return round(
        prices.cost(
            input_tokens=int(fields.get("input_tokens") or 0),
            cached_input_tokens=int(fields.get("cached_input_tokens") or 0),
            output_tokens=int(fields.get("output_tokens") or 0),
        ),
        6,
    )

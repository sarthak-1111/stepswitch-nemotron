"""Hosted providers: shared presets for hosted model services (ADR 0044).

A provider file, `registry/providers/<id>.toml`, holds what every user of one hosted service
would otherwise copy into `.stepswitch/local.toml` by hand: its URL, API format and
authentication, the models it serves with their place on the ladder (tier, family, roles) and
their prices. An endpoint uses it with `preset = "<id>"`; an endpoint whose URL is the
provider's gets the model facts too. Whatever the endpoint or a `[models."<name>"]` table sets
itself wins. Provider files are data, checked by date, like the rest of the registry: a model
that is not listed still works, with the facts the catalog derives for any hosted model.
"""

from __future__ import annotations

import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from stepswitch import paths

PROVIDERS_SUBDIR = "providers"


class Provider(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    url: str
    format: str = "chat-completions"
    auth: str = "bearer"
    api_key_env: str | None = None
    # The models an endpoint with this preset serves when it lists none itself.
    default_models: list[str] = Field(default_factory=list)
    # Per model: the keys of a `[models."<name>"]` table (tier, family, roles, context,
    # reasoning, tool_calls) plus prices (`price_input`, `price_cached_input`, `price_output`).
    models: dict[str, dict[str, Any]] = Field(default_factory=dict)
    currency: str = "USD"
    prices_checked: str | None = None
    prices_source: str | None = None
    notes: str | None = None
    source_path: Path | None = Field(default=None, exclude=True)

    def endpoint_defaults(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {"url": self.url, "format": self.format, "auth": self.auth}
        if self.api_key_env:
            defaults["api_key_env"] = self.api_key_env
        if self.default_models:
            defaults["models"] = list(self.default_models)
        return defaults

    def model_table(self, model: str) -> dict[str, Any]:
        table = self.models.get(model)
        if table is None:
            lowered = model.lower()
            table = next((t for name, t in self.models.items() if name.lower() == lowered), None)
        return dict(table or {})


def provider_dirs() -> list[Path]:
    """Packaged providers first, then the user's registry, which overrides them by id."""
    dirs = [
        d / PROVIDERS_SUBDIR
        for d in (paths.packaged_registry_dir(), paths.user_registry_dir())
        if d is not None
    ]
    return [d for d in dirs if d.is_dir()]


def read_provider(path: Path) -> Provider:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    provider = Provider.model_validate(
        {**dict(data.get("provider", {})), "models": data.get("models", {})}
    )
    provider.source_path = path
    return provider


def load(dirs: Iterable[Path] | None = None) -> dict[str, Provider]:
    providers: dict[str, Provider] = {}
    for directory in provider_dirs() if dirs is None else dirs:
        for path in sorted(directory.glob("*.toml")):
            provider = read_provider(path)
            providers[provider.id] = provider
    return providers


def get(name: str, dirs: Iterable[Path] | None = None) -> Provider | None:
    return load(dirs).get(name)


def _same_url(a: str, b: str) -> bool:
    return a.rstrip("/").lower() == b.rstrip("/").lower()


def for_endpoint(
    preset: str | None, url: str, dirs: Iterable[Path] | None = None
) -> Provider | None:
    """The provider an endpoint names with `preset`, else the one whose URL it uses."""
    providers = load(dirs)
    if preset:
        return providers.get(preset)
    return next((p for p in providers.values() if _same_url(p.url, url)), None)

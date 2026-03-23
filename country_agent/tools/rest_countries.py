from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import httpx

from country_agent.config import settings
from country_agent.models import CountryInfo


class RestCountriesError(Exception):
    """Raised when the REST Countries API call fails unexpectedly."""


def _pick_best_country_match(query: str, payload: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not payload:
        return None

    query_lower = query.strip().lower()
    for entry in payload:
        name_obj = entry.get("name", {})
        common = str(name_obj.get("common", "")).lower()
        official = str(name_obj.get("official", "")).lower()
        if query_lower in {common, official}:
            return entry

    return payload[0]


def _normalize_country(query: str, raw: dict[str, Any] | None) -> CountryInfo:
    if not raw:
        return CountryInfo(query=query, found=False)

    name_obj = raw.get("name", {})
    currencies_raw = raw.get("currencies", {}) or {}
    currencies = {
        code: (meta.get("name") or code)
        for code, meta in currencies_raw.items()
        if isinstance(meta, dict)
    }

    capitals = raw.get("capital") or []
    languages_raw = raw.get("languages") or {}

    return CountryInfo(
        query=query,
        name_common=name_obj.get("common"),
        name_official=name_obj.get("official"),
        capital=capitals[0] if capitals else None,
        population=raw.get("population"),
        currencies=currencies,
        region=raw.get("region"),
        subregion=raw.get("subregion"),
        languages=list(languages_raw.values()),
        flag_emoji=raw.get("flag"),
        found=True,
    )


def fetch_country_info(country_name: str) -> CountryInfo:
    """Fetch country data from REST Countries and normalize it."""
    safe_country_name = quote(country_name.strip(), safe="")
    endpoint = f"{settings.rest_countries_base_url}/name/{safe_country_name}"

    try:
        with httpx.Client(timeout=settings.http_timeout_seconds) as client:
            response = client.get(endpoint, params={"fullText": "true"})
            if response.status_code in {400, 404}:
                response = client.get(endpoint)
            if response.status_code in {400, 404}:
                return CountryInfo(query=country_name, found=False)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise RestCountriesError("Failed to fetch country data") from exc

    if not isinstance(payload, list):
        return CountryInfo(query=country_name, found=False)

    best = _pick_best_country_match(country_name, payload)
    return _normalize_country(country_name, best)

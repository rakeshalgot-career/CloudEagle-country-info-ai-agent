from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    rest_countries_base_url: str = "https://restcountries.com/v3.1"
    http_timeout_seconds: float = 12.0


settings = Settings(
    rest_countries_base_url=os.getenv("REST_COUNTRIES_BASE_URL", "https://restcountries.com/v3.1"),
    http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "12")),
)

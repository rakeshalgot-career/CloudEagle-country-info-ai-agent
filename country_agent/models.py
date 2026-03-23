from __future__ import annotations

from pydantic import BaseModel, Field


class CountryInfo(BaseModel):
    """Normalized country data returned by the REST Countries tool."""

    query: str
    name_common: str | None = None
    name_official: str | None = None
    capital: str | None = None
    population: int | None = None
    currencies: dict[str, str] = Field(default_factory=dict)
    region: str | None = None
    subregion: str | None = None
    languages: list[str] = Field(default_factory=list)
    flag_emoji: str | None = None
    found: bool = False


class AskRequest(BaseModel):
    question: str = Field(min_length=3, description="User question about a country")


class AskResponse(BaseModel):
    answer: str

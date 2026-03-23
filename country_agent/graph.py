from __future__ import annotations

from typing import Any, Literal, TypedDict
import re

from langgraph.graph import END, START, StateGraph

from country_agent.models import CountryInfo
from country_agent.tools.rest_countries import RestCountriesError, fetch_country_info


FieldName = Literal[
    "capital", "population", "currency", "region", "subregion", "languages", "flag"
]


DEFAULT_FIELDS: list[FieldName] = ["capital", "population", "currency"]


class AgentState(TypedDict, total=False):
    question: str
    country_name: str
    requested_fields: list[FieldName]
    country_info: CountryInfo
    answer: str
    error: str | None


FIELD_KEYWORDS: dict[FieldName, tuple[str, ...]] = {
    "capital": ("capital",),
    "population": ("population", "people", "inhabitants"),
    "currency": ("currency", "currencies", "money"),
    "region": ("region",),
    "subregion": ("subregion",),
    "languages": ("language", "languages", "speak"),
    "flag": ("flag",),
}


COUNTRY_PATTERNS = [
    re.compile(r"\b(?:of|in|for)\s+([a-zA-Z .\-']+?)\??$", re.IGNORECASE),
    re.compile(r"\b(?:does|did)\s+([a-zA-Z .\-']+?)\s+use\b", re.IGNORECASE),
    re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\??$"),
]


NON_COUNTRY_WORDS = {
    "capital",
    "population",
    "currency",
    "currencies",
    "region",
    "subregion",
    "language",
    "languages",
    "flag",
    "what",
    "which",
    "tell",
    "about",
    "country",
}


def _normalize_country_candidate(candidate: str) -> str | None:
    normalized = re.sub(r"^the\s+", "", candidate.strip(), flags=re.IGNORECASE).strip(" ?.!,:;")
    if not normalized:
        return None

    if normalized.lower() in NON_COUNTRY_WORDS:
        return None

    return normalized


def _contains_keyword(text: str, keyword: str) -> bool:
    pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
    return pattern.search(text) is not None


def _identify_requested_fields(question: str) -> list[FieldName]:
    fields: list[FieldName] = []

    for field_name, keywords in FIELD_KEYWORDS.items():
        if any(_contains_keyword(question, keyword) for keyword in keywords):
            fields.append(field_name)

    return fields or DEFAULT_FIELDS


def _extract_country_name(question: str) -> str | None:
    cleaned = question.strip()

    for pattern in COUNTRY_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            country = match.group(1)
            normalized = _normalize_country_candidate(country)
            if normalized:
                return normalized

    # Fallback: scan for any capitalized proper-noun candidate in the sentence.
    # This handles phrasing like "What currency does Japan use?" where country
    # is not sentence-final.
    proper_nouns = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", cleaned)
    for candidate in reversed(proper_nouns):
        normalized = _normalize_country_candidate(candidate)
        if normalized:
            return normalized

    tokens = [t.strip(" ?.!,:;") for t in cleaned.split()]
    if tokens:
        return _normalize_country_candidate(tokens[-1])

    return None


def identify_intent(state: AgentState) -> AgentState:
    question = state["question"].strip()
    fields = _identify_requested_fields(question)
    country = _extract_country_name(question)

    if not country:
        return {"requested_fields": fields, "error": "I could not identify a country in your question."}

    return {
        "requested_fields": fields,
        "country_name": country,
        "error": None,
    }


def invoke_country_tool(state: AgentState) -> AgentState:
    if state.get("error"):
        return {}

    country_name = state.get("country_name")
    if not country_name:
        return {"error": "Country is missing from request."}

    try:
        country_info = fetch_country_info(country_name)
    except RestCountriesError:
        return {"error": "Country service is currently unavailable. Please try again."}

    if not country_info.found:
        return {"error": f"I could not find country data for '{country_name}'."}

    return {"country_info": country_info}


def _render_field(field: FieldName, info: CountryInfo) -> str | None:
    if field == "capital" and info.capital:
        return f"Capital: {info.capital}"
    if field == "population" and info.population is not None:
        return f"Population: {info.population:,}"
    if field == "currency" and info.currencies:
        currencies = ", ".join(f"{code} ({name})" for code, name in info.currencies.items())
        return f"Currency: {currencies}"
    if field == "region" and info.region:
        return f"Region: {info.region}"
    if field == "subregion" and info.subregion:
        return f"Subregion: {info.subregion}"
    if field == "languages" and info.languages:
        return f"Languages: {', '.join(info.languages)}"
    if field == "flag" and info.flag_emoji:
        return f"Flag: {info.flag_emoji}"

    return None


def synthesize_answer(state: AgentState) -> AgentState:
    if state.get("error"):
        return {"answer": state["error"]}

    info = state.get("country_info")
    if not info:
        return {"answer": "No country data is available for this request."}

    fields = state.get("requested_fields") or DEFAULT_FIELDS
    lines: list[str] = []

    for field in fields:
        line = _render_field(field, info)
        if line:
            lines.append(line)

    if not lines:
        lines.append("Requested fields were unavailable for this country.")

    title = info.name_common or info.query
    answer = f"{title}\n" + "\n".join(lines)
    return {"answer": answer}


def build_country_graph() -> Any:
    workflow = StateGraph(AgentState)

    workflow.add_node("identify_intent", identify_intent)
    workflow.add_node("invoke_country_tool", invoke_country_tool)
    workflow.add_node("synthesize_answer", synthesize_answer)

    workflow.add_edge(START, "identify_intent")
    workflow.add_edge("identify_intent", "invoke_country_tool")
    workflow.add_edge("invoke_country_tool", "synthesize_answer")
    workflow.add_edge("synthesize_answer", END)

    return workflow.compile()

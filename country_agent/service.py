from __future__ import annotations

from country_agent.graph import build_country_graph


class CountryInfoAgent:
    """Service wrapper around the LangGraph workflow."""

    def __init__(self) -> None:
        self._graph = build_country_graph()

    def ask(self, question: str) -> str:
        state = self._graph.invoke({"question": question})
        return state["answer"]

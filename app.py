from __future__ import annotations

import warnings

from fastapi import FastAPI, HTTPException

from country_agent.models import AskRequest, AskResponse

warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
    module=r"langchain_core\._api\.deprecation",
)

from country_agent.service import CountryInfoAgent

app = FastAPI(title="Country Info AI Agent", version="1.0.0")
agent = CountryInfoAgent()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse, responses={422: {"description": "Validation Error"}})
def ask_country(request: AskRequest) -> AskResponse:
    try:
        answer = agent.ask(request.question)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Internal error") from exc

    return AskResponse(answer=answer)

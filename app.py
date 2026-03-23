from __future__ import annotations

import logging
import warnings
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from country_agent.models import AskRequest, AskResponse

warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
    module=r"langchain_core\._api\.deprecation",
)

from country_agent.service import CountryInfoAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_agent: CountryInfoAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _agent
    logger.info("Initialising CountryInfoAgent…")
    _agent = CountryInfoAgent()
    logger.info("Agent ready.")
    yield
    _agent = None


app = FastAPI(title="Country Info AI Agent", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse, responses={422: {"description": "Validation Error"}})
def ask_country(request: AskRequest) -> AskResponse:
    if _agent is None:  # pragma: no cover
        raise HTTPException(status_code=503, detail="Service not ready")
    logger.info("question=%r", request.question)
    try:
        answer = _agent.ask(request.question)
    except Exception as exc:  # pragma: no cover
        logger.exception("Unhandled error processing question")
        raise HTTPException(status_code=500, detail="Internal error") from exc
    logger.info("answered question=%r", request.question)
    return AskResponse(answer=answer)

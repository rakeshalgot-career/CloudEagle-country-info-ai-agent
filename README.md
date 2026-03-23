# Country Information AI Agent

A production-style LangGraph agent that answers country questions using the public REST Countries API.

## What this implements

- LangGraph workflow (not a single prompt)
- Explicit agent stages:
  - Intent and field identification
  - Tool invocation (REST Countries)
  - Answer synthesis
- Grounded responses based only on tool output
- Graceful handling for invalid input and missing data

## Architecture

The runtime flow is:

1. `identify_intent` node
   - Extracts the country name from the user question
   - Detects requested fields (capital, population, currency, region, subregion, languages, flag)
2. `invoke_country_tool` node
   - Calls `https://restcountries.com/v3.1/name/{country}`
   - Tries exact (`fullText=true`) and then fallback search
   - Normalizes API payload to a stable `CountryInfo` model
3. `synthesize_answer` node
   - Creates a user-facing answer from the normalized data
   - Reports partial/missing fields clearly

## Project structure

- `country_agent/graph.py` - LangGraph state and nodes
- `country_agent/tools/rest_countries.py` - REST Countries tool client and normalization
- `country_agent/models.py` - API and internal models
- `country_agent/service.py` - service wrapper over graph
- `app.py` - FastAPI HTTP service
- `cli.py` - local interactive CLI

## Run locally

Python version requirement: use Python 3.11 to 3.13. Current dependencies do not reliably install on Python 3.14 yet.

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start API:

```bash
uvicorn app:app --reload
```

3. Test:

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the capital and population of Brazil?"}'
```

Health check:

```bash
curl "http://127.0.0.1:8000/health"
```

## CLI mode

```bash
python cli.py
```

## Production-oriented choices

- Stable normalized model between external API and synthesis logic
- Explicit state-based workflow with clear node responsibilities
- Graceful fallback behavior for unknown countries and unavailable fields
- Configurable API base URL and timeout by env vars

Environment variables:

- `REST_COUNTRIES_BASE_URL` (default: `https://restcountries.com/v3.1`)
- `HTTP_TIMEOUT_SECONDS` (default: `12`)

## Known limitations and trade-offs

- Country extraction is heuristic and may fail for highly ambiguous phrasing
- Only one primary country is resolved per question
- No caching layer (kept out due to assignment constraints)

## Deployment suggestion (for assignment deliverable)

Deploy `app.py` to a simple FastAPI host (for example Render or Railway) and expose `/ask` plus `/health`.
This repository is deployment-ready once environment and dependency setup are complete.


## Submission checklist

- [x] GitHub repository link: https://github.com/rakeshalgot-career/CloudEagle-country-info-ai-agent
- [x] Hosted API URL (direct test link): https://cloudeagle-country-info-ai-agent.onrender.com/ask
- [ ] Walkthrough video link: _add here_

Video should cover:
- Overall architecture (3-node LangGraph flow)
- Live examples: population of Germany, currency of Japan, capital + population of Brazil
- Production behavior: invalid input handling, partial data, service errors
- Known limitations and trade-offs

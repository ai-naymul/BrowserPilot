# Generative UI — BrowserPilot v2.0 engine

Turns structured data into a **live, interactive dashboard**: an LLM produces a
`ComponentSpec` model and the React frontend renders it (metric cards, charts,
tables, maps) through a dynamic component registry.

This is being integrated as BrowserPilot's v2.0 output layer — the scraper
provides the data, this renders the dashboard. See
[`../docs/V2_GENERATIVE_UI_PLAN.md`](../docs/V2_GENERATIVE_UI_PLAN.md). It runs
standalone for now.

## Stack

- **Backend:** FastAPI (Python, Poetry) — LLM via OpenRouter (OpenAI SDK)
- **Frontend:** Vite + React + TypeScript + shadcn/ui + Tailwind

## Run it

### Backend

```bash
cd backend
poetry install
cp .env.example .env          # then fill in your keys
# OPENROUTER_API_KEY is required (the LLM). FIRECRAWL_API_KEY is optional.
poetry run uvicorn app.main:app --reload      # -> http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                    # -> http://localhost:8080
```

## Notes

- `OPENROUTER_API_KEY` holds an **OpenRouter** key (used via the OpenAI SDK).
- Work in progress: legacy paths (`ui_spec`/`UIPanel`, `/api/generate`) are being
  collapsed into a single `ComponentSpec` contract during BrowserPilot
  integration (Phase 2).

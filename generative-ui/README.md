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

## Run the full stack (scrape → dashboard)

Three processes: BrowserPilot (scraper, `:8000`), this gen-UI backend
(renderer, `:8001`), and this frontend (`:8080`).

```bash
# 1. BrowserPilot — the scraper — on :8000  (from the repo root)
GOOGLE_API_KEY=your_gemini_key \
  python -m uvicorn backend.main:app --port 8000

# 2. gen-UI backend — the renderer — on :8001, pointed at BrowserPilot
cd generative-ui/backend
poetry install
OPENROUTER_API_KEY=your_openrouter_key \
BROWSERPILOT_URL=http://localhost:8000 \
  poetry run uvicorn app.main:app --port 8001

# 3. gen-UI frontend — on :8080, pointed at the gen-UI backend
cd generative-ui/frontend
npm install
VITE_API_BASE_URL=http://localhost:8001 npm run dev
```

Open `http://localhost:8080`, choose **"Scrape a website"**, paste product URLs
and a question (e.g. *"compare these by price"*) → BrowserPilot scrapes them and
a live dashboard builds itself.

**Describe-a-task mode** (LLM synthesizes data, no scraping) also works with just
the gen-UI backend + frontend.

## Notes

- `OPENROUTER_API_KEY` holds an **OpenRouter** key (used via the OpenAI SDK).
- Work in progress: legacy paths (`ui_spec`/`UIPanel`, `/api/generate`) are being
  collapsed into a single `ComponentSpec` contract during BrowserPilot
  integration (Phase 2).

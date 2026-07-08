# BrowserPilot v2.0 — Generative UI: Execution Plan

**Vision (one sentence):** *Describe what you want → BrowserPilot scrapes any site (even protected ones) → a live, interactive dashboard builds itself.*

This is the differentiator no funded competitor occupies. Data players (Firecrawl, browser-use, crawl4ai) return a file. UI players (CopilotKit, thesys, Vercel AI SDK) render UI from data you already have. BrowserPilot does the full loop — **URL + a sentence → living app** — self-hosted and free.

---

## Why this wins (competitive truth)

| Capability | Claude/ChatGPT Artifacts | Firecrawl | Fellou / AI browsers | **BrowserPilot v2** |
|---|---|---|---|---|
| Pulls live data from any website | No (you paste data) | Yes | Yes | **Yes** |
| Turns it into interactive UI | Static one-shot HTML | No | No (you watch a browser) | **Yes — live dashboard** |
| Refinable (persistent data model) | No | N/A | N/A | **Yes** |
| Refreshable / connected to source | No | data only | ephemeral | **Yes** |
| Self-hosted & free | No | Paid cloud | Paid app | **Yes** |

The generative dashboard is also the **viral artifact BrowserPilot has never had**: a scraper's payoff is a boring JSON file (dead demo); a dashboard assembling itself in real time is the tweet / Show HN hero / ProductHunt gif.

---

## Source asset

Working generative-UI system exists at `Fellou/generative-ui/generative-ui-browser` (FastAPI backend + Vite/React/shadcn frontend). It is **real, not a mock**: LLM (Claude via OpenRouter) → structured entity model → `DynamicComponentRenderer` + `COMPONENT_REGISTRY` → live UI. Component types already implemented: `metric_card`, `action_button`, `line_chart`, `area_chart`, `pie_chart`, `scatter_chart`, `bar_chart`, `comparison_table`, `data_grid`, `expandable_section`, `news_highlight`, `map`, plus layout primitives (`text`, `divider`, `spacer`, `grid`, `stack`).

**⚠️ Provenance:** that code was hosted on a private company GitLab (`asix.inc`, `partner/generative-poc`). Owner confirms rights to relicense. **Clean-import is mandatory** — see Phase 1 checklist. Never push the existing git history/remote.

---

## Phased plan

### Phase 0 — Foundation (make BrowserPilot boot). GATE for everything.
The current repo does not run if you follow the README. No growth tactic converts against a broken install.
- Fix Dockerfile: install `patchright` + `patchright install chromium` (currently installs `playwright`, code imports `patchright` → crash-loop).
- Build the frontend and serve `frontend/dist` (currently serves raw source → blank UI on fresh clone).
- Pin a stable Gemini model (remove hardcoded `gemini-2.5-flash-preview-05-20` time-bomb).
- Ship `make benchmark` — a reproducible stealth benchmark (replaces screenshot-only proof).
- **Exit gate:** fresh clone on a clean machine → working scrape by following only the README.

### Phase 1 — Clean import of gen-UI. GATE: no asix history/keys published.
- Import code fresh (new git history, no GitLab remote).
- Add `MIT LICENSE`. Rotate/revoke the real API keys currently in `backend/.env`.
- Strip all `asix`/`Fellou`/`partner` references and the ~56 internal `*_COMPLETE.md` / `*_TESTS.md` status docs.
- Delete dead weight: `frontend_backup/` (Next.js), `kinetic-spark-ui/` (duplicate frontend), `backend/app/models.py` (shadowed), the legacy `ui_spec.py`/`UIPanel` system, and the dead `/api/generate` scrape pipeline.
- Collapse to **one** frontend and **one** UI-spec concept (`ComponentSpec[]`).

### Phase 2 — Integrate (scrape → dashboard).
- Define **one canonical `ComponentSpec` contract** (shared schema, not two loosely-typed pydantic/TS interfaces). Enforce it server-side with validation + fallback components (`component_templates.py` already has the building blocks).
- Add `POST /render`: structured scraped rows → `ComponentSpec[]` + `LayoutSpec`. This is the clean seam.
- Wire `DynamicComponentRenderer` as BrowserPilot's output view (alongside/replacing raw-file download).
- **Strip travel-domain hardcoding** — `extractEntityIdFromKey` (tokyo/paris/barcelona patterns), `groupIntoSections` (weather/costs/safety/logistics), MetricCard "7-day cost" heuristics. Generalize to arbitrary scraped data.
- **Exit gate:** prompt → dashboard works on 3 hero sites (e.g. Amazon pricing, a stats site, a real-estate listing).

### Phase 3 — App-ify (easier + reliable "like a mobile app").
- **Hosted "try it live" demo** (no clone, no key) — gated with owner key + auth + rate limits. Highest-leverage GTM move.
- Add auth + rate limiting to LLM endpoints (currently an open money-spending proxy).
- Mobile-first responsive layout (currently desktop tri-pane with mobile fallbacks).
- Soften the light theme (pure-white bg + saturated blue/gold → off-white + desaturated tokens); calmer motion.
- Reliability: set `max_tokens`, add JSON-repair/fallback so the main flow never 500s on a truncated LLM response.
- Remove 253 `console.log`s; fix duplicated/invalid CSS.

### Phase 4 — Launch.
- Record the 30–60s self-building-dashboard clip (the hero asset).
- Sequence: awesome-lists (durable) → r/webscraping + r/dataengineering (participate first) → Show HN (Tue–Thu 8–10am ET, reply every comment 2h) → ProductHunt.
- README hero = the clip + the hosted demo link + one-command setup that actually works.

---

## Full backlog (from both audits)

### BrowserPilot foundation (Phase 0)
- **[critical]** Docker crash-loops — patchright not installed in Dockerfile.
- **[critical]** Fresh clone serves broken UI — `main.py` serves raw `frontend/`, not built `dist`; no build step in README.
- **[high]** Hardcoded preview Gemini model — breaks when Google retires it; Docker pins `google-generativeai==0.5.0` vs requirements `>=0.8.0`.
- **[high]** Stealth benchmarks are screenshots only — no reproducible script.
- **[medium]** Dead code: `vnc_proxy.py`, `stealth_engine.get_stealth_script` (never injected), `vision_model.extract_token_usage`.
- **[medium]** GHOST_MODE.md describes stealth mechanism that runtime never executes.
- **[low]** ~29MB binary marketing assets + `reddit_*.txt` drafts committed; CI README references wrong owner `ghcr.io/veverkap`.

### Gen-UI import + integration hardening (Phases 1–3)
**Critical**
- C1 — Backend Dockerfile wrong entrypoint (`uvicorn main:app` → must be `app.main:app`).
- C2 — `docker-compose.yml` frontend service stale (nonexistent `frontend/Dockerfile`, `.next` volume, port 3000).
- C3 — `QUICKSTART.sh` broken (`pip install -r requirements.txt` in a Poetry project; wrong env var name).
- C4 — No effective rate limiting on `/api/refine/*` LLM endpoints (unbounded spend).
- C5 — No authentication on any endpoint (open money-spending LLM proxy).

**High**
- H1 — Root README describes a different, defunct product (Next.js/3000/`/api/generate`).
- H2 — `/api/refine/stream` dead & broken (calls nonexistent `intent_classifier.classify()`, `IntentType.TASK_CREATE`).
- H3 — `actionHandler.ts` POSTs to nonexistent `/api/refine/create` (404).
- H4 — `create-task` LLM call sets no `max_tokens` → truncation 500s the primary flow.
- H5 — Three different API-base-URL env var names + hardcoded `localhost:8000` (undeployable).
- H6 — CORS `allow_origins=["*"]` with `allow_credentials=True`.
- H7 — Entity/component logic hardcoded to travel/comparison demos (breaks on other data).
- H8 — Debug writes to `/tmp/llm_*_debug.txt` every request (race/leak/read-only-FS).
- H9 — Two parallel conflicting UI systems (`UIPanel` vs `ComponentSpec[]`).
- H10 — Zero automated tests.

**Medium**
- M1 — Three frontends, two dead (`frontend/`, `kinetic-spark-ui/`, `frontend_backup/`).
- M2 — Dead/shadowed `backend/app/models.py`.
- M3 — `generate_components_from_entities` permanent stub (returns `[]`).
- M4 — Map loads Leaflet from CDN while `mapbox-gl` is the declared (unused) dep.
- M5 — Duplicated & invalid CSS (`.empty-chip` conflict, `hsl(var(--accent-soft) / 1.2)`, two radius/shadow systems).
- M6 — Light theme unpolished / not "soft."
- M7 — 253 `console.log`s shipped to production.
- M8 — Inconsistent LLM model IDs + duplicated JSON-fence stripping across ~5 handlers.
- M9 — 56 aspirational status docs contradicting the broken setup.
- M10 — 2–3 LLM round-trips per user action (classification + suggested-questions + generation).
- M11 — Real API keys sitting in working-tree `backend/.env` (rotate before publishing).

**Low**
- L1 — Frontend README is default Lovable boilerplate.
- L2 — No LICENSE.
- L3 — `.env.example` mislabels the key.
- L4 — `python ^3.8` floor vs 3.12 usage.
- L5 — a11y gaps (hardcoded green/red trend colors, chart contrast, map).
- L6 — `buildEntityHierarchy` is a no-op.

---

## GTM notes
- **Issue-hygiene rule:** do not publish the full 27-item bug list as public issues — a wall of "critical: broken/no-auth" reads as *avoid this repo*. Track tech-debt here; publish only curated roadmap epics + `good first issue`s (to break the 0-external-PRs problem).
- **Realistic target:** 167 → 1,000–2,000 stars in 6–12 months *if* the product runs in one command and the demo works. 10k is a multi-year moonshot.
- Evidence base: CopilotKit ~28k stars owns "open-source generative UI" — do NOT frame this as "open-source thesys"; frame it as "the scraper that builds you the dashboard." The combination is the wedge.

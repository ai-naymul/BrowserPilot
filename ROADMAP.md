# BrowserPilot Roadmap

> Building the most capable open-source AI browser agent with undetectable stealth and universal scraping.

---

## Release v1.0.0 — The Foundation

> Status: **Done**

Set up proper project infrastructure for sustainable open-source development.

- [x] Add pytest configuration and test infrastructure
- [x] Create `tests/` directory with proper structure
- [x] Write unit tests for `proxy_manager.py` (24 tests)
- [x] Write unit tests for `anti_bot_detection.py` (17 tests)
- [x] Write unit tests for `universal_extractor.py` (33 tests)
- [x] Write unit tests for `vision_model.py` (30 tests)
- [x] Add GitHub Actions CI workflow for tests
- [x] Add issue templates (bug report, feature request)
- [x] Add pull request template
- [x] Add `CONTRIBUTING.md`
- [x] Add `LICENSE` file (MIT)
- [x] Semantic versioning starting at v1.0.0

---

## Release v1.1.0 — Ghost Mode: Undetectable Browser

> Status: **Done** ✅

Full fingerprint evasion and human-like behavior to bypass all major anti-bot systems.

### Stealth Engine (`backend/stealth_engine.py`)
- [x] Modern User-Agent pool (Chrome 120-130, Firefox 121-128, Edge 120-130)
- [x] Navigator property patching (`webdriver`, `plugins`, `languages`, `platform`)
- [x] `window.chrome` runtime injection (Cloudflare/DataDome check)
- [x] WebGL fingerprint spoofing (vendor + renderer override)
- [x] Canvas fingerprint noise injection
- [x] AudioContext fingerprint spoofing
- [ ] WebRTC leak prevention (block local IP exposure) — v1.2 scope
- [x] Sec-CH-UA Client Hints headers
- [x] Timezone/locale geo-matching to proxy location (geo helper in proxy_manager)
- [x] Permission API patching
- [ ] Screen resolution randomization — v1.2 scope (viewport configurable via env)
- [x] `deviceMemory` and `hardwareConcurrency` spoofing
- [x] Tests for all stealth scripts (23 tests)

### Human Behavior Simulator (`backend/human_behavior.py`)
- [x] Bezier curve mouse movements (cubic interpolation)
- [x] Realistic typing with variable WPM and occasional typos
- [x] Human-like scrolling (variable speed, reading pauses)
- [x] Random micro-pauses between actions
- [x] Click with slight offset from center + hold duration
- [ ] Periodic micro-interactions (mouse drift, small scrolls) — v1.2 scope
- [x] Tests for behavior simulation (15 tests)

### Integration
- [x] Inject stealth scripts in `browser_controller.py` via `add_init_script()`
- [x] Replace hardcoded Chrome 91 UA with modern UA pool
- [x] Use browser context instead of raw page for proper isolation
- [x] Replace instant clicks with human mouse movement
- [x] Replace instant typing with human typing
- [x] Replace instant scrolling with human scrolling
- [ ] Validate against bot.sannysoft.com (before/after screenshots) — manual step
- [ ] Validate against browserleaks.com — manual step

### Additional fixes shipped with v1.1.0
- [x] Central `backend/config.py` — all 25+ hardcoded values replaced with env-var-backed config
- [x] `requirements.txt` — added Pillow, python-dotenv, updated google-generativeai to >=0.8.0
- [x] Deleted broken dead code `backend/cdp_streamer.py`
- [x] `proxy_manager.py` — guarded JSON parse, SOCKS4/5 URL support, geo-locale map
- [x] `anti_bot_detection.py` — model name from config, logging, 3-attempt Gemini retry
- [x] `vnc_proxy.py` — async socket connect, fixed deprecated event loop
- [x] `universal_extractor.py` — config-backed limits, logging, fixed event loop
- [x] 152 tests passing (up from 104)

---

## Release v1.2.0 — Universal Proxy System

> Status: **Planned**

Support any proxy type with intelligent rotation and geo-matching.

### Proxy Manager Enhancement (`backend/proxy_manager.py`)
- [ ] Proxy URL parser (HTTP, HTTPS, SOCKS4, SOCKS5)
- [ ] Multiple input formats: `protocol://user:pass@host:port`, `host:port:user:pass`
- [ ] Load proxies from env JSON, text file (one per line), comma-separated URLs
- [ ] Async proxy validation via aiohttp
- [ ] Rotation strategies: best-performance, round-robin, random, least-used
- [ ] Per-proxy rate limiting (requests per minute tracking)
- [ ] Geo-location country code mapping (30+ countries)
- [ ] New fingerprint profile on each proxy rotation (new identity)
- [ ] Proxy health dashboard improvements
- [ ] Tests for URL parsing, rotation, validation, rate limiting

### New Dependencies
- [ ] Add `aiohttp>=3.9.0` to requirements.txt
- [ ] Add `aiohttp-socks>=0.8.0` to requirements.txt

### API Endpoints
- [ ] `POST /proxy/add` — add proxy at runtime
- [ ] `POST /proxy/validate` — validate all proxies
- [ ] Enhanced `GET /proxy/stats` — include protocol, geo, validation status

---

## Release v1.3.0 — Crawl Anything

> Status: **Planned**

Multi-page crawling with pagination detection and full-site support.

### Crawler Engine (`backend/crawler_engine.py`)
- [ ] `CrawlMode` enum: `SINGLE_PAGE`, `PAGINATION`, `FULL_SITE`
- [ ] `CrawlConfig` dataclass (max_pages, max_depth, delay, patterns)
- [ ] Pagination detection (heuristic + AI vision fallback)
- [ ] Full-site crawling with URL queue and BFS by depth
- [ ] URL deduplication (visited set)
- [ ] Content deduplication (hash comparison)
- [ ] `sitemap.xml` parsing and URL seeding
- [ ] `robots.txt` parsing and optional respect
- [ ] Progress broadcasting via WebSocket
- [ ] Incremental result saving (stream to disk)
- [ ] Tests for crawling, pagination, dedup, sitemap parsing

### Agent Integration (`backend/agent.py`)
- [ ] Crawl mode dispatch before agent loop
- [ ] Expanded step limits for crawl tasks
- [ ] Pass crawl config through from API

### API Changes (`backend/main.py`)
- [ ] Add `crawl_mode` to `JobRequest`
- [ ] Add `crawl_config` to `JobRequest`
- [ ] Add `proxy_config` to `JobRequest`
- [ ] Add `stealth_level` to `JobRequest`
- [ ] `GET /crawl/{job_id}/progress` endpoint

### Frontend Updates
- [ ] Crawl mode selector in `JobForm.tsx`
- [ ] Crawl config panel (max pages, depth, delay)
- [ ] Proxy config section (custom proxy URL, rotation strategy)
- [ ] Stealth level toggle (minimal / standard / maximum)
- [ ] `CrawlProgress.tsx` component (pages crawled, queue, progress bar)
- [ ] WebSocket handler for `crawl_progress` messages

---

## Release v2.0.0 — Generative UI

> Status: **Future**

AI-powered UI generation from scraped content. Users give a prompt, BrowserPilot scrapes and presents data in dynamically generated visual layouts.

- [ ] Design generative UI architecture
- [ ] Component generation from structured data
- [ ] Multiple view modes (table, cards, charts, dashboard)
- [ ] Natural language prompt → visual output pipeline
- [ ] Frontend rendering engine for generated components

---

## Growth Strategy

Each release is designed to be shareable and star-worthy.

### Per-Release Checklist
- [ ] Record demo GIF/video showing the feature in action
- [ ] Write a tweet/thread about the release
- [ ] Post on relevant subreddits (r/webscraping, r/python, r/selfhosted, r/opensource)
- [ ] Submit to HackerNews (Show HN) for major releases
- [ ] Write Dev.to / blog article for v1.1.0+ releases
- [ ] Update README with new badges, comparison tables, demo media

### Target Communities
| Release | Primary Channels |
|---------|-----------------|
| v1.0.0 | Twitter/X, GitHub Discussions |
| v1.1.0 | HN Show, r/webscraping, r/python, Dev.to |
| v1.2.0 | r/webscraping, r/selfhosted, proxy forums |
| v1.3.0 | HN Show, r/webscraping, r/selfhosted |
| v2.0.0 | HN, ProductHunt, r/artificial, r/webdev |

### README Improvements (across releases)
- [ ] Add hero demo GIF at the top
- [ ] Add "Why BrowserPilot?" section with unique selling points
- [ ] Add comparison table vs Playwright/Puppeteer/Selenium/Scrapy
- [ ] Add bot detection test proof screenshots
- [ ] Add architecture diagram
- [ ] Add test coverage badge
- [ ] Add version badge

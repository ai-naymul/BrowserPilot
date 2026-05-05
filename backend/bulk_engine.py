"""Bulk scraping engine — concurrent stealth sessions with fingerprint/proxy rotation.

Architecture:
- Workers share a single xvfb display (set once at engine level)
- Each worker owns ONE Chromium process; rotations swap contexts, not browsers
- Cookie jars persist per-domain across context rotations
- Adaptive per-domain throttle backs off on 429s, speeds up on 200s
- Task queue uses asyncio.Lock to prevent race conditions
- Fast DOM extraction by default; AI extraction opt-in
"""

import asyncio
import json
import time
import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from backend.browser_controller import BrowserController
from backend.fingerprint_profile import generate_profile
from backend.proxy_manager import SmartProxyManager
from backend.config import GHOST_MODE_ENABLED

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("outputs")

_BLOCK_SIGNALS = frozenset([
    "access denied", "blocked", "captcha", "challenge",
    "verify you are human", "pardon our interruption",
    "please turn javascript on", "checking your browser",
])


class URLStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class URLTask:
    url: str
    status: URLStatus = URLStatus.PENDING
    result: dict | None = None
    error: str | None = None
    attempts: int = 0
    worker_id: int | None = None
    started_at: float | None = None
    finished_at: float | None = None


@dataclass
class BulkJobConfig:
    urls: list[str]
    prompt: str
    output_format: str = "json"
    max_workers: int = 3
    max_retries: int = 2
    per_domain_delay_s: float = 2.0
    page_timeout_s: float = 45.0
    rotation_interval: int = 10
    use_ai_extraction: bool = False
    block_resources: bool = True


@dataclass
class BulkJobState:
    job_id: str
    config: BulkJobConfig
    tasks: list[URLTask] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float | None = None
    cancelled: bool = False

    @property
    def total(self) -> int:
        return len(self.tasks)

    @property
    def done(self) -> int:
        return sum(1 for t in self.tasks if t.status == URLStatus.DONE)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tasks if t.status == URLStatus.FAILED)

    @property
    def pending(self) -> int:
        return sum(1 for t in self.tasks if t.status in (URLStatus.PENDING, URLStatus.IN_PROGRESS))

    @property
    def progress(self) -> dict:
        elapsed = time.time() - self.started_at if self.started_at else 0
        return {
            "job_id": self.job_id,
            "total": self.total,
            "done": self.done,
            "failed": self.failed,
            "pending": self.pending,
            "cancelled": self.cancelled,
            "elapsed_s": round(elapsed, 1),
            "pages_per_min": round(self.done / max(elapsed / 60, 0.01), 1) if self.started_at else 0,
        }


# ── Adaptive per-domain throttle ────────────────────────────────────────────

class DomainThrottle:
    """Per-domain rate limiter with adaptive backoff on 429/block."""

    def __init__(self, default_delay: float = 2.0):
        self._default_delay = default_delay
        self._domain_delay: dict[str, float] = {}
        self._last_request: dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc

    async def wait(self, url: str) -> None:
        domain = self._get_domain(url)
        async with self._lock:
            delay = self._domain_delay.get(domain, self._default_delay)
            last = self._last_request.get(domain, 0)
            elapsed = time.time() - last
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
            self._last_request[domain] = time.time()

    async def report_success(self, url: str) -> None:
        domain = self._get_domain(url)
        async with self._lock:
            current = self._domain_delay.get(domain, self._default_delay)
            self._domain_delay[domain] = max(self._default_delay, current * 0.8)

    async def report_rate_limit(self, url: str) -> None:
        domain = self._get_domain(url)
        async with self._lock:
            current = self._domain_delay.get(domain, self._default_delay)
            self._domain_delay[domain] = min(current * 2, 30.0)
            logger.warning("Throttle backoff for %s: %.1fs", domain, self._domain_delay[domain])


# ── Shared block intelligence ────────────────────────────────────────────────

class BlockList:
    """Tracks which (domain, proxy) combos are blocked so workers skip them."""

    def __init__(self):
        self._blocked: set[tuple[str, str | None]] = set()
        self._lock = asyncio.Lock()

    async def mark_blocked(self, domain: str, proxy_server: str | None) -> None:
        async with self._lock:
            self._blocked.add((domain, proxy_server))
            logger.warning("Blocked combo: domain=%s proxy=%s", domain, proxy_server)

    async def is_blocked(self, domain: str, proxy_server: str | None) -> bool:
        async with self._lock:
            return (domain, proxy_server) in self._blocked


# ── Cookie jar (per-domain persistence) ──────────────────────────────────────

class CookieJar:
    """Stores cookies per domain so context rotations preserve session state."""

    def __init__(self):
        self._cookies: dict[str, list[dict]] = {}
        self._lock = asyncio.Lock()

    async def save(self, domain: str, cookies: list[dict]) -> None:
        async with self._lock:
            self._cookies[domain] = cookies

    async def load(self, domain: str) -> list[dict]:
        async with self._lock:
            return self._cookies.get(domain, [])


# ── Task queue (thread-safe) ─────────────────────────────────────────────────

class TaskQueue:
    """Concurrency-safe task dispatcher backed by asyncio.Lock."""

    def __init__(self, tasks: list[URLTask]):
        self._tasks = tasks
        self._index = 0
        self._lock = asyncio.Lock()

    async def next(self, worker_id: int) -> URLTask | None:
        async with self._lock:
            while self._index < len(self._tasks):
                task = self._tasks[self._index]
                self._index += 1
                if task.status == URLStatus.PENDING:
                    task.status = URLStatus.IN_PROGRESS
                    task.worker_id = worker_id
                    return task
            return None

    async def requeue(self, task: URLTask) -> None:
        async with self._lock:
            task.status = URLStatus.PENDING
            task.worker_id = None
            self._index = min(self._index, self._tasks.index(task))


# ── Fast DOM extraction (no AI) ─────────────────────────────────────────────

def extract_dom(html: str, url: str, title: str) -> dict:
    """Fast structured extraction using BeautifulSoup. No API calls."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
        tag.decompose()

    headings = []
    for h in soup.find_all(["h1", "h2", "h3"], limit=20):
        text = h.get_text(strip=True)
        if text:
            headings.append(text)

    paragraphs = []
    for p in soup.find_all("p", limit=30):
        text = p.get_text(strip=True)
        if len(text) > 20:
            paragraphs.append(text[:500])

    links = []
    for a in soup.find_all("a", href=True, limit=50):
        text = a.get_text(strip=True)
        href = a["href"]
        if text and href.startswith("http"):
            links.append({"text": text[:100], "href": href})

    tables = []
    for table in soup.find_all("table", limit=5):
        rows = []
        for tr in table.find_all("tr", limit=20):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if any(cells):
                rows.append(cells)
        if rows:
            tables.append(rows)

    images = []
    for img in soup.find_all("img", src=True, limit=20):
        alt = img.get("alt", "")
        if alt:
            images.append({"alt": alt, "src": img["src"][:200]})

    meta = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name", tag.get("property", ""))
        content = tag.get("content", "")
        if name and content and name in ("description", "og:title", "og:description", "keywords"):
            meta[name] = content[:300]

    return {
        "url": url,
        "title": title,
        "meta": meta,
        "headings": headings,
        "paragraphs": paragraphs,
        "links": links[:30],
        "tables": tables,
        "images": images,
    }


# ── Main engine ──────────────────────────────────────────────────────────────

class BulkEngine:
    """Orchestrates concurrent browser workers for bulk URL scraping."""

    def __init__(self, proxy_manager: SmartProxyManager | None = None):
        self._proxy_manager = proxy_manager or SmartProxyManager()
        self._jobs: dict[str, BulkJobState] = {}
        self._throttle = DomainThrottle()
        self._blocklist = BlockList()
        self._cookie_jar = CookieJar()
        self._broadcast: Callable[[str, dict], Coroutine] | None = None

    def set_broadcast(self, fn: Callable[[str, dict], Coroutine]) -> None:
        self._broadcast = fn

    async def _emit(self, job_id: str, msg: dict) -> None:
        if self._broadcast:
            await self._broadcast(job_id, msg)

    # ── public API ───────────────────────────────────────────────────────────

    async def create_job(self, config: BulkJobConfig) -> BulkJobState:
        job_id = str(uuid.uuid4())
        state = BulkJobState(
            job_id=job_id,
            config=config,
            tasks=[URLTask(url=u) for u in config.urls],
        )
        self._jobs[job_id] = state
        self._throttle._default_delay = config.per_domain_delay_s
        return state

    async def run_job(self, job_id: str) -> BulkJobState:
        state = self._jobs[job_id]
        state.started_at = time.time()

        await self._emit(job_id, {"type": "bulk_started", **state.progress})

        queue = TaskQueue(state.tasks)

        workers = []
        n_workers = min(state.config.max_workers, len(state.tasks))
        for i in range(n_workers):
            workers.append(asyncio.create_task(self._worker(state, i, queue)))

        await asyncio.gather(*workers, return_exceptions=True)

        state.finished_at = time.time()

        results = self._aggregate(state)
        output_path = OUTPUT_DIR / f"{job_id}.{state.config.output_format}"
        OUTPUT_DIR.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            if state.config.output_format == "json":
                json.dump(results, f, indent=2, ensure_ascii=False)
            else:
                f.write(self._format_results(results, state.config.output_format))

        await self._emit(job_id, {
            "type": "bulk_finished",
            **state.progress,
            "output_file": str(output_path),
        })

        self._save_checkpoint(state)
        return state

    def get_job(self, job_id: str) -> BulkJobState | None:
        return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        state = self._jobs.get(job_id)
        if not state:
            return False
        state.cancelled = True
        return True

    async def resume_job(self, job_id: str) -> BulkJobState | None:
        state = self._jobs.get(job_id)
        if not state:
            state = self._load_checkpoint(job_id)
            if not state:
                return None
            self._jobs[job_id] = state

        for task in state.tasks:
            if task.status == URLStatus.IN_PROGRESS:
                task.status = URLStatus.PENDING
            if task.status == URLStatus.FAILED and task.attempts < state.config.max_retries:
                task.status = URLStatus.PENDING

        state.cancelled = False
        return await self.run_job(job_id)

    # ── worker ───────────────────────────────────────────────────────────────

    async def _worker(self, state: BulkJobState, worker_id: int, queue: TaskQueue) -> None:
        seed = f"bulk-{state.job_id}-w{worker_id}-{int(time.time())}"
        proxy_info = self._proxy_manager.get_best_proxy()
        proxy = proxy_info.to_playwright_dict() if proxy_info else None
        proxy_server = proxy.get("server") if proxy else None
        proxy_country = proxy_info.location if proxy_info else None

        pages_on_profile = 0
        bc: BrowserController | None = None

        try:
            bc = await self._launch_browser(seed, proxy, proxy_country, state.config.block_resources)

            while not state.cancelled:
                task = await queue.next(worker_id)
                if not task:
                    break

                domain = urlparse(task.url).netloc

                if await self._blocklist.is_blocked(domain, proxy_server):
                    task.status = URLStatus.SKIPPED
                    task.error = f"blocked combo: {domain} + {proxy_server}"
                    continue

                # Context rotation: swap fingerprint, keep browser process alive
                if pages_on_profile >= state.config.rotation_interval:
                    cookies = await bc.get_cookies()
                    await self._cookie_jar.save(domain, cookies)

                    seed = f"bulk-{state.job_id}-w{worker_id}-{int(time.time())}"
                    new_profile = generate_profile(seed=seed, proxy_country=proxy_country) if GHOST_MODE_ENABLED else generate_profile()
                    saved_cookies = await self._cookie_jar.load(domain)
                    await bc.rotate_context(new_profile=new_profile, cookies=saved_cookies)
                    pages_on_profile = 0
                    logger.info("Worker %d rotated context after %d pages", worker_id, state.config.rotation_interval)

                await self._throttle.wait(task.url)

                try:
                    result = await self._scrape_url(bc, task, state.config)
                    task.status = URLStatus.DONE
                    task.result = result
                    task.finished_at = time.time()
                    pages_on_profile += 1

                    await self._throttle.report_success(task.url)

                    if proxy_info:
                        self._proxy_manager.mark_proxy_success(proxy_info, time.time() - (task.started_at or time.time()))

                    await self._emit(state.job_id, {
                        "type": "bulk_progress",
                        "url": task.url,
                        "status": "done",
                        "worker_id": worker_id,
                        **state.progress,
                    })

                except BotDetectedError as e:
                    task.attempts += 1
                    task.error = str(e)
                    await self._blocklist.mark_blocked(domain, proxy_server)
                    await self._throttle.report_rate_limit(task.url)

                    if proxy_info:
                        self._proxy_manager.mark_proxy_failure(proxy_info, domain, str(e))

                    if task.attempts >= state.config.max_retries:
                        task.status = URLStatus.FAILED
                        task.finished_at = time.time()
                    else:
                        await queue.requeue(task)

                    # Full browser restart on bot detection (new IP needed)
                    await self._close_browser(bc)
                    seed = f"bulk-{state.job_id}-w{worker_id}-retry-{int(time.time())}"
                    proxy_info = self._proxy_manager.get_best_proxy()
                    proxy = proxy_info.to_playwright_dict() if proxy_info else None
                    proxy_server = proxy.get("server") if proxy else None
                    proxy_country = proxy_info.location if proxy_info else None
                    bc = await self._launch_browser(seed, proxy, proxy_country, state.config.block_resources)
                    pages_on_profile = 0

                    await self._emit(state.job_id, {
                        "type": "bulk_progress",
                        "url": task.url,
                        "status": "blocked",
                        "worker_id": worker_id,
                        "error": str(e),
                        **state.progress,
                    })

                except Exception as e:
                    task.attempts += 1
                    task.error = str(e)
                    if task.attempts >= state.config.max_retries:
                        task.status = URLStatus.FAILED
                        task.finished_at = time.time()
                    else:
                        await queue.requeue(task)

                    await self._emit(state.job_id, {
                        "type": "bulk_progress",
                        "url": task.url,
                        "status": "error",
                        "worker_id": worker_id,
                        "error": str(e),
                        **state.progress,
                    })

        finally:
            if bc:
                await self._close_browser(bc)

    # ── browser lifecycle ────────────────────────────────────────────────────

    async def _launch_browser(
        self, seed: str, proxy: dict | None, proxy_country: str | None,
        block_resources: bool = True,
    ) -> BrowserController:
        bc = BrowserController(
            headless=False, proxy=proxy, proxy_country=proxy_country,
            block_resources=block_resources,
        )
        bc._profile = generate_profile(seed=seed, proxy_country=proxy_country) if GHOST_MODE_ENABLED else generate_profile()
        await bc.__aenter__()
        return bc

    async def _close_browser(self, bc: BrowserController) -> None:
        try:
            await bc.__aexit__(None, None, None)
        except Exception:
            pass

    # ── page scraping ────────────────────────────────────────────────────────

    async def _scrape_url(
        self,
        bc: BrowserController,
        task: URLTask,
        config: BulkJobConfig,
    ) -> dict:
        task.started_at = time.time()
        page = bc.page
        timeout_ms = int(config.page_timeout_s * 1000)

        resp = await page.goto(task.url, wait_until="domcontentloaded", timeout=timeout_ms)
        await page.wait_for_timeout(1500)

        status = resp.status if resp else 0

        if status in (403, 429):
            html = await page.content()
            lower = html.lower()
            if any(s in lower for s in _BLOCK_SIGNALS):
                raise BotDetectedError(f"HTTP {status} with block signals on {task.url}")

        title = await page.title()

        if config.use_ai_extraction:
            from backend.universal_extractor import UniversalExtractor
            extractor = UniversalExtractor()
            extracted = await extractor.extract_intelligent_content(bc, config.prompt, "json", task.url)
        else:
            html = await page.content()
            extracted = extract_dom(html, task.url, title)

        return {
            "url": task.url,
            "title": title,
            "status": status,
            "extracted": extracted,
            "scraped_at": time.time(),
        }

    # ── legacy compat ────────────────────────────────────────────────────────

    def _next_task(self, state: BulkJobState, worker_id: int) -> URLTask | None:
        for task in state.tasks:
            if task.status == URLStatus.PENDING:
                task.status = URLStatus.IN_PROGRESS
                task.worker_id = worker_id
                return task
        return None

    # ── output ───────────────────────────────────────────────────────────────

    def _aggregate(self, state: BulkJobState) -> list[dict]:
        results = []
        for task in state.tasks:
            if task.status == URLStatus.DONE and task.result:
                results.append(task.result)
            elif task.status in (URLStatus.FAILED, URLStatus.SKIPPED):
                results.append({
                    "url": task.url,
                    "status": task.status.value,
                    "error": task.error,
                    "attempts": task.attempts,
                })
        return results

    def _format_results(self, results: list[dict], fmt: str) -> str:
        if fmt == "csv":
            if not results:
                return ""
            import csv
            import io
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=results[0].keys())
            writer.writeheader()
            for r in results:
                writer.writerow({k: str(v)[:500] for k, v in r.items()})
            return buf.getvalue()
        if fmt == "md":
            lines = [f"# Bulk Scrape Results\n\nTotal: {len(results)} pages\n"]
            for r in results:
                lines.append(f"## {r.get('title', r.get('url', 'Unknown'))}\n")
                lines.append(f"URL: {r.get('url', 'N/A')}\n")
                if r.get("extracted"):
                    lines.append(f"```\n{str(r['extracted'])[:1000]}\n```\n")
            return "\n".join(lines)
        return json.dumps(results, indent=2, ensure_ascii=False)

    # ── checkpointing ────────────────────────────────────────────────────────

    def _save_checkpoint(self, state: BulkJobState) -> None:
        cp_dir = OUTPUT_DIR / "checkpoints"
        cp_dir.mkdir(parents=True, exist_ok=True)
        cp = {
            "job_id": state.job_id,
            "config": {
                "urls": state.config.urls,
                "prompt": state.config.prompt,
                "output_format": state.config.output_format,
                "max_workers": state.config.max_workers,
                "max_retries": state.config.max_retries,
                "per_domain_delay_s": state.config.per_domain_delay_s,
                "page_timeout_s": state.config.page_timeout_s,
                "rotation_interval": state.config.rotation_interval,
                "use_ai_extraction": state.config.use_ai_extraction,
                "block_resources": state.config.block_resources,
            },
            "tasks": [
                {
                    "url": t.url,
                    "status": t.status.value,
                    "error": t.error,
                    "attempts": t.attempts,
                    "result": t.result,
                }
                for t in state.tasks
            ],
        }
        with open(cp_dir / f"{state.job_id}.json", "w") as f:
            json.dump(cp, f, indent=2)

    def _load_checkpoint(self, job_id: str) -> BulkJobState | None:
        cp_path = OUTPUT_DIR / "checkpoints" / f"{job_id}.json"
        if not cp_path.exists():
            return None
        with open(cp_path) as f:
            cp = json.load(f)
        config = BulkJobConfig(**cp["config"])
        state = BulkJobState(job_id=job_id, config=config)
        for t in cp["tasks"]:
            task = URLTask(url=t["url"])
            task.status = URLStatus(t["status"])
            task.error = t.get("error")
            task.attempts = t.get("attempts", 0)
            task.result = t.get("result")
            state.tasks.append(task)
        return state


class BotDetectedError(Exception):
    pass

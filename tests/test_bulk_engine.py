"""Tests for the bulk scraping engine."""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.bulk_engine import (
    BlockList,
    BotDetectedError,
    BulkEngine,
    BulkJobConfig,
    BulkJobState,
    CookieJar,
    DomainThrottle,
    TaskQueue,
    URLStatus,
    URLTask,
    extract_dom,
)


# ── URLTask ──────────────────────────────────────────────────────────────────

class TestURLTask:
    def test_defaults(self):
        t = URLTask(url="https://example.com")
        assert t.status == URLStatus.PENDING
        assert t.result is None
        assert t.attempts == 0

    def test_status_transitions(self):
        t = URLTask(url="https://example.com")
        t.status = URLStatus.IN_PROGRESS
        assert t.status == URLStatus.IN_PROGRESS
        t.status = URLStatus.DONE
        assert t.status == URLStatus.DONE


# ── BulkJobState ─────────────────────────────────────────────────────────────

class TestBulkJobState:
    def _make_state(self, n=5):
        config = BulkJobConfig(
            urls=[f"https://example.com/{i}" for i in range(n)],
            prompt="extract data",
        )
        return BulkJobState(
            job_id="test-123",
            config=config,
            tasks=[URLTask(url=u) for u in config.urls],
        )

    def test_progress_all_pending(self):
        state = self._make_state(5)
        assert state.total == 5
        assert state.done == 0
        assert state.failed == 0
        assert state.pending == 5

    def test_progress_mixed(self):
        state = self._make_state(5)
        state.tasks[0].status = URLStatus.DONE
        state.tasks[1].status = URLStatus.DONE
        state.tasks[2].status = URLStatus.FAILED
        state.tasks[3].status = URLStatus.IN_PROGRESS
        assert state.done == 2
        assert state.failed == 1
        assert state.pending == 2

    def test_progress_dict(self):
        state = self._make_state(3)
        state.started_at = time.time()
        p = state.progress
        assert p["total"] == 3
        assert p["job_id"] == "test-123"
        assert "pages_per_min" in p

    def test_cancelled(self):
        state = self._make_state(2)
        assert state.cancelled is False
        state.cancelled = True
        assert state.progress["cancelled"] is True


# ── DomainThrottle (adaptive) ────────────────────────────────────────────────

class TestDomainThrottle:
    @pytest.mark.asyncio
    async def test_first_request_no_delay(self):
        throttle = DomainThrottle(default_delay=1.0)
        start = time.time()
        await throttle.wait("https://example.com/page1")
        elapsed = time.time() - start
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_second_request_delayed(self):
        throttle = DomainThrottle(default_delay=0.3)
        await throttle.wait("https://example.com/page1")
        start = time.time()
        await throttle.wait("https://example.com/page2")
        elapsed = time.time() - start
        assert elapsed >= 0.2

    @pytest.mark.asyncio
    async def test_different_domains_no_delay(self):
        throttle = DomainThrottle(default_delay=1.0)
        await throttle.wait("https://example.com/page1")
        start = time.time()
        await throttle.wait("https://other.com/page1")
        elapsed = time.time() - start
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_backoff_on_rate_limit(self):
        throttle = DomainThrottle(default_delay=1.0)
        await throttle.report_rate_limit("https://example.com/page1")
        assert throttle._domain_delay["example.com"] == 2.0
        await throttle.report_rate_limit("https://example.com/page2")
        assert throttle._domain_delay["example.com"] == 4.0

    @pytest.mark.asyncio
    async def test_backoff_caps_at_30s(self):
        throttle = DomainThrottle(default_delay=1.0)
        for _ in range(10):
            await throttle.report_rate_limit("https://example.com/x")
        assert throttle._domain_delay["example.com"] <= 30.0

    @pytest.mark.asyncio
    async def test_success_reduces_delay(self):
        throttle = DomainThrottle(default_delay=1.0)
        throttle._domain_delay["example.com"] = 10.0
        await throttle.report_success("https://example.com/x")
        assert throttle._domain_delay["example.com"] == 8.0

    @pytest.mark.asyncio
    async def test_success_doesnt_go_below_default(self):
        throttle = DomainThrottle(default_delay=2.0)
        throttle._domain_delay["example.com"] = 2.0
        await throttle.report_success("https://example.com/x")
        assert throttle._domain_delay["example.com"] >= 2.0


# ── BlockList ────────────────────────────────────────────────────────────────

class TestBlockList:
    @pytest.mark.asyncio
    async def test_initially_clear(self):
        bl = BlockList()
        assert await bl.is_blocked("example.com", "proxy1") is False

    @pytest.mark.asyncio
    async def test_mark_and_check(self):
        bl = BlockList()
        await bl.mark_blocked("example.com", "proxy1")
        assert await bl.is_blocked("example.com", "proxy1") is True
        assert await bl.is_blocked("example.com", "proxy2") is False
        assert await bl.is_blocked("other.com", "proxy1") is False

    @pytest.mark.asyncio
    async def test_none_proxy(self):
        bl = BlockList()
        await bl.mark_blocked("example.com", None)
        assert await bl.is_blocked("example.com", None) is True


# ── CookieJar ────────────────────────────────────────────────────────────────

class TestCookieJar:
    @pytest.mark.asyncio
    async def test_save_and_load(self):
        jar = CookieJar()
        cookies = [{"name": "session", "value": "abc123", "domain": "example.com"}]
        await jar.save("example.com", cookies)
        loaded = await jar.load("example.com")
        assert loaded == cookies

    @pytest.mark.asyncio
    async def test_load_empty(self):
        jar = CookieJar()
        assert await jar.load("unknown.com") == []

    @pytest.mark.asyncio
    async def test_overwrite(self):
        jar = CookieJar()
        await jar.save("example.com", [{"name": "a", "value": "1"}])
        await jar.save("example.com", [{"name": "b", "value": "2"}])
        loaded = await jar.load("example.com")
        assert len(loaded) == 1
        assert loaded[0]["name"] == "b"


# ── TaskQueue ────────────────────────────────────────────────────────────────

class TestTaskQueue:
    @pytest.mark.asyncio
    async def test_sequential_dispatch(self):
        tasks = [URLTask(url=f"https://example.com/{i}") for i in range(3)]
        q = TaskQueue(tasks)
        t1 = await q.next(0)
        t2 = await q.next(1)
        t3 = await q.next(0)
        t4 = await q.next(1)
        assert t1.url == "https://example.com/0"
        assert t2.url == "https://example.com/1"
        assert t3.url == "https://example.com/2"
        assert t4 is None

    @pytest.mark.asyncio
    async def test_marks_in_progress(self):
        tasks = [URLTask(url="https://example.com/0")]
        q = TaskQueue(tasks)
        t = await q.next(0)
        assert t.status == URLStatus.IN_PROGRESS
        assert t.worker_id == 0

    @pytest.mark.asyncio
    async def test_requeue(self):
        tasks = [URLTask(url="https://example.com/0"), URLTask(url="https://example.com/1")]
        q = TaskQueue(tasks)
        t1 = await q.next(0)
        t2 = await q.next(1)
        assert await q.next(0) is None
        await q.requeue(t1)
        t3 = await q.next(0)
        assert t3 is t1
        assert t3.status == URLStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_skips_non_pending(self):
        tasks = [
            URLTask(url="https://example.com/0", status=URLStatus.DONE),
            URLTask(url="https://example.com/1"),
        ]
        q = TaskQueue(tasks)
        t = await q.next(0)
        assert t.url == "https://example.com/1"

    @pytest.mark.asyncio
    async def test_concurrent_safety(self):
        tasks = [URLTask(url=f"https://example.com/{i}") for i in range(100)]
        q = TaskQueue(tasks)
        claimed = []

        async def worker(wid):
            while True:
                t = await q.next(wid)
                if not t:
                    break
                claimed.append(t.url)

        await asyncio.gather(*[worker(i) for i in range(5)])
        assert len(claimed) == 100
        assert len(set(claimed)) == 100


# ── extract_dom ──────────────────────────────────────────────────────────────

class TestExtractDom:
    def test_basic_extraction(self):
        html = """
        <html><head><title>Test</title>
        <meta name="description" content="A test page">
        </head><body>
        <h1>Main Heading</h1>
        <p>This is a paragraph with enough text to pass the threshold.</p>
        <a href="https://example.com/link1">Link One</a>
        </body></html>
        """
        result = extract_dom(html, "https://test.com", "Test")
        assert result["title"] == "Test"
        assert "Main Heading" in result["headings"]
        assert len(result["paragraphs"]) >= 1
        assert result["meta"]["description"] == "A test page"

    def test_strips_scripts_and_styles(self):
        html = """
        <html><body>
        <script>alert('bad')</script>
        <style>.x{color:red}</style>
        <h1>Clean Heading</h1>
        <p>Clean paragraph with some meaningful content here.</p>
        </body></html>
        """
        result = extract_dom(html, "https://test.com", "Test")
        assert "Clean Heading" in result["headings"]
        assert "alert" not in str(result)

    def test_table_extraction(self):
        html = """
        <html><body>
        <table>
        <tr><th>Name</th><th>Price</th></tr>
        <tr><td>Widget</td><td>$10</td></tr>
        </table>
        </body></html>
        """
        result = extract_dom(html, "https://test.com", "Test")
        assert len(result["tables"]) == 1
        assert result["tables"][0][0] == ["Name", "Price"]

    def test_empty_html(self):
        result = extract_dom("<html><body></body></html>", "https://test.com", "Test")
        assert result["title"] == "Test"
        assert result["headings"] == []
        assert result["paragraphs"] == []

    def test_link_extraction(self):
        html = """
        <html><body>
        <a href="https://example.com/page1">Page One</a>
        <a href="/relative">Relative</a>
        <a href="https://example.com/page2">Page Two</a>
        </body></html>
        """
        result = extract_dom(html, "https://test.com", "Test")
        assert len(result["links"]) == 2
        assert result["links"][0]["text"] == "Page One"


# ── BulkJobConfig ────────────────────────────────────────────────────────────

class TestBulkJobConfig:
    def test_defaults(self):
        config = BulkJobConfig(urls=["https://a.com"], prompt="test")
        assert config.max_workers == 3
        assert config.max_retries == 2
        assert config.per_domain_delay_s == 2.0
        assert config.rotation_interval == 10
        assert config.output_format == "json"
        assert config.use_ai_extraction is False
        assert config.block_resources is True

    def test_custom_values(self):
        config = BulkJobConfig(
            urls=["https://a.com", "https://b.com"],
            prompt="scrape prices",
            output_format="csv",
            max_workers=5,
            max_retries=3,
            per_domain_delay_s=1.0,
            rotation_interval=20,
            use_ai_extraction=True,
            block_resources=False,
        )
        assert config.max_workers == 5
        assert config.use_ai_extraction is True
        assert config.block_resources is False


# ── BulkEngine ───────────────────────────────────────────────────────────────

class TestBulkEngine:
    def _mock_proxy_manager(self):
        pm = MagicMock()
        pm.get_best_proxy.return_value = None
        pm.mark_proxy_success = MagicMock()
        pm.mark_proxy_failure = MagicMock()
        return pm

    @pytest.mark.asyncio
    async def test_create_job(self):
        engine = BulkEngine(proxy_manager=self._mock_proxy_manager())
        config = BulkJobConfig(urls=["https://a.com", "https://b.com"], prompt="test")
        state = await engine.create_job(config)
        assert len(state.tasks) == 2
        assert state.tasks[0].url == "https://a.com"
        assert state.job_id

    @pytest.mark.asyncio
    async def test_cancel_job(self):
        engine = BulkEngine(proxy_manager=self._mock_proxy_manager())
        config = BulkJobConfig(urls=["https://a.com"], prompt="test")
        state = await engine.create_job(config)
        assert engine.cancel_job(state.job_id) is True
        assert engine.cancel_job("nonexistent") is False
        assert state.cancelled is True

    @pytest.mark.asyncio
    async def test_get_job(self):
        engine = BulkEngine(proxy_manager=self._mock_proxy_manager())
        config = BulkJobConfig(urls=["https://a.com"], prompt="test")
        state = await engine.create_job(config)
        found = engine.get_job(state.job_id)
        assert found is state
        assert engine.get_job("nonexistent") is None

    def test_next_task_legacy(self):
        engine = BulkEngine(proxy_manager=self._mock_proxy_manager())
        config = BulkJobConfig(urls=["https://a.com", "https://b.com"], prompt="test")
        state = BulkJobState(
            job_id="test",
            config=config,
            tasks=[URLTask(url=u) for u in config.urls],
        )
        t1 = engine._next_task(state, worker_id=0)
        assert t1 is not None
        assert t1.url == "https://a.com"
        assert t1.status == URLStatus.IN_PROGRESS

        t2 = engine._next_task(state, worker_id=1)
        assert t2 is not None
        assert t2.url == "https://b.com"

        t3 = engine._next_task(state, worker_id=0)
        assert t3 is None

    def test_aggregate_results(self):
        engine = BulkEngine(proxy_manager=self._mock_proxy_manager())
        config = BulkJobConfig(urls=["https://a.com", "https://b.com", "https://c.com"], prompt="test")
        state = BulkJobState(job_id="test", config=config, tasks=[])
        state.tasks = [
            URLTask(url="https://a.com", status=URLStatus.DONE, result={"url": "https://a.com", "title": "A"}),
            URLTask(url="https://b.com", status=URLStatus.FAILED, error="timeout", attempts=2),
            URLTask(url="https://c.com", status=URLStatus.DONE, result={"url": "https://c.com", "title": "C"}),
        ]
        results = engine._aggregate(state)
        assert len(results) == 3
        assert results[0]["title"] == "A"
        assert results[1]["status"] == "failed"
        assert results[2]["title"] == "C"

    def test_format_results_json(self):
        engine = BulkEngine(proxy_manager=self._mock_proxy_manager())
        results = [{"url": "https://a.com", "data": "test"}]
        output = engine._format_results(results, "json")
        parsed = json.loads(output)
        assert len(parsed) == 1

    def test_format_results_csv(self):
        engine = BulkEngine(proxy_manager=self._mock_proxy_manager())
        results = [{"url": "https://a.com", "title": "Page A"}, {"url": "https://b.com", "title": "Page B"}]
        output = engine._format_results(results, "csv")
        assert "url" in output
        assert "https://a.com" in output
        assert "Page B" in output

    def test_format_results_md(self):
        engine = BulkEngine(proxy_manager=self._mock_proxy_manager())
        results = [{"url": "https://a.com", "title": "Page A", "extracted": "some data"}]
        output = engine._format_results(results, "md")
        assert "# Bulk Scrape Results" in output
        assert "Page A" in output

    def test_format_results_empty(self):
        engine = BulkEngine(proxy_manager=self._mock_proxy_manager())
        assert engine._format_results([], "csv") == ""


# ── Checkpoint ───────────────────────────────────────────────────────────────

class TestCheckpoint:
    def test_save_and_load(self, tmp_path):
        engine = BulkEngine(proxy_manager=MagicMock())
        config = BulkJobConfig(urls=["https://a.com", "https://b.com"], prompt="test")
        state = BulkJobState(job_id="cp-test", config=config, tasks=[])
        state.tasks = [
            URLTask(url="https://a.com", status=URLStatus.DONE, result={"title": "A"}, attempts=1),
            URLTask(url="https://b.com", status=URLStatus.FAILED, error="blocked", attempts=2),
        ]

        with patch("backend.bulk_engine.OUTPUT_DIR", tmp_path):
            engine._save_checkpoint(state)
            loaded = engine._load_checkpoint("cp-test")

        assert loaded is not None
        assert loaded.job_id == "cp-test"
        assert len(loaded.tasks) == 2
        assert loaded.tasks[0].status == URLStatus.DONE
        assert loaded.tasks[1].status == URLStatus.FAILED
        assert loaded.tasks[1].error == "blocked"
        assert loaded.config.prompt == "test"

    def test_load_nonexistent(self, tmp_path):
        engine = BulkEngine(proxy_manager=MagicMock())
        with patch("backend.bulk_engine.OUTPUT_DIR", tmp_path):
            assert engine._load_checkpoint("nonexistent") is None


# ── BotDetectedError ─────────────────────────────────────────────────────────

class TestBotDetectedError:
    def test_is_exception(self):
        err = BotDetectedError("blocked by DataDome")
        assert str(err) == "blocked by DataDome"
        assert isinstance(err, Exception)

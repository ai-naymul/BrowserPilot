"""Tests for BrowserPilot's synchronous structured-scrape endpoint.

The browser and Gemini are mocked — no real browser, no API calls.
"""
import os

os.environ.setdefault("GOOGLE_API_KEY", "test")

from types import SimpleNamespace
from unittest.mock import MagicMock

import backend.main as main
from backend.main import StructuredScrapeRequest, scrape_structured, _parse_rows


_ROWS_JSON = '[{"name": "Nike", "price": "$120"}, {"name": "Adidas", "price": "$95"}]'


class _FakePage:
    async def goto(self, url, wait_until=None, timeout=None):
        if "bad" in url:
            raise RuntimeError("navigation blocked")

    async def wait_for_timeout(self, ms):
        return None

    async def title(self):
        return "Shoes"

    async def content(self):
        return "<html><body><h1>Shoes</h1><p>content</p></body></html>"


class _FakeBC:
    def __init__(self, *a, **k):
        self.page = _FakePage()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def _wire(monkeypatch, text=_ROWS_JSON):
    monkeypatch.setattr(main, "BrowserController", _FakeBC)
    monkeypatch.setattr(main, "MODEL",
                        SimpleNamespace(generate_content=MagicMock(return_value=SimpleNamespace(text=text))))
    monkeypatch.setattr(main.smart_proxy_manager, "get_best_proxy", lambda: None)


# ── pure parser ──────────────────────────────────────────────────────────────
def test_parse_rows_array_aware():
    assert _parse_rows('[{"a": 1}]') == [{"a": 1}]
    assert _parse_rows('Here you go: [{"a": 1}, {"a": 2}] done') == [{"a": 1}, {"a": 2}]
    assert _parse_rows('no array here') == []
    assert _parse_rows('[not json]') == []
    assert _parse_rows("") == []
    # non-dict members are filtered out
    assert _parse_rows('[{"a":1}, 5, "x"]') == [{"a": 1}]


# ── endpoint ─────────────────────────────────────────────────────────────────
async def test_scrape_structured_happy(monkeypatch):
    _wire(monkeypatch)
    out = await scrape_structured(StructuredScrapeRequest(
        urls=["https://nike.com/a", "https://adidas.com/b"], prompt="compare shoe prices"))
    assert out["success"] is True
    assert len(out["rows"]) == 4  # 2 rows per URL x 2 URLs
    assert all(r["_source_url"] in ("https://nike.com/a", "https://adidas.com/b") for r in out["rows"])
    assert "error" not in out


async def test_scrape_structured_no_urls(monkeypatch):
    _wire(monkeypatch)
    out = await scrape_structured(StructuredScrapeRequest(urls=["", "  "], prompt="x"))
    assert out["success"] is False
    assert "No URLs" in out["error"]


async def test_scrape_structured_per_url_error_is_not_fatal(monkeypatch):
    _wire(monkeypatch)
    out = await scrape_structured(StructuredScrapeRequest(
        urls=["https://good.com/a", "https://bad.com/b"], prompt="x"))
    assert out["success"] is True          # good URL still produced rows
    assert len(out["rows"]) == 2           # only the good URL
    assert "1 of 2 URL(s) failed" in out["error"]


async def test_scrape_structured_empty_extraction(monkeypatch):
    _wire(monkeypatch, text="[]")
    out = await scrape_structured(StructuredScrapeRequest(urls=["https://x.com"], prompt="x"))
    assert out["success"] is False
    assert out["rows"] == []


async def test_scrape_structured_respects_max_rows(monkeypatch):
    _wire(monkeypatch)
    out = await scrape_structured(StructuredScrapeRequest(
        urls=["https://a.com", "https://b.com"], prompt="x", max_rows=3))
    assert len(out["rows"]) == 3

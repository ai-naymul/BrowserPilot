"""Tests for the scrape -> render orchestration (render_from_scrape).

Both the BrowserPilot scrape HTTP call and the LLM are mocked — no network.
"""
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test")

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.api.routes import refine
from app.api.routes.refine import ScrapeRenderRequest, render_from_scrape


_GOOD_LLM_JSON = json.dumps({
    "task_description": "Shoe price comparison",
    "entities": [],
    "components": [
        {"type": "comparison_table", "props": {
            "data": [{"id": "nike", "name": "Nike", "price": "$120"},
                     {"id": "adidas", "name": "Adidas", "price": "$95"}],
            "columns": ["name", "price"]}},
    ],
    "layout": {"type": "grid", "columns": 2, "gap": 16},
})


def _fake_llm_response(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    """Stand-in for httpx.AsyncClient used as an async context manager."""
    def __init__(self, payload=None, exc=None):
        self._payload = payload
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, json=None):
        if self._exc:
            raise self._exc
        return _FakeResp(self._payload)


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr(refine, "enrich_entities_with_geocoding", AsyncMock(side_effect=lambda e: e))


def _mock_scrape(monkeypatch, payload=None, exc=None):
    monkeypatch.setattr(refine.httpx, "AsyncClient", lambda *a, **k: _FakeClient(payload=payload, exc=exc))


def _mock_llm_ok(monkeypatch):
    monkeypatch.setattr(refine.llm_client.chat.completions, "create",
                        AsyncMock(return_value=_fake_llm_response(_GOOD_LLM_JSON)))


@pytest.mark.asyncio
async def test_scrape_render_happy_path(monkeypatch):
    _mock_scrape(monkeypatch, payload={
        "success": True,
        "rows": [{"name": "Nike", "price": "$120"}, {"name": "Adidas", "price": "$95"}],
        "source": ["https://nike.com/x", "https://adidas.com/y"],  # BrowserPilot returns a list
    })
    _mock_llm_ok(monkeypatch)
    resp = await render_from_scrape(ScrapeRenderRequest(
        urls=["https://nike.com/x", "https://adidas.com/y"], question="compare prices"))
    assert resp.success is True
    assert resp.components and resp.components[0]["type"] == "comparison_table"


@pytest.mark.asyncio
async def test_no_urls_is_graceful(monkeypatch):
    resp = await render_from_scrape(ScrapeRenderRequest(urls=["  ", ""], question="q"))
    assert resp.success is False
    assert "at least one URL" in resp.error


@pytest.mark.asyncio
async def test_scrape_reports_failure(monkeypatch):
    _mock_scrape(monkeypatch, payload={"success": False, "error": "All URLs blocked"})
    resp = await render_from_scrape(ScrapeRenderRequest(urls=["https://x.com"], question="q"))
    assert resp.success is False
    assert "blocked" in resp.error


@pytest.mark.asyncio
async def test_scrape_empty_rows_is_graceful(monkeypatch):
    _mock_scrape(monkeypatch, payload={"success": True, "rows": []})
    resp = await render_from_scrape(ScrapeRenderRequest(urls=["https://x.com"], question="q"))
    assert resp.success is False
    assert "no data" in resp.error


@pytest.mark.asyncio
async def test_scraper_unreachable_is_graceful(monkeypatch):
    _mock_scrape(monkeypatch, exc=httpx.ConnectError("connection refused"))
    resp = await render_from_scrape(ScrapeRenderRequest(urls=["https://x.com"], question="q"))
    assert resp.success is False
    assert "Could not reach the scraper" in resp.error

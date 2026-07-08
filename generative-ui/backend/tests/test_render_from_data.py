"""Tests for the generalized, data-grounded render endpoint (render_from_data).

The LLM call and geocoding are mocked — these run with no network and no key.
"""
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test")  # satisfy import-time guard

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.routes import refine
from app.api.routes.refine import (
    DataRenderRequest,
    _bound_render_rows,
    _extract_json_object,
    render_from_data,
)


def _fake_response(content: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


_GOOD_LLM_JSON = json.dumps({
    "task_description": "Shoe price comparison",
    "entities": [{
        "id": "nike-air", "type": "Product", "public_identifier": "Nike Air",
        "attributes": [{"name": "price", "value": "$120", "widget": "currency", "function": "display"}],
    }],
    "components": [
        {"type": "bar_chart", "props": {
            "data": [{"label": "Nike Air", "price": 120}, {"label": "Adidas", "price": 95}],
            "bars": [{"dataKey": "price", "name": "Price"}]}},
        {"type": "comparison_table", "props": {
            "data": [{"id": "nike-air", "name": "Nike Air", "price": "$120"},
                     {"id": "adidas", "name": "Adidas", "price": "$95"}],
            "columns": ["name", "price"]}},
    ],
    "layout": {"type": "grid", "columns": 2, "gap": 16},
})


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    # geocoding would hit Nominatim — keep tests offline
    monkeypatch.setattr(refine, "enrich_entities_with_geocoding", AsyncMock(side_effect=lambda e: e))


def _mock_llm(monkeypatch, *responses):
    create = AsyncMock(side_effect=[_fake_response(r) for r in responses]) if len(responses) > 1 \
        else AsyncMock(return_value=_fake_response(responses[0]))
    monkeypatch.setattr(refine.llm_client.chat.completions, "create", create)
    return create


# ── pure helpers ─────────────────────────────────────────────────────────────
def test_bound_render_rows_caps_count_and_cell_length():
    rows = [{"k": "x" * 1000} for _ in range(100)]
    bounded = _bound_render_rows(rows)
    assert len(bounded) == refine._MAX_RENDER_ROWS
    assert len(bounded[0]["k"]) == refine._MAX_RENDER_CELL_CHARS


def test_extract_json_object_strips_fences_and_prose():
    assert _extract_json_object('```json\n{"a":1}\n```') == '{"a":1}'
    assert _extract_json_object('Sure, here: {"a":1} — enjoy') == '{"a":1}'
    assert _extract_json_object('no json here') == 'no json here'


# ── endpoint behavior ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_render_happy_path(monkeypatch):
    _mock_llm(monkeypatch, _GOOD_LLM_JSON)
    resp = await render_from_data(DataRenderRequest(
        rows=[{"name": "Nike Air", "price": "$120"}, {"name": "Adidas", "price": "$95"}],
        question="compare these shoe prices", source="nike.com"))
    assert resp.success is True
    assert resp.components and len(resp.components) == 2
    assert {"bar_chart", "comparison_table"} <= {c["type"] for c in resp.components}
    assert resp.layout["columns"] == 2
    assert "entities" in (resp.data_model or {})


@pytest.mark.asyncio
async def test_render_empty_rows_returns_error(monkeypatch):
    _mock_llm(monkeypatch, _GOOD_LLM_JSON)  # should never be called
    resp = await render_from_data(DataRenderRequest(rows=[], question="anything"))
    assert resp.success is False
    assert "No data" in (resp.error or "")


@pytest.mark.asyncio
async def test_render_repairs_bad_json_with_one_retry(monkeypatch):
    create = _mock_llm(monkeypatch, "oops not json at all", _GOOD_LLM_JSON)
    resp = await render_from_data(DataRenderRequest(
        rows=[{"name": "X", "price": "$1"}], question="q"))
    assert resp.success is True
    assert create.await_count == 2  # retried exactly once


@pytest.mark.asyncio
async def test_render_invalid_component_falls_back_not_crash(monkeypatch):
    bad = json.dumps({"task_description": "t", "entities": [],
                      "components": [{"type": "bar_chart", "props": {}}]})  # missing required data/bars
    _mock_llm(monkeypatch, bad)
    resp = await render_from_data(DataRenderRequest(rows=[{"a": 1}], question="q"))
    assert resp.success is True
    # invalid spec becomes a visible 'text' fallback node, never a blank/crash
    assert resp.components and resp.components[0]["type"] == "text"

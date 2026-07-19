"""Tests for the API-key gate on the money-spending endpoints."""
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test")

import pytest
from fastapi import HTTPException

from app.main import require_api_key


def test_auth_disabled_when_key_unset(monkeypatch):
    monkeypatch.delenv("GENUI_API_KEY", raising=False)
    # No configured key -> auth is a no-op (local dev), any request passes.
    assert require_api_key(x_api_key=None) is None
    assert require_api_key(x_api_key="whatever") is None


def test_auth_rejects_missing_or_wrong_key(monkeypatch):
    monkeypatch.setenv("GENUI_API_KEY", "s3cret")
    with pytest.raises(HTTPException) as e1:
        require_api_key(x_api_key=None)
    assert e1.value.status_code == 401
    with pytest.raises(HTTPException) as e2:
        require_api_key(x_api_key="nope")
    assert e2.value.status_code == 401


def test_auth_accepts_correct_key(monkeypatch):
    monkeypatch.setenv("GENUI_API_KEY", "s3cret")
    assert require_api_key(x_api_key="s3cret") is None

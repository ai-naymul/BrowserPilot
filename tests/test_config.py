import os
import importlib
import pytest


def reload_config():
    import backend.config as cfg
    importlib.reload(cfg)
    return cfg


def test_get_random_ua_returns_modern_chrome_by_default():
    cfg = reload_config()
    ua = cfg.get_random_ua()
    assert "Mozilla/5.0" in ua
    assert "Chrome/9" not in ua  # not Chrome 9x


def test_get_random_ua_uses_env_pool(monkeypatch):
    monkeypatch.setenv("BROWSER_USER_AGENT_POOL", '["TestAgent/1.0"]')
    cfg = reload_config()
    assert cfg.get_random_ua() == "TestAgent/1.0"


def test_gemini_model_name_default():
    cfg = reload_config()
    # Default must be a stable GA model, not a dated preview that Google will retire.
    assert cfg.GEMINI_MODEL_NAME == "gemini-2.5-flash"


def test_gemini_model_name_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL_NAME", "gemini-custom-model")
    cfg = reload_config()
    assert cfg.GEMINI_MODEL_NAME == "gemini-custom-model"


def test_navigation_settle_default():
    cfg = reload_config()
    assert cfg.NAVIGATION_SETTLE_S == 2.0


def test_navigation_settle_from_env(monkeypatch):
    monkeypatch.setenv("NAVIGATION_SETTLE_S", "3.5")
    cfg = reload_config()
    assert cfg.NAVIGATION_SETTLE_S == 3.5


def test_extraction_max_chars_default():
    cfg = reload_config()
    assert cfg.EXTRACTION_MAX_CHARS == 12000


def test_ws_base_url_default():
    cfg = reload_config()
    assert cfg.WS_BASE_URL == "ws://localhost:8000"


def test_ws_base_url_from_env(monkeypatch):
    monkeypatch.setenv("WS_BASE_URL", "wss://myprod.example.com")
    cfg = reload_config()
    assert cfg.WS_BASE_URL == "wss://myprod.example.com"


def test_ua_pool_has_only_modern_browsers():
    cfg = reload_config()
    for ua in cfg.STEALTH_USER_AGENT_POOL:
        assert "Chrome/9" not in ua
        assert "Firefox/9" not in ua

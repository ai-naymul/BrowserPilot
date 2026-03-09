import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.proxy_manager import ProxyInfo, ProxyHealth, SmartProxyManager


@pytest.fixture
def healthy_proxy():
    return ProxyInfo(
        server="http://proxy1.example.com:8080",
        username="user1",
        password="pass1",
        location="US",
    )


@pytest.fixture
def failed_proxy():
    proxy = ProxyInfo(
        server="http://proxy2.example.com:8080",
        username="user2",
        password="pass2",
        location="DE",
    )
    proxy.health = ProxyHealth.FAILED
    proxy.consecutive_failures = 5
    proxy.failure_count = 10
    return proxy


@pytest.fixture
def blocked_proxy():
    proxy = ProxyInfo(
        server="http://proxy3.example.com:8080",
        location="GB",
    )
    proxy.health = ProxyHealth.BLOCKED
    proxy.blocked_sites.add("https://example.com")
    return proxy


@pytest.fixture
def degraded_proxy():
    proxy = ProxyInfo(
        server="http://proxy4.example.com:8080",
        location="FR",
    )
    proxy.health = ProxyHealth.DEGRADED
    proxy.consecutive_failures = 3
    proxy.failure_count = 3
    return proxy


@pytest.fixture
def proxy_manager_with_proxies(monkeypatch):
    test_proxies = [
        {"server": "http://fast-proxy.com:8080", "username": "u1", "password": "p1", "location": "US"},
        {"server": "http://medium-proxy.com:8080", "username": "u2", "password": "p2", "location": "DE"},
        {"server": "http://slow-proxy.com:8080", "location": "JP"},
    ]
    monkeypatch.setenv("SCRAPER_PROXIES", json.dumps(test_proxies))
    return SmartProxyManager()


@pytest.fixture
def empty_proxy_manager(monkeypatch):
    monkeypatch.setenv("SCRAPER_PROXIES", "[]")
    return SmartProxyManager()

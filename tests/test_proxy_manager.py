import json
import pytest
from backend.proxy_manager import ProxyInfo, ProxyHealth, SmartProxyManager


class TestProxyInfo:
    """Tests for the ProxyInfo dataclass."""

    def test_default_values(self):
        proxy = ProxyInfo(server="http://localhost:8080")
        assert proxy.health == ProxyHealth.HEALTHY
        assert proxy.success_count == 0
        assert proxy.failure_count == 0
        assert proxy.blocked_sites == set()
        assert proxy.location == "unknown"

    def test_success_rate_no_requests(self):
        proxy = ProxyInfo(server="http://localhost:8080")
        assert proxy.success_rate == 1.0

    def test_success_rate_with_requests(self):
        proxy = ProxyInfo(server="http://localhost:8080")
        proxy.success_count = 7
        proxy.failure_count = 3
        assert proxy.success_rate == 0.7

    def test_success_rate_all_failures(self):
        proxy = ProxyInfo(server="http://localhost:8080")
        proxy.failure_count = 5
        assert proxy.success_rate == 0.0

    def test_to_playwright_dict_with_auth(self):
        proxy = ProxyInfo(server="http://proxy:8080", username="user", password="pass")
        result = proxy.to_playwright_dict()
        assert result == {"server": "http://proxy:8080", "username": "user", "password": "pass"}

    def test_to_playwright_dict_without_auth(self):
        proxy = ProxyInfo(server="http://proxy:8080")
        result = proxy.to_playwright_dict()
        assert result == {"server": "http://proxy:8080"}

    def test_blocked_sites_not_shared_between_instances(self):
        proxy1 = ProxyInfo(server="http://a:8080")
        proxy2 = ProxyInfo(server="http://b:8080")
        proxy1.blocked_sites.add("https://site.com")
        assert "https://site.com" not in proxy2.blocked_sites


class TestSmartProxyManager:
    """Tests for the SmartProxyManager class."""

    def test_loads_proxies_from_env(self, proxy_manager_with_proxies):
        assert len(proxy_manager_with_proxies.proxies) == 3

    def test_loads_string_proxies(self, monkeypatch):
        monkeypatch.setenv("SCRAPER_PROXIES", json.dumps(["http://a:8080", "http://b:8080"]))
        manager = SmartProxyManager()
        assert len(manager.proxies) == 2
        assert manager.proxies[0].server == "http://a:8080"

    def test_empty_proxy_list(self, empty_proxy_manager):
        assert len(empty_proxy_manager.proxies) == 0

    def test_get_best_proxy_returns_proxy(self, proxy_manager_with_proxies):
        proxy = proxy_manager_with_proxies.get_best_proxy()
        assert proxy is not None
        assert proxy.server in ["http://fast-proxy.com:8080", "http://medium-proxy.com:8080", "http://slow-proxy.com:8080"]

    def test_get_best_proxy_empty_pool(self, empty_proxy_manager):
        assert empty_proxy_manager.get_best_proxy() is None

    def test_get_best_proxy_skips_failed(self, proxy_manager_with_proxies):
        for p in proxy_manager_with_proxies.proxies:
            p.health = ProxyHealth.FAILED
        # All failed — should return None
        assert proxy_manager_with_proxies.get_best_proxy() is None

    def test_get_best_proxy_excludes_blocked_site(self, proxy_manager_with_proxies):
        proxies = proxy_manager_with_proxies.proxies
        proxies[0].blocked_sites.add("https://blocked-site.com")
        proxies[1].blocked_sites.add("https://blocked-site.com")
        # proxy[2] is NOT blocked — should be returned
        result = proxy_manager_with_proxies.get_best_proxy(exclude_blocked_for="https://blocked-site.com")
        assert result is not None
        assert result.server == "http://slow-proxy.com:8080"

    def test_get_best_proxy_prefers_higher_success_rate(self, proxy_manager_with_proxies):
        proxies = proxy_manager_with_proxies.proxies
        proxies[0].success_count = 10
        proxies[0].failure_count = 0
        proxies[1].success_count = 5
        proxies[1].failure_count = 5
        proxies[2].success_count = 0
        proxies[2].failure_count = 10

        best = proxy_manager_with_proxies.get_best_proxy()
        assert best.server == "http://fast-proxy.com:8080"

    def test_get_best_proxy_resets_failures_when_all_exhausted(self, proxy_manager_with_proxies):
        for p in proxy_manager_with_proxies.proxies:
            p.consecutive_failures = 5
            p.health = ProxyHealth.DEGRADED
        # Should reset consecutive_failures and return a proxy
        result = proxy_manager_with_proxies.get_best_proxy()
        assert result is not None

    def test_mark_proxy_success(self, healthy_proxy):
        manager = SmartProxyManager.__new__(SmartProxyManager)
        manager.proxies = [healthy_proxy]
        manager.mark_proxy_success(healthy_proxy, response_time=0.5)
        assert healthy_proxy.success_count == 1
        assert healthy_proxy.consecutive_failures == 0
        assert healthy_proxy.health == ProxyHealth.HEALTHY
        assert healthy_proxy.response_time == 0.5

    def test_mark_proxy_failure_cloudflare(self, healthy_proxy):
        manager = SmartProxyManager.__new__(SmartProxyManager)
        manager.proxies = [healthy_proxy]
        manager.max_consecutive_failures = 3
        manager.mark_proxy_failure(healthy_proxy, site_url="https://target.com", detection_type="cloudflare")
        assert healthy_proxy.failure_count == 1
        assert healthy_proxy.health == ProxyHealth.BLOCKED
        assert "https://target.com" in healthy_proxy.blocked_sites

    def test_mark_proxy_failure_generic(self, healthy_proxy):
        manager = SmartProxyManager.__new__(SmartProxyManager)
        manager.proxies = [healthy_proxy]
        manager.max_consecutive_failures = 3
        manager.mark_proxy_failure(healthy_proxy, detection_type="unknown")
        assert healthy_proxy.health == ProxyHealth.DEGRADED

    def test_mark_proxy_failure_consecutive_leads_to_failed(self, healthy_proxy):
        manager = SmartProxyManager.__new__(SmartProxyManager)
        manager.proxies = [healthy_proxy]
        manager.max_consecutive_failures = 3
        for _ in range(3):
            manager.mark_proxy_failure(healthy_proxy)
        assert healthy_proxy.health == ProxyHealth.FAILED

    def test_get_proxy_stats(self, proxy_manager_with_proxies):
        stats = proxy_manager_with_proxies.get_proxy_stats()
        assert stats["total"] == 3
        assert stats["healthy"] == 3
        assert stats["failed"] == 0
        assert stats["available"] == 3

    def test_get_proxy_stats_empty(self, empty_proxy_manager):
        stats = empty_proxy_manager.get_proxy_stats()
        assert stats["total"] == 0
        assert stats["available"] == 0

    def test_get_proxy_stats_mixed_health(self, proxy_manager_with_proxies):
        proxies = proxy_manager_with_proxies.proxies
        proxies[0].health = ProxyHealth.HEALTHY
        proxies[1].health = ProxyHealth.BLOCKED
        proxies[2].health = ProxyHealth.FAILED
        stats = proxy_manager_with_proxies.get_proxy_stats()
        assert stats["healthy"] == 1
        assert stats["blocked"] == 1
        assert stats["failed"] == 1
    
    def test_mark_proxy_success_resets_after_failures(self, degraded_proxy):
        manager = SmartProxyManager.__new__(SmartProxyManager)
        manager.proxies = [degraded_proxy]
        manager.mark_proxy_success(degraded_proxy)
        assert degraded_proxy.consecutive_failures == 0
        assert degraded_proxy.health == ProxyHealth.HEALTHY
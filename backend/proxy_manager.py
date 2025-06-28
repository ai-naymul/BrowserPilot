import os, json, random

# rotate the proxy if its being deteceted by cloudflare or other antibot system

class ProxyManager:
    def __init__(self):
        # list can be provided through env or file; feel free to extend
        source = os.getenv("SCRAPER_PROXIES", "[]")
        self.proxies = json.loads(source)

    def get_proxy(self) -> dict | None:
        """
        Returns a Playwright-style proxy dict:
        {"server": "...", "username": "...", "password": "..."}
        or None if no proxies configured.
        """
        if not self.proxies:
            return None
        return random.choice(self.proxies)
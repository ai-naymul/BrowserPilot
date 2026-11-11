"""Access control for the BrowserPilot API.

Without this, every endpoint is open to anyone who can reach the port — including
any web page you happen to visit, which can POST /job (burning your Gemini key
and driving a real browser through your proxies) and open /stream/{id} to send
mouse and keyboard events into that browser.

Two independent gates, both fail-closed:

1. Origin gate (always on). Browsers attach `Origin` to cross-site requests, so
   rejecting foreign origins kills the drive-by attack with no config and no
   effect on curl/CLI clients (they send no Origin). CORS alone does not do this:
   it hides the *response*, not the side effect.
2. Token gate (opt-in via BROWSERPILOT_TOKEN). Required for anything exposed
   beyond loopback, where the Origin gate protects nothing — any local process,
   LAN peer, or port-forward can send a request with no Origin header at all.

Set BROWSERPILOT_TOKEN and put it in localStorage.browserpilot_token (or build
the frontend with VITE_API_TOKEN) before exposing the port.
"""

from __future__ import annotations

import os
import secrets
from urllib.parse import parse_qs

TOKEN: str = os.getenv("BROWSERPILOT_TOKEN", "")

# Extra origins to accept, comma separated, e.g. "https://pilot.example.com".
ALLOWED_ORIGINS: list[str] = [
    o.strip().rstrip("/")
    for o in os.getenv("BROWSERPILOT_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "[::1]", "::1"}

# Fail-closed: everything is protected unless it is one of these. The SPA shell
# must load before the browser can read its token out of localStorage.
_PUBLIC_PATHS = {"/", "/health", "/favicon.ico", "/vite.svg", "/robots.txt"}
_PUBLIC_PREFIXES = ("/assets/",)

_TOKEN_HEADER = "x-api-token"


def origin_ok(origin: str | None) -> bool:
    """True if `origin` may talk to this API. No Origin header = non-browser client."""
    if not origin:
        return True
    origin = origin.rstrip("/")
    if origin in ALLOWED_ORIGINS:
        return True
    host = origin.split("://", 1)[-1]
    if host.startswith("["):  # IPv6 literal: [::1]:8000
        host = host.split("]", 1)[0] + "]"
    elif ":" in host:
        host = host.split(":", 1)[0]
    return host in _LOOPBACK_HOSTS


def token_ok(supplied: str | None) -> bool:
    """True if `supplied` satisfies the token gate (or no token is configured)."""
    if not TOKEN:
        return True
    return bool(supplied) and secrets.compare_digest(supplied, TOKEN)


def path_is_public(path: str) -> bool:
    return path in _PUBLIC_PATHS or path.startswith(_PUBLIC_PREFIXES)


def _headers(scope) -> dict[str, str]:
    return {
        k.decode("latin-1").lower(): v.decode("latin-1")
        for k, v in scope.get("headers") or []
    }


def _query_token(scope) -> str | None:
    # WebSockets cannot set headers from the browser, so the token may ride in
    # ?token=... for /ws and /stream. HTTP accepts it too, for <a href> downloads.
    qs = parse_qs(scope.get("query_string", b"").decode("latin-1"))
    vals = qs.get("token")
    return vals[0] if vals else None


class LocalOnlyMiddleware:
    """ASGI gate for HTTP and WebSocket. Rejects before the app ever sees it."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        headers = _headers(scope)
        if not origin_ok(headers.get("origin")):
            return await self._reject(scope, send, 403, "origin not allowed")

        if not path_is_public(scope.get("path", "")):
            supplied = headers.get(_TOKEN_HEADER) or _query_token(scope)
            if not token_ok(supplied):
                return await self._reject(scope, send, 401, "missing or invalid API token")

        return await self.app(scope, receive, send)

    @staticmethod
    async def _reject(scope, send, status: int, detail: str):
        if scope["type"] == "websocket":
            # Closing before accept fails the handshake — no socket is opened.
            await send({"type": "websocket.close", "code": 1008})
            return
        body = ('{"detail":"%s"}' % detail).encode()
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({"type": "http.response.body", "body": body})

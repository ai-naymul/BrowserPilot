"""Access-control tests for backend/security.py.

Dependency-free on purpose: the gate is the only thing standing between a web
page you visit and a browser under your control, so it must be testable without
installing patchright/gemini/fastapi. Drives the middleware with a hand-rolled
ASGI harness and a trivial inner app.

Run: python tests/test_security.py     (or: pytest tests/test_security.py)
"""

import asyncio
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backend.security as security
from backend.security import LocalOnlyMiddleware, origin_ok, token_ok, path_is_public


async def _inner_app(scope, receive, send):
    """Records that the request reached the app, then answers 200."""
    scope["_reached_app"] = True
    if scope["type"] == "websocket":
        await send({"type": "websocket.accept"})
        return
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


def call(path="/job", *, method="POST", origin=None, token=None, query="", ws=False):
    """Run one request through the middleware; returns (status_or_code, reached_app)."""
    scope = {
        "type": "websocket" if ws else "http",
        "path": path,
        "method": method,
        "query_string": query.encode(),
        "headers": [],
    }
    if origin:
        scope["headers"].append((b"origin", origin.encode()))
    if token:
        scope["headers"].append((b"x-api-token", token.encode()))

    sent = []

    async def send(msg):
        sent.append(msg)

    async def receive():
        return {"type": "http.disconnect"}

    asyncio.run(LocalOnlyMiddleware(_inner_app)(scope, receive, send))

    reached = scope.get("_reached_app", False)
    if ws:
        code = sent[0].get("code", 0) if sent and sent[0]["type"] == "websocket.close" else 0
        return code, reached
    return sent[0]["status"], reached


# ── Origin gate: always on, no configuration ─────────────────────────────────

def test_foreign_origin_rejected():
    status, reached = call(origin="https://evil.example")
    assert status == 403, status
    assert not reached


def test_localhost_origin_allowed():
    for o in ("http://localhost:8000", "http://127.0.0.1:5173", "http://localhost:5173"):
        status, reached = call(origin=o)
        assert (status, reached) == (200, True), (o, status, reached)


def test_no_origin_allowed_for_cli_clients():
    # curl sends no Origin; blocking it would break every documented curl example.
    assert call()[0] == 200


def test_websocket_foreign_origin_closed_before_accept():
    code, reached = call(ws=True, origin="https://evil.example")
    assert code == 1008, code
    assert not reached


# ── Token gate: opt-in via BROWSERPILOT_TOKEN ────────────────────────────────

def _with_token(value):
    os.environ["BROWSERPILOT_TOKEN"] = value
    importlib.reload(security)
    return security


def test_token_required_when_configured():
    sec = _with_token("s3cret")
    try:
        assert sec.LocalOnlyMiddleware  # reloaded module is the one under test
        # no token → 401, never reaches the app
        status, reached = _run_with(sec, token=None)
        assert (status, reached) == (401, False), (status, reached)
        # right token → 200
        assert _run_with(sec, token="s3cret") == (200, True)
        # wrong token → 401
        assert _run_with(sec, token="nope")[0] == 401
        # ?token= works (WebSocket handshakes and <a href> downloads cannot set headers)
        assert _run_with(sec, query="token=s3cret") == (200, True)
        # WebSocket with no token → closed with 1008, not accepted
        assert _run_with(sec, ws=True)[0] == 1008
        assert _run_with(sec, ws=True, query="token=s3cret") == (0, True)
    finally:
        os.environ.pop("BROWSERPILOT_TOKEN", None)
        importlib.reload(security)


def _run_with(sec, *, token=None, query="", ws=False):
    """Same as call(), but against a freshly reloaded security module."""
    scope = {
        "type": "websocket" if ws else "http",
        "path": "/job",
        "method": "POST",
        "query_string": query.encode(),
        "headers": [],
    }
    if token:
        scope["headers"].append((b"x-api-token", token.encode()))
    sent = []

    async def send(msg):
        sent.append(msg)

    async def receive():
        return {"type": "http.disconnect"}

    asyncio.run(sec.LocalOnlyMiddleware(_inner_app)(scope, receive, send))
    reached = scope.get("_reached_app", False)
    if ws:
        code = sent[0].get("code", 0) if sent and sent[0]["type"] == "websocket.close" else 0
        return code, reached
    return sent[0]["status"], reached


# ── Public paths: the SPA shell must load before it can hold a token ─────────

def test_public_paths_need_no_token():
    sec = _with_token("s3cret")
    try:
        for p in ("/", "/assets/index-abc.js", "/favicon.ico"):
            scope = {"type": "http", "path": p, "method": "GET", "query_string": b"", "headers": []}
            sent = []

            async def send(msg, _sent=sent):
                _sent.append(msg)

            async def receive():
                return {"type": "http.disconnect"}

            asyncio.run(sec.LocalOnlyMiddleware(_inner_app)(scope, receive, send))
            assert sent[0]["status"] == 200, (p, sent[0])
        assert path_is_public("/") and path_is_public("/assets/x.js")
        assert not path_is_public("/job") and not path_is_public("/download/abc")
    finally:
        os.environ.pop("BROWSERPILOT_TOKEN", None)
        importlib.reload(security)


def test_helpers():
    assert origin_ok(None) and origin_ok("http://localhost:8000")
    assert not origin_ok("https://evil.example")
    assert origin_ok("http://[::1]:8000")
    assert token_ok("anything")  # no token configured → open
    assert security.TOKEN == ""


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"\n{'FAILED' if failed else 'OK'} — {failed} failure(s)")
    sys.exit(1 if failed else 0)

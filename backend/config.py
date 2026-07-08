import os
import platform
import random
import json
from dotenv import load_dotenv

load_dotenv()

# ── AI Model ──────────────────────────────────────────────────────────────────
GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# ── User-Agent pool ──────────────────────────────────────────────────────────
# IMPORTANT: Only Chrome/Edge UAs. We run Chromium — Firefox UAs create
# detectable inconsistencies (window.chrome exists, vendor="Google Inc.").
# Grouped by OS so get_random_ua() can match the actual host OS.
#
# DYNAMIC VERSION: Auto-detects Playwright's bundled Chromium major version
# and generates UAs for (bundled, bundled-1, bundled-2) to avoid version
# mismatch between the claimed UA and the actual Chromium binary. Anti-bot
# systems cross-check CDP browser version with the UA string.

_UA_TEMPLATES: dict[str, str] = {
    "windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36",
    "windows_edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36 Edg/{version}.0.0.0",
    "mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36",
    "linux": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36",
}


def _detect_chromium_major() -> int:
    """Detect Playwright's bundled Chromium major version from the installed binary."""
    chromium_override = os.getenv("CHROMIUM_MAJOR_VERSION")
    if chromium_override and chromium_override.isdigit():
        return int(chromium_override)
    import re as _re
    import subprocess as _sp
    import pathlib as _pl
    try:
        pw_cache = _pl.Path.home() / ".cache" / "ms-playwright"
        for d in sorted(pw_cache.iterdir(), reverse=True):
            if d.name.startswith("chromium-") and d.is_dir():
                for binary in [d / "chrome-linux64" / "chrome", d / "chrome-linux" / "chrome",
                               d / "chrome-win" / "chrome.exe",
                               d / "chrome-mac" / "Chromium.app" / "Contents" / "MacOS" / "Chromium"]:
                    if binary.exists():
                        r = _sp.run([str(binary), "--version"], capture_output=True, text=True, timeout=5)
                        m = _re.search(r"(\d+)\.", r.stdout)
                        if m:
                            return int(m.group(1))
                break
    except Exception:
        pass
    return 136


def _build_ua_pool() -> tuple[list[str], list[str], list[str]]:
    """Build UA pools dynamically from the detected Chromium version."""
    base = _detect_chromium_major()
    versions = [base, base - 1, base - 2]
    windows = []
    mac = []
    linux = []
    for v in versions:
        windows.append(_UA_TEMPLATES["windows"].format(version=v))
        mac.append(_UA_TEMPLATES["mac"].format(version=v))
        linux.append(_UA_TEMPLATES["linux"].format(version=v))
    windows.append(_UA_TEMPLATES["windows_edge"].format(version=base))
    return windows, mac, linux


_UA_POOL_WINDOWS, _UA_POOL_MAC, _UA_POOL_LINUX = _build_ua_pool()
STEALTH_USER_AGENT_POOL: list[str] = _UA_POOL_WINDOWS + _UA_POOL_MAC + _UA_POOL_LINUX


def _detect_host_os() -> str:
    system = platform.system()
    if system == "Darwin":
        return "mac"
    if system == "Linux":
        return "linux"
    return "windows"


def get_random_ua() -> str:
    """Return a Chrome UA matching the host OS. Override via BROWSER_USER_AGENT_POOL env (JSON array)."""
    custom = os.getenv("BROWSER_USER_AGENT_POOL")
    if custom:
        try:
            pool = json.loads(custom)
            if pool:
                return random.choice(pool)
        except (json.JSONDecodeError, IndexError):
            pass
    host_os = _detect_host_os()
    if host_os == "mac":
        return random.choice(_UA_POOL_MAC)
    if host_os == "linux":
        return random.choice(_UA_POOL_LINUX)
    return random.choice(_UA_POOL_WINDOWS)

# ── Viewport ──────────────────────────────────────────────────────────────────
BROWSER_VIEWPORT_WIDTH: int = int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1280"))
BROWSER_VIEWPORT_HEIGHT: int = int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "800"))

# ── Timing (seconds) ──────────────────────────────────────────────────────────
NAVIGATION_SETTLE_S: float = float(os.getenv("NAVIGATION_SETTLE_S", "2.0"))
CLICK_SETTLE_S: float = float(os.getenv("CLICK_SETTLE_S", "1.0"))
SCROLL_SETTLE_S: float = float(os.getenv("SCROLL_SETTLE_S", "1.0"))
INTERACTION_DELAY_S: float = float(os.getenv("INTERACTION_DELAY_S", "0.5"))
STREAM_POLL_INTERVAL_S: float = float(os.getenv("STREAM_POLL_INTERVAL_S", "0.1"))
PROXY_ROTATION_DELAY_S: float = float(os.getenv("PROXY_ROTATION_DELAY_S", "3.0"))
CAPTCHA_SETTLE_S: float = float(os.getenv("CAPTCHA_SETTLE_S", "3.0"))
STREAM_SESSION_TIMEOUT_S: float = float(os.getenv("STREAM_SESSION_TIMEOUT_S", "30.0"))

# ── Human behavior ────────────────────────────────────────────────────────────
HUMAN_TYPING_WPM_MIN: int = int(os.getenv("HUMAN_TYPING_WPM_MIN", "40"))
HUMAN_TYPING_WPM_MAX: int = int(os.getenv("HUMAN_TYPING_WPM_MAX", "80"))
HUMAN_TYPO_RATE: float = float(os.getenv("HUMAN_TYPO_RATE", "0.03"))
HUMAN_MOUSE_STEPS: int = int(os.getenv("HUMAN_MOUSE_STEPS", "20"))

# ── Browser retries ───────────────────────────────────────────────────────────
MAX_PROXY_RETRIES: int = int(os.getenv("MAX_PROXY_RETRIES", "5"))
MAX_CAPTCHA_ATTEMPTS: int = int(os.getenv("MAX_CAPTCHA_ATTEMPTS", "3"))

# ── Content extraction ────────────────────────────────────────────────────────
EXTRACTION_MAX_CHARS: int = int(os.getenv("EXTRACTION_MAX_CHARS", "12000"))
EXTRACTION_FALLBACK_CHARS: int = int(os.getenv("EXTRACTION_FALLBACK_CHARS", "8000"))
EXTRACTION_STRUCTURE_CHARS: int = int(os.getenv("EXTRACTION_STRUCTURE_CHARS", "2000"))

# ── Network ───────────────────────────────────────────────────────────────────
WS_BASE_URL: str = os.getenv("WS_BASE_URL", "ws://localhost:8000")
VNC_DEFAULT_PORT: int = int(os.getenv("VNC_DEFAULT_PORT", "5901"))
VNC_WS_PORT_OFFSET: int = int(os.getenv("VNC_WS_PORT_OFFSET", "1000"))

# ── Ghost Mode ───────────────────────────────────────────────────────────────
GHOST_MODE_ENABLED: bool = os.getenv("GHOST_MODE_ENABLED", "1") == "1"
GHOST_MODE_HUMAN_BEHAVIOR: bool = os.getenv("GHOST_MODE_HUMAN_BEHAVIOR", "1") == "1"
GHOST_MODE_SEED: str = os.getenv("GHOST_MODE_SEED", "")

# ── Xvfb ─────────────────────────────────────────────────────────────────────
XVFB_DISPLAY_START: int = int(os.getenv("XVFB_DISPLAY_START", "99"))
XVFB_DISPLAY_END: int = int(os.getenv("XVFB_DISPLAY_END", "110"))

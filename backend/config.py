import os
import random
import json
from dotenv import load_dotenv

load_dotenv()

# ── AI Model ──────────────────────────────────────────────────────────────────
GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# ── User-Agent pool (Chrome 120-130, Firefox 121-128, Edge 130) ───────────────
STEALTH_USER_AGENT_POOL: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
]

def get_random_ua() -> str:
    """Return a random modern user agent. Override pool via BROWSER_USER_AGENT_POOL env (JSON array)."""
    custom = os.getenv("BROWSER_USER_AGENT_POOL")
    if custom:
        try:
            pool = json.loads(custom)
            if pool:
                return random.choice(pool)
        except (json.JSONDecodeError, IndexError):
            pass
    return random.choice(STEALTH_USER_AGENT_POOL)

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

# ── Xvfb ─────────────────────────────────────────────────────────────────────
XVFB_DISPLAY_START: int = int(os.getenv("XVFB_DISPLAY_START", "99"))
XVFB_DISPLAY_END: int = int(os.getenv("XVFB_DISPLAY_END", "110"))

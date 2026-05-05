import hashlib
import struct
from dataclasses import dataclass
from typing import Optional

from backend.config import get_random_ua, _detect_chromium_major, _UA_TEMPLATES
from backend.proxy_manager import get_locale_for_country


@dataclass
class FingerprintProfile:
    seed: str
    user_agent: str
    viewport_width: int
    viewport_height: int
    screen_width: int
    screen_height: int
    device_pixel_ratio: float
    color_depth: int
    timezone: str
    locale: str
    languages: list[str]
    hardware_concurrency: int
    device_memory: int
    webrtc_policy: str


_WINDOWS_SCREENS = [
    (1920, 1080), (1366, 768), (2560, 1440), (1536, 864),
    (1440, 900), (1280, 720), (1600, 900),
]

_MAC_SCREENS = [
    (1440, 900), (1680, 1050), (2560, 1600), (1920, 1080),
    (2560, 1440), (1280, 800),
]

_LINUX_SCREENS = [
    (1920, 1080), (2560, 1440), (1366, 768), (1600, 900),
    (3840, 2160),
]

_HARDWARE_CONCURRENCY_VALUES = [4, 6, 8, 12, 16]
_DEVICE_MEMORY_VALUES = [4, 8, 8, 8, 16]

_WINDOWS_DPR = [1.0, 1.0, 1.25, 1.5]
_MAC_DPR = [1.0, 2.0, 2.0, 2.0]
_LINUX_DPR = [1.0, 1.0, 1.0, 2.0]


class _SeededRandom:
    """Deterministic PRNG from a seed string."""

    def __init__(self, seed: str):
        h = hashlib.sha256(seed.encode()).digest()
        self._state = struct.unpack("<IIII", h[:16])
        self._idx = 0

    def _next(self) -> int:
        a, b, c, d = self._state
        t = b ^ (b << 11) & 0xFFFFFFFF
        self._state = (d, a, b, c)
        result = (d ^ (d >> 19) ^ t ^ (t >> 8)) & 0xFFFFFFFF
        self._state = (result, a, b, c)
        return result

    def randint(self, lo: int, hi: int) -> int:
        return lo + (self._next() % (hi - lo + 1))

    def choice(self, seq: list):
        return seq[self._next() % len(seq)]


def _detect_os_from_ua(ua: str) -> str:
    if "Macintosh" in ua or "Mac OS" in ua:
        return "mac"
    if "Linux" in ua:
        return "linux"
    return "windows"


def _locale_to_languages(locale: str) -> list[str]:
    lang = locale.split("-")[0]
    if lang == locale:
        return [locale]
    return [locale, lang]


def generate_profile(
    seed: Optional[str] = None,
    proxy_country: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> FingerprintProfile:
    """Generate a coherent fingerprint profile from a seed.

    If seed is None, generates a random one. All profile values are determined
    by the seed for reproducibility. If proxy_country is provided, timezone and
    locale are geo-matched.
    """
    if seed is None:
        import secrets
        seed = secrets.token_hex(16)

    rng = _SeededRandom(seed)

    if user_agent is None:
        ua_pool_key = rng.choice(["windows", "mac", "linux"])
        base_version = _detect_chromium_major()
        version_offset = rng.randint(0, 2)
        version = base_version - version_offset
        ua = _UA_TEMPLATES[ua_pool_key].format(version=version)
    else:
        ua = user_agent
        ua_pool_key = _detect_os_from_ua(ua)

    os_type = ua_pool_key

    if os_type == "mac":
        screens = _MAC_SCREENS
        dpr_pool = _MAC_DPR
    elif os_type == "linux":
        screens = _LINUX_SCREENS
        dpr_pool = _LINUX_DPR
    else:
        screens = _WINDOWS_SCREENS
        dpr_pool = _WINDOWS_DPR

    screen_w, screen_h = rng.choice(screens)
    dpr = rng.choice(dpr_pool)
    color_depth = 24

    viewport_w = min(screen_w, screen_w - rng.randint(0, 100))
    viewport_h = min(screen_h - rng.randint(60, 140), screen_h)

    hw_conc = rng.choice(_HARDWARE_CONCURRENCY_VALUES)
    dev_mem = rng.choice(_DEVICE_MEMORY_VALUES)

    if proxy_country:
        locale, timezone = get_locale_for_country(proxy_country)
    else:
        locale = "en-US"
        timezone = "America/New_York"

    languages = _locale_to_languages(locale)

    return FingerprintProfile(
        seed=seed,
        user_agent=ua,
        viewport_width=viewport_w,
        viewport_height=viewport_h,
        screen_width=screen_w,
        screen_height=screen_h,
        device_pixel_ratio=dpr,
        color_depth=color_depth,
        timezone=timezone,
        locale=locale,
        languages=languages,
        hardware_concurrency=hw_conc,
        device_memory=dev_mem,
        webrtc_policy="disable_non_proxied_udp",
    )


def validate_coherence(profile: FingerprintProfile) -> list[str]:
    """Return list of coherence violations. Empty list = valid profile."""
    violations = []
    os_type = _detect_os_from_ua(profile.user_agent)

    if os_type == "mac":
        valid_screens = _MAC_SCREENS
        if profile.device_pixel_ratio not in [1.0, 2.0]:
            violations.append(f"Mac DPR {profile.device_pixel_ratio} not in [1.0, 2.0]")
    elif os_type == "linux":
        valid_screens = _LINUX_SCREENS
    else:
        valid_screens = _WINDOWS_SCREENS

    if (profile.screen_width, profile.screen_height) not in valid_screens:
        violations.append(
            f"Screen {profile.screen_width}x{profile.screen_height} not valid for {os_type}"
        )

    if profile.viewport_width > profile.screen_width:
        violations.append("viewport_width > screen_width")
    if profile.viewport_height > profile.screen_height:
        violations.append("viewport_height > screen_height")

    if profile.hardware_concurrency not in _HARDWARE_CONCURRENCY_VALUES:
        violations.append(f"hardware_concurrency {profile.hardware_concurrency} not in valid set")
    if profile.device_memory not in _DEVICE_MEMORY_VALUES:
        violations.append(f"device_memory {profile.device_memory} not in valid set")

    if profile.color_depth not in (24, 30):
        violations.append(f"color_depth {profile.color_depth} not in [24, 30]")

    return violations

import pytest
from backend.fingerprint_profile import (
    generate_profile,
    validate_coherence,
    FingerprintProfile,
    _detect_os_from_ua,
    _WINDOWS_SCREENS,
    _MAC_SCREENS,
    _LINUX_SCREENS,
)


def test_deterministic_same_seed():
    p1 = generate_profile(seed="fixed-seed-123")
    p2 = generate_profile(seed="fixed-seed-123")
    assert p1 == p2


def test_different_seeds_different_profiles():
    p1 = generate_profile(seed="seed-a")
    p2 = generate_profile(seed="seed-b")
    assert p1.user_agent != p2.user_agent or p1.viewport_width != p2.viewport_width


def test_random_seed_when_none():
    p1 = generate_profile(seed=None)
    p2 = generate_profile(seed=None)
    assert p1.seed != p2.seed


def test_profile_viewport_variety():
    viewports = set()
    for i in range(100):
        p = generate_profile(seed=f"variety-{i}")
        viewports.add((p.viewport_width, p.viewport_height))
    assert len(viewports) >= 5


def test_profile_ua_matches_host_and_binary():
    """UA must mirror the real host OS and Chromium version.

    navigator.platform and navigator.userAgentData are not spoofable under
    Patchright, so a UA that disagrees with either is a free detection signal.
    Variety across seeds is intentionally gone: it was only achievable by
    claiming a different OS or an older Chrome version than the binary.
    """
    from backend.config import _detect_host_os, _detect_chromium_major

    host = _detect_host_os()
    major = _detect_chromium_major()
    expected_marker = {"windows": "Windows NT", "mac": "Macintosh", "linux": "X11; Linux"}[host]

    for i in range(50):
        p = generate_profile(seed=f"ua-coherence-{i}")
        ua = p.user_agent
        assert expected_marker in ua, f"seed {i}: UA host mismatch: {ua}"
        assert f"Chrome/{major}." in ua, f"seed {i}: UA version != {major}: {ua}"
        assert "HeadlessChrome" not in ua, f"seed {i}: headless UA leaked: {ua}"


def test_coherence_all_generated_profiles():
    for i in range(50):
        p = generate_profile(seed=f"coherence-{i}")
        violations = validate_coherence(p)
        assert violations == [], f"Seed coherence-{i}: {violations}"


def test_coherence_mac_dpr():
    for i in range(50):
        p = generate_profile(seed=f"mac-dpr-{i}")
        if "Macintosh" in p.user_agent:
            assert p.device_pixel_ratio in [1.0, 2.0], f"Mac DPR: {p.device_pixel_ratio}"


def test_coherence_windows_resolution():
    for i in range(50):
        p = generate_profile(seed=f"win-res-{i}")
        if "Windows" in p.user_agent:
            assert (p.screen_width, p.screen_height) in _WINDOWS_SCREENS


def test_coherence_linux_resolution():
    for i in range(50):
        p = generate_profile(seed=f"linux-res-{i}")
        if "Linux" in p.user_agent:
            assert (p.screen_width, p.screen_height) in _LINUX_SCREENS


def test_coherence_viewport_smaller_than_screen():
    for i in range(50):
        p = generate_profile(seed=f"vp-{i}")
        assert p.viewport_width <= p.screen_width
        assert p.viewport_height <= p.screen_height


def test_coherence_hardware():
    for i in range(50):
        p = generate_profile(seed=f"hw-{i}")
        assert p.hardware_concurrency in [4, 6, 8, 12, 16]
        assert p.device_memory in [4, 8, 16]


def test_geo_matching_us():
    p = generate_profile(seed="geo-us", proxy_country="US")
    assert p.timezone == "America/New_York"
    assert p.locale == "en-US"
    assert "en-US" in p.languages


def test_geo_matching_de():
    p = generate_profile(seed="geo-de", proxy_country="DE")
    assert p.timezone == "Europe/Berlin"
    assert p.locale == "de-DE"
    assert "de-DE" in p.languages
    assert "de" in p.languages


def test_geo_matching_jp():
    p = generate_profile(seed="geo-jp", proxy_country="JP")
    assert p.timezone == "Asia/Tokyo"
    assert p.locale == "ja-JP"


def test_geo_matching_unknown_defaults_to_us():
    p = generate_profile(seed="geo-xx", proxy_country="ZZ")
    assert p.timezone == "America/New_York"
    assert p.locale == "en-US"


def test_webrtc_policy_always_set():
    p = generate_profile(seed="rtc")
    assert p.webrtc_policy == "disable_non_proxied_udp"


def test_custom_user_agent():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0"
    p = generate_profile(seed="custom-ua", user_agent=ua)
    assert p.user_agent == ua
    assert (p.screen_width, p.screen_height) in _WINDOWS_SCREENS


def test_detect_os_from_ua():
    assert _detect_os_from_ua("Mozilla/5.0 (Macintosh; Intel Mac OS X)") == "mac"
    assert _detect_os_from_ua("Mozilla/5.0 (X11; Linux x86_64)") == "linux"
    assert _detect_os_from_ua("Mozilla/5.0 (Windows NT 10.0)") == "windows"
    assert _detect_os_from_ua("Unknown") == "windows"

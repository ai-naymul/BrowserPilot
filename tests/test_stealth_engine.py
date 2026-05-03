# tests/test_stealth_engine.py
import re
import pytest
from backend.stealth_engine import get_stealth_script, get_ua_headers, _get_platform_for_ua


def test_script_patches_webdriver():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "navigator, 'webdriver'" in script
    assert "undefined" in script


def test_script_injects_window_chrome():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "window.chrome" in script
    assert "window.chrome.runtime" in script


def test_script_patches_permissions():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "Permissions.prototype.query" in script
    assert "notifications" in script


def test_script_patches_webgl():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "WebGLRenderingContext.prototype.getParameter" in script
    assert "37445" in script
    assert "37446" in script


def test_script_patches_navigator_plugins():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "navigator, 'plugins'" in script
    assert "Chrome PDF" in script


def test_script_patches_languages_default():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "navigator, 'languages'" in script
    assert "en-US" in script


def test_script_patches_languages_custom():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0", languages=["de-DE", "de"])
    assert "de-DE" in script


def test_script_patches_hardware_concurrency():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "navigator, 'hardwareConcurrency'" in script


def test_script_patches_device_memory():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "navigator, 'deviceMemory'" in script


def test_script_patches_canvas():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "HTMLCanvasElement.prototype.toDataURL" in script


def test_script_patches_audio_context():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "AudioBuffer.prototype.getChannelData" in script


def test_script_webgl_uses_custom_vendor():
    script = get_stealth_script(
        "Mozilla/5.0 Chrome/130.0.0.0",
        webgl_vendor="TestVendor Inc.",
        webgl_renderer="TestRenderer 9000",
    )
    assert "TestVendor Inc." in script
    assert "TestRenderer 9000" in script


def test_script_hardware_concurrency_in_valid_range():
    for _ in range(20):
        script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
        match = re.search(r"hardwareConcurrency.*?get.*?=> (\d+)", script, re.DOTALL)
        assert match, "hardwareConcurrency value not found"
        value = int(match.group(1))
        assert value in [4, 6, 8, 12, 16]


def test_script_device_memory_in_valid_range():
    for _ in range(20):
        script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
        match = re.search(r"deviceMemory.*?get.*?=> (\d+)", script, re.DOTALL)
        assert match
        value = int(match.group(1))
        assert value in [4, 8]


def test_headers_include_user_agent():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    headers = get_ua_headers(ua)
    assert headers["User-Agent"] == ua


def test_chrome_ua_gets_sec_ch_ua():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    headers = get_ua_headers(ua)
    assert "sec-ch-ua" in headers
    assert "130" in headers["sec-ch-ua"]
    assert "sec-ch-ua-mobile" in headers
    assert headers["sec-ch-ua-mobile"] == "?0"
    assert "sec-ch-ua-platform" in headers


def test_edge_ua_gets_sec_ch_ua_with_edge():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
    headers = get_ua_headers(ua)
    assert "Microsoft Edge" in headers["sec-ch-ua"]


def test_firefox_ua_no_sec_ch_ua():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
    headers = get_ua_headers(ua)
    assert "sec-ch-ua" not in headers
    assert headers["User-Agent"] == ua


def test_accept_language_always_present():
    ua = "Mozilla/5.0 Chrome/130.0.0.0"
    headers = get_ua_headers(ua)
    assert "Accept-Language" in headers


def test_platform_windows():
    assert _get_platform_for_ua("Mozilla/5.0 (Windows NT 10.0; Win64; x64)") == "Win32"


def test_platform_mac():
    assert _get_platform_for_ua("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)") == "MacIntel"


def test_platform_linux():
    assert _get_platform_for_ua("Mozilla/5.0 (X11; Linux x86_64)") == "Linux x86_64"


def test_platform_unknown_defaults_to_win32():
    assert _get_platform_for_ua("SomeUnknownBrowser/1.0") == "Win32"

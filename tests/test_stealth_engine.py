# tests/test_stealth_engine.py
import re
import pytest
from backend.stealth_engine import get_stealth_script, get_ua_headers, _get_platform_for_ua, _get_uad_platform_for_ua


def test_script_patches_webdriver():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    # Webdriver is removed by deleting from Navigator.prototype (not defining a getter)
    # so 'webdriver' in navigator returns false — the strongest possible evasion
    assert "Navigator.prototype" in script
    assert "webdriver" in script
    assert "delete" in script


def test_script_injects_window_chrome():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "window.chrome" in script
    assert "runtime" in script
    assert "Chrome/" in script  # conditional: only inject for Chrome UAs


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
    # Plugins overridden at Navigator.prototype level to defeat native-getter bypass detection
    assert "Navigator.prototype, 'plugins'" in script
    assert "Chrome PDF" in script
    assert "PluginArray.prototype" in script


def test_script_patches_languages_default():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "Navigator.prototype, 'languages'" in script
    assert "Navigator.prototype, 'language'" in script
    assert "en-US" in script


def test_script_patches_languages_custom():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0", languages=["de-DE", "de"])
    assert "de-DE" in script


def test_script_patches_hardware_concurrency():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "Navigator.prototype, 'hardwareConcurrency'" in script


def test_script_patches_device_memory():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "Navigator.prototype, 'deviceMemory'" in script


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


def test_script_hardware_concurrency_uses_real_cpu_count():
    import os
    real_cores = os.cpu_count() or 8
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    match = re.search(r"_getHW = function\(\) \{ return (\d+);", script)
    assert match, "hardwareConcurrency value not found"
    value = int(match.group(1))
    assert value == real_cores


def test_script_device_memory_default():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    match = re.search(r"_getDM = function\(\) \{ return (\d+);", script)
    assert match
    value = int(match.group(1))
    assert value == 8


def test_script_hardware_concurrency_custom_override():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0", hardware_concurrency=16)
    match = re.search(r"_getHW = function\(\) \{ return (\d+);", script)
    assert match
    assert int(match.group(1)) == 16


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


def test_script_fixes_outer_height():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "outerHeight" in script
    assert "innerHeight + 80" in script


def test_script_fixes_screen_position():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "screenX" in script
    assert "screenY" in script
    # screenX and screenY must be non-zero across many runs
    for _ in range(20):
        s = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
        match_x = re.search(r"_screenX = (\d+)", s)
        assert match_x, "screenX not found"
        assert int(match_x.group(1)) >= 20


def test_script_injects_navigator_connection():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "navigator.connection" in script
    assert "effectiveType" in script
    assert "'4g'" in script


def test_script_injects_media_devices():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "enumerateDevices" in script
    assert "audioinput" in script
    assert "videoinput" in script


def test_script_injects_battery_api():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "getBattery" in script
    assert "charging" in script


def test_script_injects_mime_types():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "mimeTypes" in script
    assert "MimeTypeArray.prototype" in script


def test_script_sets_stack_trace_limit():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "stackTraceLimit" in script


def test_script_has_tostring_shield():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "Function.prototype.toString" in script
    assert "_stealthRegisterNative" in script
    assert "[native code]" in script


def test_script_cleans_automation_artifacts():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "chrome_asyncScriptInfo" in script
    assert "__selenium_evaluate" in script
    assert "domAutomationController" in script
    assert "cdc_" in script


def test_script_patches_canvas_toblob():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "toBlob" in script


def test_script_cleans_up_stealth_utility():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "delete window._stealthRegisterNative" in script


def test_script_registers_patched_functions_as_native():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    # query, getParameter x2, toDataURL, getChannelData, toBlob, getBattery
    assert script.count("_stealthRegisterNative") >= 5


def test_script_patches_navigator_language_singular():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "Navigator.prototype, 'language'" in script
    assert "'en-US'" in script


def test_script_patches_navigator_language_custom():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0", languages=["fr-FR", "fr"])
    assert "'fr-FR'" in script


def test_script_freezes_languages_array():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "Object.freeze" in script


def test_script_patches_user_agent_data():
    ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    script = get_stealth_script(ua)
    assert "userAgentData" in script
    assert "getHighEntropyValues" in script
    assert "'Linux'" in script
    assert "130" in script


def test_script_user_agent_data_windows():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    script = get_stealth_script(ua)
    assert "'Windows'" in script


def test_script_battery_uses_battery_manager_prototype():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "BatteryManager.prototype" in script
    assert "Object.create(BatteryManager.prototype)" in script
    assert "EventTarget.prototype" in script


def test_script_plugins_have_mime_cross_refs():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "enabledPlugin" in script
    assert "application/pdf" in script
    assert "MimeType.prototype" in script


def test_script_mimetypes_have_named_access():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "MimeTypeArray.prototype" in script
    assert "namedItem" in script


def test_script_plugins_five_entries():
    script = get_stealth_script("Mozilla/5.0 Chrome/130.0.0.0")
    assert "PDF Viewer" in script
    assert "Chrome PDF Viewer" in script
    assert "Chromium PDF Viewer" in script
    assert "Microsoft Edge PDF Viewer" in script
    assert "WebKit built-in PDF" in script


def test_get_uad_platform():
    from backend.stealth_engine import _get_uad_platform_for_ua
    assert _get_uad_platform_for_ua("Mozilla/5.0 (Windows NT 10.0; Win64; x64)") == "Windows"
    assert _get_uad_platform_for_ua("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)") == "macOS"
    assert _get_uad_platform_for_ua("Mozilla/5.0 (X11; Linux x86_64)") == "Linux"
    assert _get_uad_platform_for_ua("SomeUnknownBrowser/1.0") == "Windows"

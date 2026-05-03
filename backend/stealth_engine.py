import json
import random
from typing import Optional

_WEBGL_PROFILES: list[tuple[str, str]] = [
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Apple", "Apple M1"),
    ("Apple", "Apple M2"),
]


def _get_platform_for_ua(ua: str) -> str:
    if "Win64" in ua or "WOW64" in ua or "Windows" in ua:
        return "Win32"
    if "Macintosh" in ua or "Mac OS X" in ua:
        return "MacIntel"
    if "Linux" in ua:
        return "Linux x86_64"
    return "Win32"


def _get_sec_ch_ua(ua: str) -> tuple[Optional[str], Optional[str]]:
    if "Chrome/" not in ua:
        return None, None
    version = ua.split("Chrome/")[1].split(".")[0]
    if "Windows" in ua:
        platform = '"Windows"'
    elif "Macintosh" in ua or "Mac OS X" in ua:
        platform = '"macOS"'
    else:
        platform = '"Linux"'
    if "Edg/" in ua:
        edge_ver = ua.split("Edg/")[1].split(".")[0]
        sec = f'"Not/A)Brand";v="8", "Chromium";v="{version}", "Microsoft Edge";v="{edge_ver}"'
    else:
        sec = f'"Not/A)Brand";v="8", "Chromium";v="{version}", "Google Chrome";v="{version}"'
    return sec, platform


def get_ua_headers(user_agent: str) -> dict[str, str]:
    """Return HTTP headers consistent with the given User-Agent string."""
    headers: dict[str, str] = {"User-Agent": user_agent}
    sec_ch_ua, sec_ch_platform = _get_sec_ch_ua(user_agent)
    if sec_ch_ua:
        headers["sec-ch-ua"] = sec_ch_ua
        headers["sec-ch-ua-mobile"] = "?0"
        headers["sec-ch-ua-platform"] = sec_ch_platform
    headers["Accept-Language"] = "en-US,en;q=0.9"
    return headers


def get_stealth_script(
    user_agent: str,
    languages: Optional[list[str]] = None,
    webgl_vendor: Optional[str] = None,
    webgl_renderer: Optional[str] = None,
    hardware_concurrency: Optional[int] = None,
    device_memory: Optional[int] = None,
) -> str:
    """Generate a JavaScript stealth script for Playwright page.add_init_script()."""
    if languages is None:
        languages = ["en-US", "en"]
    if webgl_vendor is None or webgl_renderer is None:
        webgl_vendor, webgl_renderer = random.choice(_WEBGL_PROFILES)
    if hardware_concurrency is None:
        hardware_concurrency = random.choice([4, 6, 8, 12, 16])
    if device_memory is None:
        device_memory = random.choice([4, 8])

    platform = _get_platform_for_ua(user_agent)
    languages_json = json.dumps(languages)
    canvas_noise = round(random.uniform(0.0001, 0.0003), 6)

    return f"""(function() {{
  // 1. Remove navigator.webdriver (Playwright/Selenium detection vector #1)
  Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});

  // 2. Realistic plugin list
  Object.defineProperty(navigator, 'plugins', {{
    get: () => {{
      const plugins = [
        {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
        {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
        {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }},
      ];
      Object.setPrototypeOf(plugins, PluginArray.prototype);
      return plugins;
    }},
  }});

  // 3. Languages matching proxy geo
  Object.defineProperty(navigator, 'languages', {{
    get: () => {languages_json},
  }});

  // 4. Platform matching UA OS
  Object.defineProperty(navigator, 'platform', {{
    get: () => '{platform}',
  }});

  // 5. Hardware fingerprint
  Object.defineProperty(navigator, 'hardwareConcurrency', {{
    get: () => {hardware_concurrency},
  }});
  Object.defineProperty(navigator, 'deviceMemory', {{
    get: () => {device_memory},
  }});

  // 6. window.chrome runtime — Cloudflare check #1
  // window.chrome.runtime must exist for Cloudflare fingerprint checks
  if (!window.chrome) {{
    window.chrome = {{
      app: {{
        isInstalled: false,
        InstallState: {{ DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }},
        RunningState: {{ CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }},
        getDetails: function() {{}},
        getIsInstalled: function() {{ return false; }},
        runningState: function() {{ return 'cannot_run'; }},
      }},
      csi: function() {{}},
      loadTimes: function() {{ return {{}}; }},
      runtime: {{
        OnInstalledReason: {{ CHROME_UPDATE: 'chrome_update', INSTALL: 'install', UPDATE: 'update' }},
        PlatformOs: {{ ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', WIN: 'win' }},
        id: undefined,
        connect: function() {{}},
        sendMessage: function() {{}},
      }},
    }};
  }}

  // 7. Permissions.query — headless returns 'denied', real Chrome returns 'default'
  if (window.Permissions && window.Permissions.prototype.query) {{
    const _originalQuery = window.Permissions.prototype.query;
    window.Permissions.prototype.query = function(parameters) {{
      if (parameters.name === 'notifications') {{
        return Promise.resolve({{ state: Notification.permission, onchange: null }});
      }}
      return _originalQuery.apply(this, [parameters]);
    }};
  }}

  // 8. WebGL fingerprint spoofing
  (function() {{
    const _getParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
      if (parameter === 37445) return '{webgl_vendor}';
      if (parameter === 37446) return '{webgl_renderer}';
      return _getParam.apply(this, [parameter]);
    }};
    if (typeof WebGL2RenderingContext !== 'undefined') {{
      const _getParam2 = WebGL2RenderingContext.prototype.getParameter;
      WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) return '{webgl_vendor}';
        if (parameter === 37446) return '{webgl_renderer}';
        return _getParam2.apply(this, [parameter]);
      }};
    }}
  }})();

  // 9. Canvas fingerprint noise
  (function() {{
    const _noise = {canvas_noise};
    const _origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
      const ctx = this.getContext('2d');
      if (ctx && this.width > 0 && this.height > 0) {{
        const imageData = ctx.getImageData(0, 0, this.width, this.height);
        const d = imageData.data;
        for (let i = 0; i < d.length; i += 4) {{
          d[i]   = Math.min(255, d[i]   + Math.floor(_noise * 255));
          d[i+1] = Math.min(255, d[i+1] + Math.floor(_noise * 255));
          d[i+2] = Math.min(255, d[i+2] + Math.floor(_noise * 255));
        }}
        ctx.putImageData(imageData, 0, 0);
      }}
      return _origToDataURL.apply(this, [type, quality]);
    }};
  }})();

  // 10. AudioContext fingerprint noise
  (function() {{
    const _origGetChannelData = AudioBuffer.prototype.getChannelData;
    AudioBuffer.prototype.getChannelData = function() {{
      const array = _origGetChannelData.apply(this, arguments);
      for (let i = 0; i < array.length; i += 100) {{
        array[i] += (Math.random() - 0.5) * 0.0001;
      }}
      return array;
    }};
  }})();
}})();"""

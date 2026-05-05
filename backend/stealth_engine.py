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


def _get_uad_platform_for_ua(ua: str) -> str:
    """Return navigator.userAgentData.platform value (different from navigator.platform)."""
    if "Windows" in ua:
        return "Windows"
    if "Macintosh" in ua or "Mac OS X" in ua:
        return "macOS"
    if "Linux" in ua:
        return "Linux"
    return "Windows"


def _get_uad_platform_version(ua: str) -> str:
    if "Windows" in ua:
        return "15.0.0"
    if "Macintosh" in ua or "Mac OS X" in ua:
        return "14.5.0"
    return "6.5.0"


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
    """Generate a JavaScript stealth script for Playwright's add_init_script().

    NOTE: With patchright (default runtime), this script is NOT needed and NOT used.
    Patchright + full Chromium provides native stealth (no CDP detection, real plugins,
    real codecs, real window.chrome). This function exists as a fallback for environments
    using regular Playwright where add_init_script is functional.
    """
    if languages is None:
        languages = ["en-US", "en"]
    if webgl_vendor is None or webgl_renderer is None:
        webgl_vendor, webgl_renderer = random.choice(_WEBGL_PROFILES)
    if hardware_concurrency is None:
        import os as _os
        try:
            real_cores = _os.cpu_count() or 8
        except Exception:
            real_cores = 8
        hardware_concurrency = real_cores
    if device_memory is None:
        device_memory = 8

    platform = _get_platform_for_ua(user_agent)
    uad_platform = _get_uad_platform_for_ua(user_agent)
    uad_platform_version = _get_uad_platform_version(user_agent)
    languages_json = json.dumps(languages)
    primary_language = languages[0] if languages else "en-US"
    chrome_version = ""
    chrome_full_version = ""
    if "Chrome/" in user_agent:
        chrome_full_version = user_agent.split("Chrome/")[1].split(" ")[0]
        chrome_version = chrome_full_version.split(".")[0]
    canvas_noise = round(random.uniform(0.0001, 0.0003), 6)
    screen_x = random.randint(20, 280)
    screen_y = random.randint(20, 120)
    connection_rtt = random.choice([25, 50, 75, 100, 150])
    connection_downlink = round(random.uniform(5.0, 25.0), 1)
    battery_level = random.randint(40, 99)

    return f"""(function() {{
  // ===================================================================
  // PATCH 0: Function.prototype.toString shield (MUST BE FIRST)
  // ===================================================================
  // When we override native functions with JS getters/functions,
  // calling .toString() on them returns "() => {{ ... }}" instead of
  // "function get plugins() {{ [native code] }}". Pixelscan's
  // tamperedFunctions check and CreepJS lie detector both flag this.
  // This shield intercepts toString calls on our patched functions
  // and returns the native-looking string.
  (function() {{
    const _nativeToStringFunc = Function.prototype.toString;
    const _patchedToString = new WeakSet();

    function _registerNative(fn, name) {{
      if (typeof fn === 'function') {{
        _patchedToString.add(fn);
        fn._nativeName = name || '';
      }}
      return fn;
    }}

    const _handler = {{
      apply: function(target, thisArg, args) {{
        if (_patchedToString.has(thisArg)) {{
          return 'function ' + (thisArg._nativeName || '') + '() {{ [native code] }}';
        }}
        return Reflect.apply(target, thisArg, args);
      }},
    }};

    Function.prototype.toString = new Proxy(_nativeToStringFunc, _handler);
    _patchedToString.add(Function.prototype.toString);
    Function.prototype.toString._nativeName = 'toString';

    // Expose _registerNative for use by later patches
    window._stealthRegisterNative = _registerNative;
  }})();

  // ===================================================================
  // PATCH 0b: Clean automation artifacts from window/document
  // ===================================================================
  (function() {{
    // ChromeDriver artifacts
    const cdcProps = Object.getOwnPropertyNames(window).filter(p => p.match(/^cdc_|^\\$cdc_/));
    cdcProps.forEach(p => {{ try {{ delete window[p]; }} catch(e) {{}} }});
    // Selenium artifacts
    try {{ delete document.$chrome_asyncScriptInfo; }} catch(e) {{}}
    try {{ delete window.__selenium_evaluate; }} catch(e) {{}}
    try {{ delete window.__selenium_unwrapped; }} catch(e) {{}}
    try {{ delete window.__webdriver_script_fn; }} catch(e) {{}}
    try {{ delete window.__lastWatirAlert; }} catch(e) {{}}
    try {{ delete window.__webdriver_evaluate; }} catch(e) {{}}
    try {{ delete window.domAutomation; }} catch(e) {{}}
    try {{ delete window.domAutomationController; }} catch(e) {{}}
  }})();

  // ===================================================================
  // PATCH 0c: Neutralize CDP console serialization traps
  // ===================================================================
  // When Runtime.enable is active (Playwright's CDP), V8 Inspector serializes
  // all console.* arguments, invoking getter traps that detect automation.
  // We wrap console methods to serialize args to primitives first, preventing
  // custom getters from firing during CDP serialization.
  (function() {{
    const _safeSerialize = function(arg) {{
      if (arg === null || arg === undefined) return arg;
      const t = typeof arg;
      if (t === 'string' || t === 'number' || t === 'boolean' || t === 'bigint') return arg;
      if (t === 'symbol') return arg.toString();
      if (t === 'function') return arg;
      try {{ return JSON.parse(JSON.stringify(arg)); }} catch(e) {{ return String(arg); }}
    }};
    ['debug', 'log', 'info', 'warn', 'error', 'trace', 'dir', 'table'].forEach(function(method) {{
      const _orig = console[method];
      if (!_orig) return;
      console[method] = function() {{
        const safe = [];
        for (let i = 0; i < arguments.length; i++) safe.push(_safeSerialize(arguments[i]));
        return _orig.apply(console, safe);
      }};
      if (window._stealthRegisterNative) window._stealthRegisterNative(console[method], method);
    }});
  }})();

  // ===================================================================
  // PATCH 1: Remove navigator.webdriver
  // ===================================================================
  // Delete from prototype so 'webdriver' in navigator returns false
  try {{ delete Navigator.prototype['webdriver']; }} catch(e) {{}}

  // 2. Realistic plugin+mimeType list with full bidirectional cross-references
  // Pixelscan deep checks: instanceof Plugin/PluginArray, MimeType.enabledPlugin back-ref,
  // mimeTypes['application/pdf'] named access, toString() === "[object Plugin]"
  (function() {{
    const _pluginMimeData = [
      {{
        name: 'PDF Viewer',
        filename: 'internal-pdf-viewer',
        description: 'Portable Document Format',
        mimes: [
          {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
          {{ type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
        ],
      }},
      {{
        name: 'Chrome PDF Viewer',
        filename: 'internal-pdf-viewer',
        description: 'Portable Document Format',
        mimes: [
          {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
          {{ type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
        ],
      }},
      {{
        name: 'Chromium PDF Viewer',
        filename: 'internal-pdf-viewer',
        description: 'Portable Document Format',
        mimes: [
          {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
          {{ type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
        ],
      }},
      {{
        name: 'Microsoft Edge PDF Viewer',
        filename: 'internal-pdf-viewer',
        description: 'Portable Document Format',
        mimes: [
          {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
          {{ type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
        ],
      }},
      {{
        name: 'WebKit built-in PDF',
        filename: 'internal-pdf-viewer',
        description: 'Portable Document Format',
        mimes: [
          {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
          {{ type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
        ],
      }},
    ];

    // Build all MimeType objects and Plugin objects with cross-refs
    const _allMimeTypes = [];
    const _mimeByType = {{}};

    // Cached singleton so every access returns the same object identity
    let _cachedPluginArray = null;
    let _cachedMimeTypeArray = null;

    function buildPlugins() {{
      if (_cachedPluginArray) return _cachedPluginArray;

      const pluginArr = Object.create(PluginArray.prototype);
      _pluginMimeData.forEach(function(pd, pi) {{
        const plugin = Object.create(Plugin.prototype);
        Object.defineProperty(plugin, 'name', {{ value: pd.name, enumerable: true, configurable: true }});
        Object.defineProperty(plugin, 'filename', {{ value: pd.filename, enumerable: true, configurable: true }});
        Object.defineProperty(plugin, 'description', {{ value: pd.description, enumerable: true, configurable: true }});
        Object.defineProperty(plugin, 'length', {{ value: pd.mimes.length, enumerable: true, configurable: true }});

        pd.mimes.forEach(function(md, mi) {{
          const mimeType = Object.create(MimeType.prototype);
          Object.defineProperty(mimeType, 'type', {{ value: md.type, enumerable: true, configurable: true }});
          Object.defineProperty(mimeType, 'suffixes', {{ value: md.suffixes, enumerable: true, configurable: true }});
          Object.defineProperty(mimeType, 'description', {{ value: md.description, enumerable: true, configurable: true }});
          Object.defineProperty(mimeType, 'enabledPlugin', {{ value: plugin, enumerable: true, configurable: true }});
          Object.defineProperty(plugin, mi, {{ value: mimeType, enumerable: false, configurable: true }});
          Object.defineProperty(plugin, md.type, {{ value: mimeType, enumerable: false, configurable: true }});
          _allMimeTypes.push(mimeType);
          if (!_mimeByType[md.type]) _mimeByType[md.type] = mimeType;
        }});

        plugin.item = function(i) {{ return this[i] || null; }};
        plugin.namedItem = function(n) {{ return this[n] || null; }};
        plugin[Symbol.iterator] = function*() {{ for (let i = 0; i < pd.mimes.length; i++) yield this[i]; }};

        Object.defineProperty(pluginArr, pi, {{ value: plugin, enumerable: true, configurable: true }});
        Object.defineProperty(pluginArr, pd.name, {{ value: plugin, enumerable: false, configurable: true }});
      }});

      Object.defineProperty(pluginArr, 'length', {{ value: _pluginMimeData.length, enumerable: true, configurable: true }});
      pluginArr.item = function(i) {{ return this[i] || null; }};
      pluginArr.namedItem = function(name) {{ return this[name] || null; }};
      pluginArr.refresh = function() {{}};
      pluginArr[Symbol.iterator] = function*() {{ for (let i = 0; i < _pluginMimeData.length; i++) yield this[i]; }};

      _cachedPluginArray = pluginArr;
      return pluginArr;
    }}

    function buildMimeTypes() {{
      if (_cachedMimeTypeArray) return _cachedMimeTypeArray;
      buildPlugins();
      const mtArr = Object.create(MimeTypeArray.prototype);
      const uniqueMimes = [];
      const seen = new Set();
      _allMimeTypes.forEach(function(mt) {{
        const t = mt.type;
        if (!seen.has(t)) {{ seen.add(t); uniqueMimes.push(mt); }}
      }});
      uniqueMimes.forEach(function(mt, i) {{
        Object.defineProperty(mtArr, i, {{ value: mt, enumerable: true, configurable: true }});
        Object.defineProperty(mtArr, mt.type, {{ value: mt, enumerable: false, configurable: true }});
      }});
      Object.defineProperty(mtArr, 'length', {{ value: uniqueMimes.length, enumerable: true, configurable: true }});
      mtArr.item = function(i) {{ return this[i] || null; }};
      mtArr.namedItem = function(name) {{ return this[name] || null; }};
      mtArr[Symbol.iterator] = function*() {{ for (let i = 0; i < uniqueMimes.length; i++) yield this[i]; }};
      _cachedMimeTypeArray = mtArr;
      return mtArr;
    }}

    if (window._stealthRegisterNative) {{
      window._stealthRegisterNative(buildPlugins, 'get plugins');
      window._stealthRegisterNative(buildMimeTypes, 'get mimeTypes');
    }}
    try {{
      Object.defineProperty(Navigator.prototype, 'plugins', {{
        get: buildPlugins,
        configurable: true,
        enumerable: true,
      }});
    }} catch(e) {{}}
    try {{
      Object.defineProperty(Navigator.prototype, 'mimeTypes', {{
        get: buildMimeTypes,
        configurable: true,
        enumerable: true,
      }});
    }} catch(e) {{}}
  }})();

  // 3. Languages matching proxy geo — must patch BOTH language (singular) and languages (plural)
  // Pixelscan checks navigator.language === navigator.languages[0]
  // AND checks getter.toString() via Object.getOwnPropertyDescriptor — must be registered native
  (function() {{
    const _frozenLangs = Object.freeze({languages_json});
    const _getLang = function() {{ return '{primary_language}'; }};
    const _getLangs = function() {{ return _frozenLangs; }};
    if (window._stealthRegisterNative) {{
      window._stealthRegisterNative(_getLang, 'get language');
      window._stealthRegisterNative(_getLangs, 'get languages');
    }}
    Object.defineProperty(Navigator.prototype, 'language', {{
      get: _getLang, configurable: true, enumerable: true,
    }});
    Object.defineProperty(Navigator.prototype, 'languages', {{
      get: _getLangs, configurable: true, enumerable: true,
    }});
  }})();

  // 4. Platform matching UA OS — patch on prototype + userAgentData for 3-way consistency
  (function() {{
    const _getPlatform = function() {{ return '{platform}'; }};
    if (window._stealthRegisterNative) window._stealthRegisterNative(_getPlatform, 'get platform');
    Object.defineProperty(Navigator.prototype, 'platform', {{
      get: _getPlatform, configurable: true, enumerable: true,
    }});
  }})();
  // userAgentData — doesn't exist in headless, must be created from scratch
  // Pixelscan checks 3-way consistency: UA string, platform, userAgentData.platform
  (function() {{
    const _brands = [
      {{ brand: 'Not/A)Brand', version: '8' }},
      {{ brand: 'Chromium', version: '{chrome_version}' }},
      {{ brand: 'Google Chrome', version: '{chrome_version}' }},
    ];
    // Use plain object — inheriting from NavigatorUAData.prototype causes "Illegal invocation"
    // because native getters require internal slots our fake doesn't have
    const _fakeUAD = {{}};
    Object.defineProperties(_fakeUAD, {{
      brands: {{ value: _brands, enumerable: true, configurable: true }},
      mobile: {{ value: false, enumerable: true, configurable: true }},
      platform: {{ value: '{uad_platform}', enumerable: true, configurable: true }},
    }});
    _fakeUAD.getHighEntropyValues = function(hints) {{
      return Promise.resolve({{
        brands: _brands,
        mobile: false,
        platform: '{uad_platform}',
        platformVersion: '{uad_platform_version}',
        architecture: 'x86',
        bitness: '64',
        model: '',
        uaFullVersion: '{chrome_full_version}',
        fullVersionList: [
          {{ brand: 'Not/A)Brand', version: '8.0.0.0' }},
          {{ brand: 'Chromium', version: '{chrome_full_version}' }},
          {{ brand: 'Google Chrome', version: '{chrome_full_version}' }},
        ],
      }});
    }};
    _fakeUAD.toJSON = function() {{
      return {{ brands: _brands, mobile: false, platform: '{uad_platform}' }};
    }};
    try {{
      const _getUAD = function() {{ return _fakeUAD; }};
      if (window._stealthRegisterNative) window._stealthRegisterNative(_getUAD, 'get userAgentData');
      Object.defineProperty(Navigator.prototype, 'userAgentData', {{
        get: _getUAD, configurable: true, enumerable: true,
      }});
    }} catch(e) {{}}
  }})();

  // 5. Hardware fingerprint — on prototype, getters registered with toString shield
  (function() {{
    const _getHW = function() {{ return {hardware_concurrency}; }};
    const _getDM = function() {{ return {device_memory}; }};
    if (window._stealthRegisterNative) {{
      window._stealthRegisterNative(_getHW, 'get hardwareConcurrency');
      window._stealthRegisterNative(_getDM, 'get deviceMemory');
    }}
    Object.defineProperty(Navigator.prototype, 'hardwareConcurrency', {{
      get: _getHW, configurable: true, enumerable: true,
    }});
    Object.defineProperty(Navigator.prototype, 'deviceMemory', {{
      get: _getDM, configurable: true, enumerable: true,
    }});
  }})();

  // 6. window.chrome runtime — Cloudflare check #1
  // Only inject for Chrome/Edge UAs. Firefox should NOT have window.chrome.
  if (!window.chrome && /Chrome\\//.test(navigator.userAgent)) {{
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
    const _patchedQuery = function query(parameters) {{
      if (parameters.name === 'notifications') {{
        return Promise.resolve({{ state: 'default', onchange: null }});
      }}
      return _originalQuery.apply(this, [parameters]);
    }};
    window.Permissions.prototype.query = _patchedQuery;
    if (window._stealthRegisterNative) window._stealthRegisterNative(_patchedQuery, 'query');
  }}

  // 8. WebGL fingerprint spoofing
  (function() {{
    const _getParam = WebGLRenderingContext.prototype.getParameter;
    const _patchedGetParam = function getParameter(parameter) {{
      if (parameter === 37445) return '{webgl_vendor}';
      if (parameter === 37446) return '{webgl_renderer}';
      return _getParam.apply(this, [parameter]);
    }};
    WebGLRenderingContext.prototype.getParameter = _patchedGetParam;
    if (window._stealthRegisterNative) window._stealthRegisterNative(_patchedGetParam, 'getParameter');

    if (typeof WebGL2RenderingContext !== 'undefined') {{
      const _getParam2 = WebGL2RenderingContext.prototype.getParameter;
      const _patchedGetParam2 = function getParameter(parameter) {{
        if (parameter === 37445) return '{webgl_vendor}';
        if (parameter === 37446) return '{webgl_renderer}';
        return _getParam2.apply(this, [parameter]);
      }};
      WebGL2RenderingContext.prototype.getParameter = _patchedGetParam2;
      if (window._stealthRegisterNative) window._stealthRegisterNative(_patchedGetParam2, 'getParameter');
    }}
  }})();

  // 9. Canvas fingerprint noise (toDataURL + toBlob + fillText)
  (function() {{
    const _noise = {canvas_noise};
    const _origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const _patchedToDataURL = function toDataURL(type, quality) {{
      const ctx = this.getContext('2d');
      if (ctx && this.width > 0 && this.height > 0) {{
        try {{
          const imageData = ctx.getImageData(0, 0, this.width, this.height);
          const d = imageData.data;
          for (let i = 0; i < d.length; i += 4) {{
            d[i]   = Math.min(255, d[i]   + Math.floor(_noise * 255));
            d[i+1] = Math.min(255, d[i+1] + Math.floor(_noise * 255));
            d[i+2] = Math.min(255, d[i+2] + Math.floor(_noise * 255));
          }}
          ctx.putImageData(imageData, 0, 0);
        }} catch(e) {{}}
      }}
      return _origToDataURL.apply(this, [type, quality]);
    }};
    HTMLCanvasElement.prototype.toDataURL = _patchedToDataURL;
    if (window._stealthRegisterNative) window._stealthRegisterNative(_patchedToDataURL, 'toDataURL');

    // Also patch toBlob (CreepJS uses both)
    const _origToBlob = HTMLCanvasElement.prototype.toBlob;
    if (_origToBlob) {{
      const _patchedToBlob = function toBlob(callback, type, quality) {{
        const ctx = this.getContext('2d');
        if (ctx && this.width > 0 && this.height > 0) {{
          try {{
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const d = imageData.data;
            for (let i = 0; i < d.length; i += 4) {{
              d[i]   = Math.min(255, d[i]   + Math.floor(_noise * 255));
            }}
            ctx.putImageData(imageData, 0, 0);
          }} catch(e) {{}}
        }}
        return _origToBlob.apply(this, [callback, type, quality]);
      }};
      HTMLCanvasElement.prototype.toBlob = _patchedToBlob;
      if (window._stealthRegisterNative) window._stealthRegisterNative(_patchedToBlob, 'toBlob');
    }}
  }})();

  // 10. AudioContext fingerprint noise
  (function() {{
    const _origGetChannelData = AudioBuffer.prototype.getChannelData;
    const _patchedGetChannelData = function getChannelData() {{
      const array = _origGetChannelData.apply(this, arguments);
      for (let i = 0; i < array.length; i += 100) {{
        array[i] += (Math.random() - 0.5) * 0.0001;
      }}
      return array;
    }};
    AudioBuffer.prototype.getChannelData = _patchedGetChannelData;
    if (window._stealthRegisterNative) window._stealthRegisterNative(_patchedGetChannelData, 'getChannelData');
  }})();

  // 11. Screen / window consistency — headless has outerHeight === innerHeight (no browser chrome)
  (function() {{
    const _outerH = window.innerHeight + 80;
    const _outerW = window.innerWidth;
    const _screenX = {screen_x};
    const _screenY = {screen_y};
    const _gOH = function() {{ return _outerH; }};
    const _gOW = function() {{ return _outerW; }};
    const _gSX = function() {{ return _screenX; }};
    const _gSY = function() {{ return _screenY; }};
    const _gSL = function() {{ return _screenX; }};
    const _gST = function() {{ return _screenY; }};
    if (window._stealthRegisterNative) {{
      window._stealthRegisterNative(_gOH, 'get outerHeight');
      window._stealthRegisterNative(_gOW, 'get outerWidth');
      window._stealthRegisterNative(_gSX, 'get screenX');
      window._stealthRegisterNative(_gSY, 'get screenY');
      window._stealthRegisterNative(_gSL, 'get screenLeft');
      window._stealthRegisterNative(_gST, 'get screenTop');
    }}
    try {{
      Object.defineProperty(window, 'outerHeight', {{ get: _gOH }});
      Object.defineProperty(window, 'outerWidth', {{ get: _gOW }});
      Object.defineProperty(window, 'screenX', {{ get: _gSX }});
      Object.defineProperty(window, 'screenY', {{ get: _gSY }});
      Object.defineProperty(window, 'screenLeft', {{ get: _gSL }});
      Object.defineProperty(window, 'screenTop', {{ get: _gST }});
    }} catch(e) {{}}
  }})();

  // 12. navigator.connection — absent in headless, present in real Chrome
  (function() {{
    if (!navigator.connection) {{
      const _connData = {{
        effectiveType: '4g',
        rtt: {connection_rtt},
        downlink: {connection_downlink},
        saveData: false,
        onchange: null,
      }};
      const _getConn = function() {{ return _connData; }};
      if (window._stealthRegisterNative) window._stealthRegisterNative(_getConn, 'get connection');
      try {{
        Object.defineProperty(Navigator.prototype, 'connection', {{
          get: _getConn, configurable: true, enumerable: true,
        }});
      }} catch(e) {{}}
    }}
  }})();

  // 13. navigator.mediaDevices — headless returns empty device list
  (function() {{
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
      const _origEnumerate = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
      Object.defineProperty(navigator.mediaDevices, 'enumerateDevices', {{
        value: function() {{
          return _origEnumerate().then(function(devices) {{
            if (devices.length === 0) {{
              return [
                {{ kind: 'audioinput', deviceId: 'default', label: '', groupId: 'default' }},
                {{ kind: 'audiooutput', deviceId: 'default', label: '', groupId: 'default' }},
                {{ kind: 'videoinput', deviceId: 'default', label: '', groupId: 'default' }},
              ];
            }}
            return devices;
          }});
        }},
        configurable: true,
        writable: true,
      }});
    }}
  }})();

  // 14. Battery API — create BatteryManager if missing (headless has neither)
  (function() {{
    // In headless, BatteryManager class doesn't exist at all — create it
    if (typeof BatteryManager === 'undefined') {{
      window.BatteryManager = function BatteryManager() {{}};
      BatteryManager.prototype = Object.create(EventTarget.prototype);
      BatteryManager.prototype.constructor = BatteryManager;
      Object.defineProperty(BatteryManager, 'name', {{ value: 'BatteryManager' }});
    }}
    const _mockBattery = Object.create(BatteryManager.prototype);
    Object.defineProperties(_mockBattery, {{
      charging: {{ get: () => true, enumerable: true, configurable: true }},
      chargingTime: {{ get: () => 0, enumerable: true, configurable: true }},
      dischargingTime: {{ get: () => Infinity, enumerable: true, configurable: true }},
      level: {{ get: () => 0.{battery_level}, enumerable: true, configurable: true }},
      onchargingchange: {{ get: () => null, set: () => {{}}, enumerable: true, configurable: true }},
      onchargingtimechange: {{ get: () => null, set: () => {{}}, enumerable: true, configurable: true }},
      ondischargingtimechange: {{ get: () => null, set: () => {{}}, enumerable: true, configurable: true }},
      onlevelchange: {{ get: () => null, set: () => {{}}, enumerable: true, configurable: true }},
    }});
    _mockBattery.addEventListener = EventTarget.prototype.addEventListener.bind(_mockBattery);
    _mockBattery.removeEventListener = EventTarget.prototype.removeEventListener.bind(_mockBattery);
    _mockBattery.dispatchEvent = EventTarget.prototype.dispatchEvent.bind(_mockBattery);
    const _getBattery = function getBattery() {{ return Promise.resolve(_mockBattery); }};
    if (window._stealthRegisterNative) window._stealthRegisterNative(_getBattery, 'getBattery');
    Object.defineProperty(Navigator.prototype, 'getBattery', {{
      value: _getBattery, configurable: true, writable: true,
    }});
  }})();

  // 15. Video codec support — headless Chromium lacks H.264 (proprietary codec)
  // bot.sannysoft.com checks MediaSource.isTypeSupported and HTMLVideoElement.canPlayType
  // Real Chrome returns "probably" for H.264, headless returns "" — a known bot tell
  (function() {{
    const _h264Types = [
      'video/mp4; codecs="avc1.42E01E"',
      'video/mp4; codecs="avc1.4D401F"',
      'video/mp4; codecs="avc1.64001E"',
      'video/mp4; codecs="avc1.640028"',
      'video/mp4; codecs="avc1.42001E, mp4a.40.2"',
      'video/mp4; codecs="mp4a.40.2"',
      'audio/mp4; codecs="mp4a.40.2"',
    ];
    if (typeof MediaSource !== 'undefined' && MediaSource.isTypeSupported) {{
      const _origIsType = MediaSource.isTypeSupported.bind(MediaSource);
      const _patchedIsType = function isTypeSupported(type) {{
        if (_h264Types.some(t => type.includes('avc1') || type.includes('mp4a'))) return true;
        return _origIsType(type);
      }};
      MediaSource.isTypeSupported = _patchedIsType;
      if (window._stealthRegisterNative) window._stealthRegisterNative(_patchedIsType, 'isTypeSupported');
    }}
    if (typeof HTMLVideoElement !== 'undefined') {{
      const _origCanPlay = HTMLVideoElement.prototype.canPlayType;
      const _patchedCanPlay = function canPlayType(type) {{
        if (type.includes('avc1') || type.includes('mp4a') || type.includes('mp4')) {{
          return 'probably';
        }}
        return _origCanPlay.apply(this, [type]);
      }};
      HTMLVideoElement.prototype.canPlayType = _patchedCanPlay;
      if (window._stealthRegisterNative) window._stealthRegisterNative(_patchedCanPlay, 'canPlayType');
    }}
    if (typeof HTMLAudioElement !== 'undefined') {{
      const _origCanPlayAudio = HTMLAudioElement.prototype.canPlayType;
      const _patchedCanPlayAudio = function canPlayType(type) {{
        if (type.includes('mp4a') || type.includes('aac') || type.includes('mp3') || type.includes('mpeg')) {{
          return 'probably';
        }}
        return _origCanPlayAudio.apply(this, [type]);
      }};
      HTMLAudioElement.prototype.canPlayType = _patchedCanPlayAudio;
      if (window._stealthRegisterNative) window._stealthRegisterNative(_patchedCanPlayAudio, 'canPlayType');
    }}
  }})();

  // 16. Error.stackTraceLimit — V8 headless default is 10, Chrome default is also 10
  try {{ Error.stackTraceLimit = 10; }} catch(e) {{}}

  // 17. Cleanup — remove our utility from window so it doesn't leak as an unusual property
  try {{ delete window._stealthRegisterNative; }} catch(e) {{}}
}})();"""

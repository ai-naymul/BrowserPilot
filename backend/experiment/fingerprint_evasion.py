import random
import base64
import json
import time
from typing import Dict, List

class AdvancedFingerprintEvasion:
    def __init__(self):
        self.fingerprint_profiles = self._load_fingerprint_profiles()
        self.current_profile = None
        
    def _load_fingerprint_profiles(self) -> List[Dict]:
        """Load realistic fingerprint profiles to defeat fingerprintjs"""
        return [
            {
                "name": "Windows_Chrome_120",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080},
                "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
                "timezone": "America/New_York",
                "language": "en-US",
                "platform": "Win32",
                "hardware_concurrency": 8,
                "device_memory": 8,
                "webgl_vendor": "Google Inc. (Intel)",
                "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "canvas_noise": 0.1,
                "audio_noise": 0.05,
                "fonts": ["Arial", "Times New Roman", "Helvetica", "Georgia", "Verdana"]
            },
            {
                "name": "Linux_Chrome_119", 
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "viewport": {"width": 1366, "height": 768},
                "screen": {"width": 1366, "height": 768, "colorDepth": 24},
                "timezone": "Europe/London",
                "language": "en-GB", 
                "platform": "Linux x86_64",
                "hardware_concurrency": 4,
                "device_memory": 4,
                "webgl_vendor": "Mesa",
                "webgl_renderer": "Mesa DRI Intel(R) HD Graphics",
                "canvas_noise": 0.15,
                "audio_noise": 0.08,
                "fonts": ["DejaVu Sans", "Liberation Sans", "Ubuntu", "Arial", "Helvetica"]
            },
            {
                "name": "MacOS_Safari_17",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "viewport": {"width": 1440, "height": 900},
                "screen": {"width": 1440, "height": 900, "colorDepth": 24},
                "timezone": "America/Los_Angeles",
                "language": "en-US",
                "platform": "MacIntel", 
                "hardware_concurrency": 8,
                "device_memory": 16,
                "webgl_vendor": "Apple Inc.",
                "webgl_renderer": "Apple GPU",
                "canvas_noise": 0.05,
                "audio_noise": 0.03,
                "fonts": ["SF Pro Display", "Helvetica Neue", "Arial", "Times", "Georgia"]
            }
        ]
    
    def get_random_profile(self) -> Dict:
        """Get a random but consistent fingerprint profile"""
        self.current_profile = random.choice(self.fingerprint_profiles)
        return self.current_profile.copy()
    
    def generate_anti_fingerprintjs_script(self, profile: Dict) -> str:
        """Generate comprehensive script to defeat fingerprintjs and SimilarWeb detection"""
        return f"""
        // Advanced Fingerprint Evasion - Defeats fingerprintjs specifically
        (function() {{
            'use strict';
            
            console.log('🥷 Loading advanced fingerprint evasion for profile:', '{profile["name"]}');
            
            // Seeded random for consistent fingerprinting within session
            let seed = {random.randint(1, 1000000)};
            const originalRandom = Math.random;
            Math.random = function() {{
                seed = (seed * 9301 + 49297) % 233280;
                return seed / 233280;
            }};
            
            // Override Navigator Properties (defeats basic fingerprinting)
            Object.defineProperties(navigator, {{
                userAgent: {{
                    get: () => '{profile["user_agent"]}',
                    configurable: true
                }},
                language: {{
                    get: () => '{profile["language"]}',
                    configurable: true
                }},
                languages: {{
                    get: () => ['{profile["language"]}', 'en'],
                    configurable: true
                }},
                platform: {{
                    get: () => '{profile["platform"]}',
                    configurable: true
                }},
                hardwareConcurrency: {{
                    get: () => {profile["hardware_concurrency"]},
                    configurable: true
                }},
                deviceMemory: {{
                    get: () => {profile["device_memory"]},
                    configurable: true
                }},
                webdriver: {{
                    get: () => undefined,
                    configurable: true
                }},
                plugins: {{
                    get: () => {{
                        return {{
                            length: 3,
                            0: {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' }},
                            1: {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' }},
                            2: {{ name: 'Native Client', filename: 'internal-nacl-plugin' }}
                        }};
                    }},
                    configurable: true
                }}
            }});
            
            // Override Screen Properties (consistent with viewport)
            Object.defineProperties(screen, {{
                width: {{
                    get: () => {profile["screen"]["width"]},
                    configurable: true
                }},
                height: {{
                    get: () => {profile["screen"]["height"]},
                    configurable: true
                }},
                availWidth: {{
                    get: () => {profile["screen"]["width"]},
                    configurable: true
                }},
                availHeight: {{
                    get: () => {profile["screen"]["height"] - 40},
                    configurable: true
                }},
                colorDepth: {{
                    get: () => {profile["screen"]["colorDepth"]},
                    configurable: true
                }},
                pixelDepth: {{
                    get: () => {profile["screen"]["colorDepth"]},
                    configurable: true
                }}
            }});
            
            // Canvas Fingerprint Protection with Noise (defeats canvas fingerprinting)
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            
            HTMLCanvasElement.prototype.getContext = function(type, options) {{
                const context = originalGetContext.call(this, type, options);
                
                if (type === '2d') {{
                    const originalFillText = context.fillText;
                    const originalStrokeText = context.strokeText;
                    const noise = {profile["canvas_noise"]};
                    
                    context.fillText = function(text, x, y, maxWidth) {{
                        const noisyX = x + (Math.random() - 0.5) * noise;
                        const noisyY = y + (Math.random() - 0.5) * noise;
                        return originalFillText.call(this, text, noisyX, noisyY, maxWidth);
                    }};
                    
                    context.strokeText = function(text, x, y, maxWidth) {{
                        const noisyX = x + (Math.random() - 0.5) * noise;
                        const noisyY = y + (Math.random() - 0.5) * noise;
                        return originalStrokeText.call(this, text, noisyX, noisyY, maxWidth);
                    }};
                }}
                
                return context;
            }};
            
            // Override Canvas toDataURL with noise injection
            HTMLCanvasElement.prototype.toDataURL = function() {{
                const context = this.getContext('2d');
                if (context) {{
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    const data = imageData.data;
                    
                    // Add subtle noise to prevent fingerprinting
                    for (let i = 0; i < data.length; i += 4) {{
                        if (Math.random() < 0.01) {{ // 1% of pixels get noise
                            data[i] = Math.min(255, Math.max(0, data[i] + (Math.random() - 0.5) * 2));
                            data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + (Math.random() - 0.5) * 2));
                            data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + (Math.random() - 0.5) * 2));
                        }}
                    }}
                    
                    context.putImageData(imageData, 0, 0);
                }}
                return originalToDataURL.call(this);
            }};
            
            // WebGL Fingerprint Protection (defeats WebGL fingerprinting)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                switch (parameter) {{
                    case this.VENDOR:
                        return '{profile["webgl_vendor"]}';
                    case this.RENDERER:
                        return '{profile["webgl_renderer"]}';
                    case this.VERSION:
                        return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
                    case this.SHADING_LANGUAGE_VERSION:
                        return 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)';
                    default:
                        return getParameter.call(this, parameter);
                }}
            }};
            
            // WebGL2 Context Protection
            if (window.WebGL2RenderingContext) {{
                const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                    switch (parameter) {{
                        case this.VENDOR:
                            return '{profile["webgl_vendor"]}';
                        case this.RENDERER:
                            return '{profile["webgl_renderer"]}';
                        default:
                            return getParameter2.call(this, parameter);
                    }}
                }};
            }}
            
            // Audio Context Fingerprint Protection (defeats audio fingerprinting)
            if (window.AudioContext || window.webkitAudioContext) {{
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                const originalCreateAnalyser = AudioContextClass.prototype.createAnalyser;
                
                AudioContextClass.prototype.createAnalyser = function() {{
                    const analyser = originalCreateAnalyser.call(this);
                    const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                    
                    analyser.getFloatFrequencyData = function(array) {{
                        originalGetFloatFrequencyData.call(this, array);
                        // Add subtle noise to audio fingerprint
                        for (let i = 0; i < array.length; i++) {{
                            array[i] += (Math.random() - 0.5) * {profile["audio_noise"]};
                        }}
                    }};
                    
                    return analyser;
                }};
            }}
            
            // Font Detection Protection
            Object.defineProperty(document, 'fonts', {{
                get: () => {{
                    const fonts = {json.dumps(profile["fonts"])};
                    return {{
                        check: (font) => fonts.some(f => font.includes(f)),
                        values: () => fonts.map(f => ({{family: f}})),
                        size: fonts.length
                    }};
                }},
                configurable: true
            }});
            
            // Timezone Spoofing (consistent timezone)
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {{
                const timezones = {{
                    'America/New_York': 300,
                    'Europe/London': 0,
                    'America/Los_Angeles': 480,
                    'Europe/Berlin': -60
                }};
                return timezones['{profile["timezone"]}'] || 0;
            }};
            
            // Override Intl.DateTimeFormat for timezone consistency
            const originalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(...args) {{
                if (args.length === 0 || !args[0]) {{
                    args[0] = '{profile["language"]}';
                }}
                if (args.length === 1) {{
                    args[1] = {{ timeZone: '{profile["timezone"]}' }};
                }} else if (args[1] && !args[1].timeZone) {{
                    args[1].timeZone = '{profile["timezone"]}';
                }}
                return new originalDateTimeFormat(...args);
            }};
            
            // Remove all automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
            
            // Chrome runtime spoofing
            if (window.chrome && window.chrome.runtime) {{
                delete window.chrome.runtime.onConnect;
                delete window.chrome.runtime.onMessage;
            }}
            
            // Permissions API Override
            if (navigator.permissions && navigator.permissions.query) {{
                navigator.permissions.query = function(permissionDesc) {{
                    return Promise.resolve({{
                        state: 'granted',
                        name: permissionDesc.name
                    }});
                }};
            }}
            
            // Battery API Spoofing
            if (navigator.getBattery) {{
                navigator.getBattery = function() {{
                    return Promise.resolve({{
                        charging: true,
                        chargingTime: Infinity,
                        dischargingTime: Infinity,
                        level: 1.0
                    }});
                }};
            }}
            
            // GamePad API Spoofing
            if (navigator.getGamepads) {{
                navigator.getGamepads = function() {{
                    return [];
                }};
            }}
            
            console.log('✅ Advanced fingerprint evasion loaded successfully');
        }})();
        """

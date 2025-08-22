import random
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import time
import hashlib

logger = logging.getLogger(__name__)

class AdvancedFingerprintEvasion:
    def __init__(self, browser_data_path: str = "browsers.json"):
        self.browser_data = self._load_browser_data(browser_data_path)
        
        # ✅ ADD: Load realistic profiles
        self.realistic_profiles = self._load_realistic_profiles()
        self.current_session = None
        
        # Keep existing used_fingerprints tracking
        self.used_fingerprints = set()
        self.fingerprint_rotation_count = 0
        self.last_rotation_time = time.time()


    def _load_realistic_profiles(self) -> Dict:
        """Load the generated realistic profiles"""
        try:
            with open("realistic_profiles.json", 'r') as f:
                profiles = json.load(f)
                logger.info(f"✅ Loaded {len(profiles)} realistic profiles")
                
                # Group by type for easy selection
                grouped = {
                    'business_windows': [],
                    'mac_users': [], 
                    'home_windows': [],
                    'linux_users': []
                }
                
                for profile in profiles:
                    profile_type = profile.get('profile_type', 'business_windows')
                    if profile_type in grouped:
                        grouped[profile_type].append(profile)
                
                return grouped
                
        except FileNotFoundError:
            logger.warning("⚠️ realistic_profiles.json not found, using fallback profiles")
            return self._get_fallback_profiles()
    def start_new_session(self, session_duration_hours: float = None):
        """Start a new user session with consistent profile"""
        if session_duration_hours is None:
            session_duration_hours = random.uniform(0.5, 4.0)
            
        # Choose profile pool based on realistic distribution  
        if random.random() < 0.75:  # 75% Windows users
            profile_pool = 'business_windows'
        elif random.random() < 0.9:  # 15% Mac users  
            profile_pool = 'mac_users'
        elif random.random() < 0.95:  # 5% home Windows
            profile_pool = 'home_windows'
        else:  # 5% Linux users
            profile_pool = 'linux_users'
        
        available_profiles = self.realistic_profiles.get(profile_pool, self.realistic_profiles['business_windows'])
        base_profile = random.choice(available_profiles)
        
        self.current_session = {
            'id': hashlib.md5(f"{time.time()}_{random.random()}".encode()).hexdigest()[:12],
            'start_time': time.time(),
            'duration_target': session_duration_hours * 3600,
            'base_profile': base_profile,
            'requests_made': 0,
            'success_count': 0,
            'failure_count': 0,
            'personal_browsing_speed': random.uniform(0.7, 1.8)
        }
        
        logger.info(f"👤 Started session {self.current_session['id']} ({profile_pool})")
        return self.current_session

    def get_session_profile(self) -> Dict:
        """Get consistent profile for current session"""
        if not self.current_session:
            self.start_new_session()
        
        base = self.current_session['base_profile']
        session_id = self.current_session['id']
        
        # Build consistent profile with minimal variation
        profile = {
            'name': f"Session_{session_id}_{base['viewport'][0]}x{base['viewport'][1]}",
            'user_agent': base['user_agent'],
            'viewport': {
                'width': base['viewport'][0], 
                'height': base['viewport'][1] - random.randint(80, 120)  # Browser chrome
            },
            'screen': {
                'width': base['viewport'][0],
                'height': base['viewport'][1],
                'colorDepth': 24
            },
            'timezone': base['timezone'],
            'language': 'en-US',
            'languages': ['en-US', 'en'],
            'platform': 'Win32' if 'Windows' in base['user_agent'] else 'MacIntel' if 'Macintosh' in base['user_agent'] else 'Linux x86_64',
            'hardware_concurrency': base['hardware']['cores'],
            'device_memory': base['hardware']['memory'], 
            'max_touch_points': 0,  # Desktop only
            'session_id': session_id,
            'fingerprint_hash': f"session_{session_id}"
        }
        
        self.current_session['requests_made'] += 1
        return profile

    def should_end_session(self) -> bool:
        """Check if current session should end"""
        if not self.current_session:
            return True
            
        session_duration = time.time() - self.current_session['start_time']
        
        # End session based on realistic user behavior
        if session_duration > self.current_session['duration_target']:
            return True
        if self.current_session['requests_made'] > 15:  # User gets tired
            return True
        if self.current_session['failure_count'] >= 3:  # User gives up
            return True
        if random.random() < 0.1:  # Sometimes users just leave
            return True
            
        return False

    def record_session_result(self, success: bool):
        """Record result for current session"""
        if self.current_session:
            if success:
                self.current_session['success_count'] += 1
            else:
                self.current_session['failure_count'] += 1
    def _get_fallback_profiles(self) -> Dict:
        """Fallback profiles if generated ones not available"""
        return {
            'business_windows': [
                {
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'viewport': (1920, 1080),
                    'timezone': 'America/New_York',
                    'hardware': {'cores': 8, 'memory': 16},
                    'profile_type': 'business_windows'
                },
                {
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'viewport': (1366, 768),
                    'timezone': 'America/Chicago',
                    'hardware': {'cores': 4, 'memory': 8},
                    'profile_type': 'business_windows'
                }
                # Add more fallback profiles...
            ],
            'mac_users': [
                {
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'viewport': (1440, 900),
                    'timezone': 'America/Los_Angeles',
                    'hardware': {'cores': 8, 'memory': 16},
                    'profile_type': 'mac_users'
                }
            ]
        }
    def _load_browser_data(self, path: str) -> Dict:
        """Load browser data from JSON file"""
        try:
            with open("backend/experiment/browsers.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"✅ Loaded browser data with {self._count_user_agents(data)} user agents")
                return data
        except FileNotFoundError:
            logger.warning(f"⚠️ browser.json not found, using fallback data")
            # return self._get_fallback_browser_data()
    
    def _count_user_agents(self, data: Dict) -> int:
        """Count total number of user agents in the data"""
        count = 0
        if 'user_agents' in data:
            for platform_type in data['user_agents'].values():
                for os_data in platform_type.values():
                    for browser_list in os_data.values():
                        if isinstance(browser_list, list):
                            count += len(browser_list)
        return count
    
    # def _get_fallback_browser_data(self) -> Dict:
    #     """Fallback browser data if JSON not available"""
    #     return {
    #         "headers": {
    #             "chrome": {
    #                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    #                 "Accept-Language": "en-US,en;q=0.9",
    #                 "Accept-Encoding": "gzip, deflate, br",
    #                 "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    #                 "Sec-Ch-Ua-Mobile": "?0",
    #                 "Sec-Ch-Ua-Platform": '"Windows"',
    #                 "Sec-Fetch-Dest": "document",
    #                 "Sec-Fetch-Mode": "navigate",
    #                 "Sec-Fetch-Site": "none",
    #                 "Sec-Fetch-User": "?1",
    #                 "Upgrade-Insecure-Requests": "1"
    #             },
    #             "firefox": {
    #                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    #                 "Accept-Language": "en-US,en;q=0.5",
    #                 "Accept-Encoding": "gzip, deflate, br",
    #                 "Upgrade-Insecure-Requests": "1",
    #                 "Sec-Fetch-Dest": "document",
    #                 "Sec-Fetch-Mode": "navigate",
    #                 "Sec-Fetch-Site": "none",
    #                 "Sec-Fetch-User": "?1"
    #             }
    #         },
    #         "cipherSuite": {
    #             "chrome": [
    #                 "TLS_AES_128_GCM_SHA256",
    #                 "TLS_AES_256_GCM_SHA384",
    #                 "TLS_CHACHA20_POLY1305_SHA256",
    #                 "ECDHE-ECDSA-AES128-GCM-SHA256",
    #                 "ECDHE-RSA-AES128-GCM-SHA256"
    #             ],
    #             "firefox": [
    #                 "TLS_AES_128_GCM_SHA256",
    #                 "TLS_CHACHA20_POLY1305_SHA256",
    #                 "TLS_AES_256_GCM_SHA384",
    #                 "ECDHE-ECDSA-AES128-GCM-SHA256",
    #                 "ECDHE-RSA-AES128-GCM-SHA256"
    #             ]
    #         },
    #         "user_agents": {
    #             "desktop": {
    #                 "windows": {
    #                     "chrome": [
    #                         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    #                         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    #                     ],
    #                     "firefox": [
    #                         "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    #                     ]
    #                 }
    #             }
    #         }
    #     }
    
    def get_random_profile(self) -> Dict:
        """Get profile - now uses session-based approach"""
        # Use session profile if we have an active session
        if self.current_session and not self.should_end_session():
            return self.get_session_profile()
        
        # Start new session if needed
        if self.should_end_session():
            if self.current_session:
                logger.info(f"👋 Ending session {self.current_session['id']} after {self.current_session['requests_made']} requests")
            self.start_new_session()
        
        return self.get_session_profile()


    
    def _choose_browser_type(self, platform_type: str, os_type: str) -> str:
        """Choose browser type based on platform with realistic distribution"""
        if platform_type == 'desktop':
            # Chrome dominates desktop
            return random.choices(['chrome', 'firefox', 'edge', 'safari', 'opera'], 
                                 weights=[65, 10, 15, 8, 2])[0]
        else:
            if os_type == 'ios':
                return random.choices(['safari', 'chrome', 'firefox'], 
                                     weights=[60, 35, 5])[0]
            else:  # android
                return random.choices(['chrome', 'samsung', 'firefox', 'opera'], 
                                     weights=[70, 15, 10, 5])[0]
    
    def _get_random_user_agent(self, platform_type: str, os_type: str, browser_type: str) -> str:
        """Get random user agent from loaded data or generate one"""
        try:
            agents = self.browser_data['user_agents'][platform_type][os_type].get(browser_type, [])
            if agents and isinstance(agents, list) and len(agents) > 0:
                base_ua = random.choice(agents)
                # Add minor variations to make it unique
                return self._add_ua_variations(base_ua, browser_type)
            else:
                return self._generate_synthetic_user_agent(platform_type, os_type, browser_type)
        except (KeyError, TypeError):
            return self._generate_synthetic_user_agent(platform_type, os_type, browser_type)
    
    def _add_ua_variations(self, base_ua: str, browser_type: str) -> str:
        """Add minor variations to user agent to make it unique"""
        import re
        
        # Randomly update version numbers
        if browser_type == 'chrome' and 'Chrome/' in base_ua:
            # Update Chrome version
            major = random.randint(110, 122)
            minor = random.randint(0, 9)
            patch = random.randint(0, 9999)
            build = random.randint(0, 999)
            base_ua = re.sub(r'Chrome/[\d.]+', f'Chrome/{major}.{minor}.{patch}.{build}', base_ua)
            
        elif browser_type == 'firefox' and 'Firefox/' in base_ua:
            # Update Firefox version
            major = random.randint(115, 122)
            base_ua = re.sub(r'Firefox/[\d.]+', f'Firefox/{major}.0', base_ua)
            base_ua = re.sub(r'rv:[\d.]+', f'rv:{major}.0', base_ua)
        
        # Occasionally add or remove AppleWebKit version variations
        if random.random() < 0.1 and 'AppleWebKit' in base_ua:
            webkit_version = f"{random.randint(537, 538)}.{random.randint(1, 50)}"
            base_ua = re.sub(r'AppleWebKit/[\d.]+', f'AppleWebKit/{webkit_version}', base_ua)
        
        return base_ua
    
    def _generate_synthetic_user_agent(self, platform_type: str, os_type: str, browser_type: str) -> str:
        """Generate synthetic user agent when no data available"""
        os_strings = {
            'windows': f"Windows NT {random.choice(['10.0', '11.0'])}; Win64; x64",
            'linux': "X11; Linux x86_64",
            'darwin': f"Macintosh; Intel Mac OS X 10_{random.randint(13, 15)}_{random.randint(0, 9)}",
            'android': f"Linux; Android {random.randint(10, 14)}",
            'ios': f"iPhone; CPU iPhone OS {random.randint(14, 17)}_{random.randint(0, 5)} like Mac OS X"
        }
        
        browser_strings = {
            'chrome': f"Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36",
            'firefox': f"Gecko/20100101 Firefox/{random.randint(115, 122)}.0",
            'edge': f"Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36 Edg/{random.randint(110, 122)}.0.0.0",
            'safari': f"Version/{random.randint(15, 17)}.{random.randint(0, 6)} Safari/605.1.15"
        }
        
        os_str = os_strings.get(os_type, os_strings['windows'])
        browser_str = browser_strings.get(browser_type, browser_strings['chrome'])
        
        return f"Mozilla/5.0 ({os_str}) AppleWebKit/537.36 (KHTML, like Gecko) {browser_str}"
    
    def _generate_dynamic_viewport(self, platform_type: str, os_type: str) -> Dict[str, int]:
        """Generate realistic viewport dimensions with bulletproof safety"""
        try:
            if platform_type == 'desktop':
                # Common desktop resolutions
                viewports = [
                    (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
                    (1280, 720), (1600, 900), (2560, 1440), (1680, 1050),
                    (1920, 1200), (2560, 1600), (3840, 2160), (1280, 800),
                    (1024, 768), (1280, 1024), (1360, 768)
                ]
                
                width, height = random.choice(viewports)
                
                # Safely subtract browser chrome
                chrome_height = random.randint(60, 150)
                height = max(600, height - chrome_height)
                
            else:  # mobile
                if os_type == 'ios':
                    viewports = [
                        (390, 844), (414, 896), (375, 812), (414, 736),
                        (375, 667), (320, 568), (428, 926), (390, 852)
                    ]
                else:  # android
                    viewports = [
                        (360, 800), (412, 915), (360, 780), (393, 851),
                        (412, 869), (360, 640), (412, 892), (384, 854)
                    ]
                
                width, height = random.choice(viewports)
            
            # SAFE variations - use absolutely safe ranges
            width_min = max(1, width - 5)
            width_max = width + 5
            height_min = max(1, height - 10) 
            height_max = height + 10
            
            # Ensure min <= max for random.randint
            if width_min >= width_max:
                width_variation = 0
            else:
                width_variation = random.randint(width_min - width, width_max - width)
                
            if height_min >= height_max:
                height_variation = 0
            else:
                height_variation = random.randint(height_min - height, height_max - height)
            
            # Apply variations with absolute bounds
            width = max(320, min(4000, width + width_variation))
            height = max(480, min(3000, height + height_variation))
            
            return {"width": int(width), "height": int(height)}
            
        except Exception as e:
            logger.error(f"Error generating viewport: {e}")
            # Fallback to safe defaults
            return {"width": 1920, "height": 1080}


    
    # def _generate_dynamic_screen(self, viewport: Dict[str, int], platform_type: str) -> Dict:
    #     """Generate screen dimensions based on viewport"""
    #     if platform_type == 'desktop':
    #         # Screen is typically same width but taller than viewport
    #         screen_width = viewport['width']
    #         screen_height = viewport['height'] + random.randint(60, 150)
    #     else:
    #         # Mobile screen matches viewport more closely
    #         screen_width = viewport['width']
    #         screen_height = viewport['height'] + random.randint(20, 60)
        
    #     # Color depth varies but 24 is most common
    #     color_depth = random.choices([24, 32, 16], weights=[80, 15, 5])[0]
        
    #     # Pixel ratio for retina displays
    #     pixel_ratio = random.choices([1, 1.5, 2, 3], weights=[40, 10, 40, 10])[0]
        
    #     return {
    #         "width": screen_width,
    #         "height": screen_height,
    #         "colorDepth": color_depth,
    #         "pixelDepth": color_depth,
    #         "availWidth": screen_width,
    #         "availHeight": screen_height - random.randint(20, 80),
    #         "devicePixelRatio": pixel_ratio,
    #         "orientation": {
    #             "angle": 0 if platform_type == 'desktop' else random.choice([0, 90]),
    #             "type": "landscape-primary" if platform_type == 'desktop' else random.choice(["portrait-primary", "landscape-primary"])
    #         }
    #     }
    
    def _generate_dynamic_screen(self, viewport: Dict[str, int], platform_type: str) -> Dict:
        """Generate screen dimensions based on viewport with safety checks"""
        # Ensure viewport has valid dimensions
        viewport_width = max(320, viewport.get('width', 1920))
        viewport_height = max(480, viewport.get('height', 1080))
        
        if platform_type == 'desktop':
            screen_width = viewport_width
            screen_height = viewport_height + random.randint(60, 150)
        else:
            screen_width = viewport_width
            screen_height = viewport_height + random.randint(20, 60)
        
        # Safety bounds
        screen_width = max(320, min(4000, screen_width))
        screen_height = max(480, min(3000, screen_height))
        
        color_depth = random.choices([24, 32, 16], weights=[80, 15, 5])[0]
        pixel_ratio = random.choices([1, 1.5, 2, 3], weights=[40, 10, 40, 10])[0]
        
        return {
            "width": screen_width,
            "height": screen_height,
            "colorDepth": color_depth,
            "pixelDepth": color_depth,
            "availWidth": screen_width,
            "availHeight": max(400, screen_height - random.randint(20, 80)),
            "devicePixelRatio": pixel_ratio,
            "orientation": {
                "angle": 0 if platform_type == 'desktop' else random.choice([0, 90]),
                "type": "landscape-primary" if platform_type == 'desktop' else random.choice(["portrait-primary", "landscape-primary"])
            }
        }

    def _generate_dynamic_hardware(self, platform_type: str) -> Dict:
        """Generate realistic hardware specifications"""
        if platform_type == 'desktop':
            cores = random.choices([2, 4, 6, 8, 12, 16, 24, 32], 
                                  weights=[5, 30, 20, 25, 10, 5, 3, 2])[0]
            memory = random.choices([2, 4, 8, 16, 32, 64], 
                                   weights=[5, 15, 40, 30, 8, 2])[0]
            touch_points = 0
        else:
            cores = random.choices([4, 6, 8], weights=[30, 50, 20])[0]
            memory = random.choices([2, 3, 4, 6, 8, 12], 
                                   weights=[10, 15, 30, 25, 15, 5])[0]
            touch_points = random.choice([1, 5, 10])
        
        return {
            "cores": cores,
            "memory": memory,
            "touch_points": touch_points
        }
    
    def _generate_dynamic_locale(self) -> Dict:
        """Generate correlated timezone and language settings"""
        locales = [
            {"timezone": "America/New_York", "language": "en-US", "languages": ["en-US", "en"]},
            {"timezone": "America/Los_Angeles", "language": "en-US", "languages": ["en-US", "en"]},
            {"timezone": "America/Chicago", "language": "en-US", "languages": ["en-US", "en"]},
            {"timezone": "Europe/London", "language": "en-GB", "languages": ["en-GB", "en"]},
            {"timezone": "Europe/Paris", "language": "fr-FR", "languages": ["fr-FR", "fr", "en"]},
            {"timezone": "Europe/Berlin", "language": "de-DE", "languages": ["de-DE", "de", "en"]},
            {"timezone": "Asia/Tokyo", "language": "ja-JP", "languages": ["ja-JP", "ja", "en"]},
            {"timezone": "Asia/Shanghai", "language": "zh-CN", "languages": ["zh-CN", "zh", "en"]},
            {"timezone": "Australia/Sydney", "language": "en-AU", "languages": ["en-AU", "en"]},
            {"timezone": "America/Toronto", "language": "en-CA", "languages": ["en-CA", "en", "fr"]},
            {"timezone": "Asia/Mumbai", "language": "en-IN", "languages": ["en-IN", "hi", "en"]},
            {"timezone": "America/Sao_Paulo", "language": "pt-BR", "languages": ["pt-BR", "pt", "en"]},
            {"timezone": "Europe/Moscow", "language": "ru-RU", "languages": ["ru-RU", "ru", "en"]},
            {"timezone": "Asia/Seoul", "language": "ko-KR", "languages": ["ko-KR", "ko", "en"]},
            {"timezone": "Europe/Amsterdam", "language": "nl-NL", "languages": ["nl-NL", "nl", "en"]}
        ]
        
        locale = random.choice(locales)
        
        # Sometimes shuffle the order of languages
        if random.random() < 0.3:
            random.shuffle(locale['languages'])
        
        return locale
    
    def _generate_dynamic_webgl(self, platform_type: str, os_type: str, browser_type: str) -> Dict:
        """Generate realistic WebGL parameters"""
        if platform_type == 'desktop':
            if os_type == 'windows':
                vendors = [
                    "Google Inc. (NVIDIA)",
                    "Google Inc. (AMD)",
                    "Google Inc. (Intel)",
                    "Google Inc."
                ]
                renderers = [
                    f"ANGLE (NVIDIA, NVIDIA GeForce {random.choice(['GTX 1060', 'GTX 1070', 'GTX 1080', 'RTX 2060', 'RTX 2070', 'RTX 3060', 'RTX 3070', 'RTX 3080', 'RTX 4060', 'RTX 4070', 'RTX 4080'])} Direct3D11 vs_5_0 ps_5_0, D3D11)",
                    f"ANGLE (AMD, AMD Radeon {random.choice(['RX 570', 'RX 580', 'RX 5700', 'RX 6600', 'RX 6700', 'RX 7600', 'RX 7700'])} Direct3D11 vs_5_0 ps_5_0, D3D11)",
                    f"ANGLE (Intel, Intel(R) {random.choice(['UHD Graphics 630', 'UHD Graphics 730', 'Iris Xe Graphics'])} Direct3D11 vs_5_0 ps_5_0, D3D11)"
                ]
            elif os_type == 'darwin':
                vendors = ["Apple Inc."]
                renderers = [
                    "Apple GPU",
                    "Apple M1 GPU",
                    "Apple M2 GPU",
                    "AMD Radeon Pro 5500M OpenGL Engine",
                    "Intel(R) Iris(TM) Plus Graphics OpenGL Engine"
                ]
            else:  # linux
                vendors = ["Mesa", "NVIDIA Corporation", "AMD"]
                renderers = [
                    "Mesa Intel(R) UHD Graphics 630",
                    "Mesa AMD Radeon RX 6700 XT",
                    "NVIDIA GeForce GTX 1660/PCIe/SSE2"
                ]
        else:  # mobile
            if os_type == 'android':
                vendors = ["Qualcomm", "ARM", "Google Inc. (Qualcomm)"]
                renderers = [
                    "Adreno (TM) 640",
                    "Adreno (TM) 650",
                    "Mali-G78",
                    "Mali-G77"
                ]
            else:  # ios
                vendors = ["Apple Inc."]
                renderers = ["Apple GPU", "Apple A15 GPU", "Apple A16 GPU"]
        
        return {
            "vendor": random.choice(vendors),
            "renderer": random.choice(renderers)
        }
    
    def _generate_noise_parameters(self) -> Dict:
        """Generate unique noise parameters for canvas and audio"""
        return {
            "canvas": random.uniform(0.01, 0.25),
            "audio": random.uniform(0.01, 0.15),
            "webgl": random.uniform(0.001, 0.01),
            "font": random.uniform(0.01, 0.05)
        }
    
    def _get_platform_string(self, os_type: str, platform_type: str) -> str:
        """Get platform string for navigator.platform"""
        platform_strings = {
            'windows': 'Win32',
            'linux': 'Linux x86_64',
            'darwin': 'MacIntel',
            'android': 'Linux armv8l',
            'ios': 'iPhone'
        }
        return platform_strings.get(os_type, 'Win32')
    
    def _generate_dynamic_headers(self, browser_type: str, platform_type: str, user_agent: str) -> Dict:
        """Generate dynamic, realistic HTTP headers"""
        # Try to get from loaded data first
        try:
            base_headers = self.browser_data['headers'].get(browser_type, {})
        except (KeyError, TypeError):
            base_headers = {}
        
        # Core headers that should always be present
        headers = {
            "User-Agent": user_agent,
            "Accept": random.choice([
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "*/*"
            ]),
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-GB,en;q=0.9",
                "en-US,en;q=0.8,es;q=0.6",
                "en;q=0.9",
                "en-US,en;q=0.9,fr;q=0.8",
                "en-US,en;q=0.9,de;q=0.8"
            ]),
            "Accept-Encoding": "gzip, deflate, br"
        }
        
        # Browser-specific headers
        if browser_type in ['chrome', 'edge']:
            # Chrome/Edge specific Sec-CH-UA headers
            major_version = random.randint(110, 122)
            headers.update({
                "Sec-Ch-Ua": f'"Not_A Brand";v="8", "Chromium";v="{major_version}", "{browser_type.title()}";v="{major_version}"',
                "Sec-Ch-Ua-Mobile": "?1" if platform_type == 'mobile' else "?0",
                "Sec-Ch-Ua-Platform": f'"{self._get_platform_string("windows", "desktop")}"',
                "Sec-Fetch-Dest": random.choice(["document", "empty", "iframe"]),
                "Sec-Fetch-Mode": random.choice(["navigate", "cors", "same-origin"]),
                "Sec-Fetch-Site": random.choice(["none", "same-origin", "cross-site"]),
                "Sec-Fetch-User": "?1"
            })
            
            # Randomly add additional Sec-CH headers
            if random.random() < 0.3:
                headers["Sec-Ch-Ua-Arch"] = random.choice(['"x86"', '""'])
                headers["Sec-Ch-Ua-Bitness"] = '"64"'
                headers["Sec-Ch-Ua-Full-Version-List"] = f'"Not_A Brand";v="8.0.0.0", "Chromium";v="{major_version}.0.0.0"'
            
            # Sometimes add client hints
            if random.random() < 0.2:
                headers["Sec-Ch-Prefers-Color-Scheme"] = random.choice(["light", "dark"])
                headers["Sec-Ch-Prefers-Reduced-Motion"] = "no-preference"
        
        # Randomly add optional headers
        optional_headers = {
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": random.choice(["no-cache", "max-age=0", "no-store"]),
            "Pragma": "no-cache",
            "DNT": random.choice(["1", None]),  # Sometimes include, sometimes don't
            "Connection": random.choice(["keep-alive", "close"]),
            "Save-Data": "on" if random.random() < 0.1 else None,
            "Purpose": "prefetch" if random.random() < 0.05 else None
        }
        
        for key, value in optional_headers.items():
            if value is not None and random.random() < 0.7:  # 70% chance to include
                headers[key] = value
        
        # Update with browser-specific headers from loaded data
        headers.update({k: v for k, v in base_headers.items() if k not in headers})
        
        # Randomize header order
        keys = list(headers.keys())
        random.shuffle(keys)
        return {k: headers[k] for k in keys}
    
    def _get_cipher_suites(self, browser_type: str) -> List[str]:
        """Get cipher suites for browser type"""
        try:
            suites = self.browser_data['cipherSuite'].get(browser_type, [])
            if suites:
                # Return a random subset in random order
                num_suites = random.randint(10, min(20, len(suites)))
                selected = random.sample(suites, num_suites)
                random.shuffle(selected)
                return selected
        except (KeyError, TypeError):
            pass
        
        # Fallback cipher suites
        default_suites = [
            "TLS_AES_128_GCM_SHA256",
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "ECDHE-ECDSA-AES128-GCM-SHA256",
            "ECDHE-RSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES256-GCM-SHA384"
        ]
        return default_suites
    
    def _generate_connection_info(self) -> Dict:
        """Generate network connection information"""
        return {
            "effectiveType": random.choice(["4g", "3g", "slow-2g"]),
            "rtt": random.randint(50, 300),
            "downlink": random.uniform(1.0, 10.0),
            "saveData": random.choice([True, False])
        }
    
    def _generate_battery_info(self, platform_type: str) -> Dict:
        """Generate battery information"""
        if platform_type == 'desktop':
            # Desktop usually plugged in
            return {
                "charging": True,
                "chargingTime": 0,
                "dischargingTime": float('inf'),
                "level": 1.0
            }
        else:
            # Mobile battery varies
            charging = random.random() < 0.3
            level = random.uniform(0.1, 1.0)
            return {
                "charging": charging,
                "chargingTime": 0 if not charging else random.randint(0, 7200),
                "dischargingTime": float('inf') if charging else random.randint(3600, 28800),
                "level": level
            }
    
    def _generate_media_devices(self) -> List[Dict]:
        """Generate media device information"""
        devices = []
        
        # Microphones
        num_mics = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        for i in range(num_mics):
            devices.append({
                "deviceId": hashlib.md5(f"mic_{i}_{random.random()}".encode()).hexdigest(),
                "kind": "audioinput",
                "label": random.choice(["Default", "Built-in Microphone", "External Microphone", ""]),
                "groupId": hashlib.md5(f"group_audio_{random.random()}".encode()).hexdigest()
            })
        
        # Speakers
        num_speakers = random.choices([1, 2], weights=[70, 30])[0]
        for i in range(num_speakers):
            devices.append({
                "deviceId": hashlib.md5(f"speaker_{i}_{random.random()}".encode()).hexdigest(),
                "kind": "audiooutput",
                "label": random.choice(["Default", "Built-in Speakers", "External Speakers", ""]),
                "groupId": hashlib.md5(f"group_audio_{random.random()}".encode()).hexdigest()
            })
        
        # Cameras
        num_cameras = random.choices([0, 1, 2], weights=[10, 70, 20])[0]
        for i in range(num_cameras):
            devices.append({
                "deviceId": hashlib.md5(f"camera_{i}_{random.random()}".encode()).hexdigest(),
                "kind": "videoinput",
                "label": random.choice(["Default", "FaceTime HD Camera", "Integrated Camera", ""]),
                "groupId": hashlib.md5(f"group_video_{random.random()}".encode()).hexdigest()
            })
        
        return devices
    
    def _generate_plugins(self, browser_type: str, platform_type: str) -> List[Dict]:
        """Generate plugin information"""
        if platform_type == 'mobile':
            return []  # Mobile browsers typically don't report plugins
        
        if browser_type == 'firefox':
            # Firefox typically reports fewer plugins
            return []
        
        # Chrome-based browsers
        plugins = []
        
        # PDF plugins
        if random.random() < 0.9:
            plugins.append({
                "name": "Chrome PDF Plugin",
                "filename": "internal-pdf-viewer",
                "description": "Portable Document Format",
                "mimeTypes": [{"type": "application/pdf", "suffixes": "pdf"}]
            })
        
        if random.random() < 0.7:
            plugins.append({
                "name": "Chrome PDF Viewer",
                "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                "description": "",
                "mimeTypes": [{"type": "application/pdf", "suffixes": "pdf"}]
            })
        
        # Native Client (older Chrome)
        if random.random() < 0.3:
            plugins.append({
                "name": "Native Client",
                "filename": "internal-nacl-plugin",
                "description": "",
                "mimeTypes": [
                    {"type": "application/x-nacl", "suffixes": ""},
                    {"type": "application/x-pnacl", "suffixes": ""}
                ]
            })
        
        return plugins
    
    def _generate_profile_hash(self, user_agent: str, viewport: Dict, screen: Dict) -> str:
        """Generate unique hash for profile to track usage"""
        data = f"{user_agent}_{viewport}_{screen}_{time.time()}_{random.random()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_profile_by_type(self, profile_type: str = "balanced") -> Dict:
        """Get profile by specific characteristics"""
        if profile_type == "high_end":
            profile = self.get_random_profile()
            profile['hardware_concurrency'] = random.choice([12, 16, 24, 32])
            profile['device_memory'] = random.choice([16, 32, 64])
        elif profile_type == "mobile_like":
            profile = self.get_random_profile()
            profile['viewport'] = {"width": random.randint(360, 428), "height": random.randint(640, 926)}
        elif profile_type == "corporate":
            profile = self.get_random_profile()
            profile['timezone'] = random.choice(['America/New_York', 'America/Chicago', 'Europe/London'])
            profile['language'] = 'en-US'
        else:
            profile = self.get_random_profile()
        
        return profile
    
    def generate_anti_fingerprintjs_script(self, profile: Dict) -> str:
        """Generate ultra-dynamic anti-fingerprinting script"""
        # Generate random seed for this session
        session_seed = random.randint(1000000, 9999999)
        entropy_seed = random.randint(1000000, 9999999)
        
        # Dynamic script generation with runtime randomization
        return f"""
        // Ultra-Dynamic Anti-Fingerprinting v3.0 - Session {profile['fingerprint_hash'][:8]}
        (function() {{
            'use strict';
            
            console.log('🛡️ Loading dynamic fingerprint evasion: {profile["name"]}');
            
            // Dynamic random generation with multiple entropy sources
            let seed = {session_seed};
            let entropy = {entropy_seed};
            let counter = 0;
            const originalRandom = Math.random;
            
            Math.random = function() {{
                // Mix multiple PRNG algorithms for unpredictability
                seed = (seed * 9301 + 49297) % 233280;
                entropy = (entropy * 16807) % 2147483647;
                counter = (counter * 1103515245 + 12345) % 2147483648;
                
                // Combine three different sources
                const val1 = seed / 233280;
                const val2 = entropy / 2147483647;
                const val3 = counter / 2147483648;
                
                // Add time-based entropy
                const timeEntropy = (Date.now() % 1000) / 1000;
                
                return ((val1 + val2 + val3 + timeEntropy) / 4) % 1;
            }};
            
            // Dynamic Navigator properties with runtime variations
            const navigatorProps = {{
                userAgent: {{
                    get: () => {{
                        // Add micro-variations at runtime
                        const ua = '{profile["user_agent"]}';
                        if (Math.random() < 0.01) {{
                            // 1% chance to slightly modify UA
                            return ua.replace(/Chrome\/(\d+)/, (match, p1) => 'Chrome/' + (parseInt(p1) + Math.floor(Math.random() * 3)));
                        }}
                        return ua;
                    }},
                    configurable: true
                }},
                language: {{
                    get: () => {{
                        const langs = {json.dumps(profile.get("languages", ["en-US", "en"]))};
                        return langs[0] || '{profile["language"]}';
                    }},
                    configurable: true
                }},
                languages: {{
                    get: () => {{
                        const langs = {json.dumps(profile.get("languages", ["en-US", "en"]))};
                        // Sometimes shuffle the order
                        if (Math.random() < 0.1) {{
                            return [...langs].sort(() => Math.random() - 0.5);
                        }}
                        return langs;
                    }},
                    configurable: true
                }},
                platform: {{
                    get: () => '{profile["platform"]}',
                    configurable: true
                }},
                hardwareConcurrency: {{
                    get: () => {{
                        // Add slight variations
                        const base = {profile["hardware_concurrency"]};
                        if (Math.random() < 0.05) {{
                            return Math.max(1, base + (Math.random() < 0.5 ? -1 : 1));
                        }}
                        return base;
                    }},
                    configurable: true
                }},
                deviceMemory: {{
                    get: () => {profile.get("device_memory", 8)},
                    configurable: true
                }},
                maxTouchPoints: {{
                    get: () => {profile.get("max_touch_points", 0)},
                    configurable: true
                }},
                webdriver: {{
                    get: () => undefined,
                    configurable: true
                }},
                vendor: {{
                    get: () => {{
                        const vendors = ['Google Inc.', '', 'Apple Computer, Inc.'];
                        return vendors[Math.floor(Math.random() * vendors.length)];
                    }},
                    configurable: true
                }},
                doNotTrack: {{
                    get: () => {json.dumps(profile.get("do_not_track"))},
                    configurable: true
                }},
                connection: {{
                    get: () => ({{
                        effectiveType: '{profile.get("connection_info", {}).get("effectiveType", "4g")}',
                        rtt: {profile.get("connection_info", {}).get("rtt", 100)} + Math.floor(Math.random() * 50),
                        downlink: {profile.get("connection_info", {}).get("downlink", 10)} + Math.random(),
                        saveData: {str(profile.get("connection_info", {}).get("saveData", False)).lower()}
                    }}),
                    configurable: true
                }}
            }};
            
            // Apply navigator overrides
            try {{
                for (const [prop, descriptor] of Object.entries(navigatorProps)) {{
                    Object.defineProperty(navigator, prop, descriptor);
                }}
            }} catch (e) {{
                console.warn('Navigator override failed:', e);
            }}
            
            // Dynamic Screen properties
            const screenProps = {{
                width: {{
                    get: () => {profile["screen"]["width"]} + Math.floor(Math.random() * 10) - 5,
                    configurable: true
                }},
                height: {{
                    get: () => {profile["screen"]["height"]} + Math.floor(Math.random() * 10) - 5,
                    configurable: true
                }},
                availWidth: {{
                    get: () => {profile["screen"].get("availWidth", profile["screen"]["width"])},
                    configurable: true
                }},
                availHeight: {{
                    get: () => {profile["screen"].get("availHeight", profile["screen"]["height"] - 40)},
                    configurable: true
                }},
                colorDepth: {{
                    get: () => {profile["screen"].get("colorDepth", 24)},
                    configurable: true
                }},
                pixelDepth: {{
                    get: () => {profile["screen"].get("pixelDepth", 24)},
                    configurable: true
                }},
                orientation: {{
                    get: () => ({json.dumps(profile["screen"].get("orientation", {"angle": 0, "type": "landscape-primary"}))}),
                    configurable: true
                }}
            }};
            
            // Apply screen overrides
            try {{
                for (const [prop, descriptor] of Object.entries(screenProps)) {{
                    Object.defineProperty(screen, prop, descriptor);
                }}
            }} catch (e) {{
                console.warn('Screen override failed:', e);
            }}
            
            // Ultra-Dynamic Canvas Protection
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            const canvasNoise = {profile.get("canvas_noise", 0.1)};
            
            HTMLCanvasElement.prototype.getContext = function(type, ...args) {{
                const context = originalGetContext.call(this, type, ...args);
                
                if (type === '2d' && context) {{
                    // Wrap all drawing methods with noise
                    const methods = ['fillRect', 'strokeRect', 'fillText', 'strokeText', 'arc', 'bezierCurveTo', 'quadraticCurveTo'];
                    
                    methods.forEach(method => {{
                        if (context[method]) {{
                            const original = context[method];
                            context[method] = function(...params) {{
                                // Add noise to numeric parameters
                                const noisyParams = params.map(param => {{
                                    if (typeof param === 'number') {{
                                        return param + (Math.random() - 0.5) * canvasNoise;
                                    }}
                                    return param;
                                }});
                                return original.apply(this, noisyParams);
                            }};
                        }}
                    }});
                    
                    // Override getImageData to add noise
                    const originalGetImageData = context.getImageData;
                    context.getImageData = function(...args) {{
                        const imageData = originalGetImageData.apply(this, args);
                        // Add random noise to pixels
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            if (Math.random() < 0.001) {{ // 0.1% of pixels
                                imageData.data[i] = Math.min(255, Math.max(0, imageData.data[i] + Math.floor(Math.random() * 5) - 2));
                                imageData.data[i + 1] = Math.min(255, Math.max(0, imageData.data[i + 1] + Math.floor(Math.random() * 5) - 2));
                                imageData.data[i + 2] = Math.min(255, Math.max(0, imageData.data[i + 2] + Math.floor(Math.random() * 5) - 2));
                            }}
                        }}
                        return imageData;
                    }};
                }}
                
                if ((type === 'webgl' || type === 'webgl2' || type === 'experimental-webgl') && context) {{
                    const getParameter = context.getParameter;
                    context.getParameter = function(parameter) {{
                        // WebGL spoofing
                        switch (parameter) {{
                            case context.VENDOR:
                            case 0x9245:
                                return '{profile.get("webgl_vendor", "Google Inc.")}';
                            case context.RENDERER:
                            case 0x9246:
                                return '{profile.get("webgl_renderer", "ANGLE")}';
                            case context.VERSION:
                                return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
                            case context.SHADING_LANGUAGE_VERSION:
                                return 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)';
                            default:
                                return getParameter.call(this, parameter);
                        }}
                    }};
                    
                    // Dynamic WebGL extensions
                    const getSupportedExtensions = context.getSupportedExtensions;
                    context.getSupportedExtensions = function() {{
                        const extensions = getSupportedExtensions.call(this);
                        // Randomly filter some extensions
                        if (Math.random() < 0.1) {{
                            return extensions.filter(() => Math.random() > 0.1);
                        }}
                        return extensions;
                    }};
                }}
                
                return context;
            }};
            
            // Dynamic Audio Context Protection
            if (window.AudioContext || window.webkitAudioContext) {{
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                const audioNoise = {profile.get("audio_noise", 0.05)};
                
                const originalCreateOscillator = AudioContextClass.prototype.createOscillator;
                AudioContextClass.prototype.createOscillator = function() {{
                    const oscillator = originalCreateOscillator.call(this);
                    const originalConnect = oscillator.connect;
                    
                    oscillator.connect = function(destination) {{
                        // Add slight frequency variation
                        if (oscillator.frequency && oscillator.frequency.value) {{
                            oscillator.frequency.value += (Math.random() - 0.5) * audioNoise;
                        }}
                        return originalConnect.call(this, destination);
                    }};
                    
                    return oscillator;
                }};
            }}
            
            // Dynamic timezone spoofing
            const timezoneOffset = {{
                'America/New_York': 300,
                'America/Los_Angeles': 480,
                'America/Chicago': 360,
                'Europe/London': 0,
                'Europe/Berlin': -60,
                'Europe/Paris': -60,
                'Asia/Tokyo': -540,
                'Asia/Shanghai': -480
            }}['{profile.get("timezone", "America/New_York")}'] || 0;
            
            Date.prototype.getTimezoneOffset = function() {{
                // Add slight variation
                return timezoneOffset + Math.floor(Math.random() * 3) - 1;
            }};
            
            // Dynamic Plugin spoofing
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {{
                    const plugins = {json.dumps(profile.get("plugins", []))};
                    
                    // Create plugin-like objects
                    return {{
                        length: plugins.length,
                        ...plugins.reduce((acc, plugin, i) => {{
                            acc[i] = plugin;
                            acc[plugin.name] = plugin;
                            return acc;
                        }}, {{}})
                    }};
                }},
                configurable: true
            }});
            
            // Battery API with dynamic values
            if (navigator.getBattery) {{
                const batteryInfo = {json.dumps(profile.get("battery_info", {"charging": True, "level": 1.0}))};
                navigator.getBattery = function() {{
                    return Promise.resolve({{
                        ...batteryInfo,
                        level: Math.max(0.1, Math.min(1.0, batteryInfo.level + (Math.random() - 0.5) * 0.1))
                    }});
                }};
            }}
            
            // Media Devices spoofing
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
                const devices = {json.dumps(profile.get("media_devices", []))};
                navigator.mediaDevices.enumerateDevices = function() {{
                    return Promise.resolve(devices);
                }};
            }}
            
            // Remove automation indicators
            const deleteProps = [
                'webdriver', '__webdriver_script_fn', '__driver_evaluate', '__webdriver_evaluate',
                '__selenium_evaluate', '__fxdriver_evaluate', '__driver_unwrapped', '__webdriver_unwrapped',
                '__selenium_unwrapped', '__fxdriver_unwrapped', '_Selenium_IDE_Recorder', '_selenium',
                'calledSelenium', '_WEBDRIVER_ELEM_CACHE', 'ChromeDriverw', '__webdriverFunc',
                'domAutomation', 'domAutomationController', '__lastWatirAlert', '__lastWatirConfirm',
                '__lastWatirPrompt', '$chrome_asyncScriptInfo', '$cdc_asdjflasutopfhvcZLmcfl_'
            ];
            
            deleteProps.forEach(prop => {{
                try {{
                    delete window[prop];
                    delete document[prop];
                    delete navigator[prop];
                }} catch (e) {{}}
            }});
            
            // Chrome specific
            if (window.chrome) {{
                window.chrome = {{
                    runtime: {{}},
                    loadTimes: function() {{
                        return {{
                            requestTime: Date.now() / 1000,
                            startLoadTime: Date.now() / 1000,
                            commitLoadTime: Date.now() / 1000,
                            finishDocumentLoadTime: Date.now() / 1000,
                            finishLoadTime: Date.now() / 1000,
                            firstPaintTime: Date.now() / 1000,
                            firstPaintAfterLoadTime: 0,
                            navigationType: "Other"
                        }};
                    }},
                    csi: function() {{ return {{}}; }}
                }};
            }}
            
            // Permission API
            if (navigator.permissions && navigator.permissions.query) {{
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {{
                    // Randomize some permissions
                    const permissions = {{
                        'notifications': Math.random() > 0.5 ? 'granted' : 'denied',
                        'geolocation': Math.random() > 0.3 ? 'granted' : 'prompt',
                        'camera': Math.random() > 0.7 ? 'granted' : 'denied',
                        'microphone': Math.random() > 0.7 ? 'granted' : 'denied'
                    }};
                    
                    const state = permissions[parameters.name] || 'prompt';
                    return Promise.resolve({{ state, name: parameters.name }});
                }};
            }}
            
            console.log('✅ Dynamic fingerprint evasion active');
            console.log('🔐 Session hash: {profile["fingerprint_hash"][:16]}');
            console.log('🎲 Entropy: {session_seed}/{entropy_seed}');
            
        }})();
        """
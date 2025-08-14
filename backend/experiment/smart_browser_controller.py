import asyncio
import time
import random
import logging
import re
import json
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from browser_controller import BrowserController
from fingerprint_evasion import AdvancedFingerprintEvasion
from proxy_manager import AdvancedProxyManager, ProxyType
import base64
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class Bypass403Engine:
    """Advanced 403/Anti-bot bypass engine with all known techniques"""
    
    def __init__(self):
        self.bypass_attempts = []
        self.successful_bypasses = {}  # Track what works for each domain
        self.failed_bypasses = {}
        
        # Path manipulation payloads
        self.path_payloads = [
            lambda p: p,  # Original
            lambda p: f"%2e/{p}",  # URL encoded dot
            lambda p: f"{p}/.",  # Trailing dot
            lambda p: f"//{p}//",  # Double slashes
            lambda p: f"./{p}/./",  # Current directory
            lambda p: f"{p}%20",  # Space
            lambda p: f"{p}%09",  # Tab
            lambda p: f"{p}?",  # Question mark
            lambda p: f"{p}#",  # Hash
            lambda p: f"{p}.html",  # Add extension
            lambda p: f"{p}.php",
            lambda p: f"{p}.json",
            lambda p: f"{p}/*",  # Wildcard
            lambda p: f"{p}/../{p}",  # Directory traversal
            lambda p: f"{p};/",  # Semicolon
            lambda p: f"{p}..;/",  # Dot dot semicolon
            lambda p: p.upper(),  # Uppercase
            lambda p: p.lower(),  # Lowercase
            lambda p: self._random_case(p),  # Random case
            lambda p: p[0].upper() + p[1:] if len(p) > 1 else p.upper(),  # Capitalize first
            lambda p: f"{p}/?anything={random.randint(1000,9999)}",  # Random parameter
            lambda p: f"{p}/index.html",
            lambda p: f"{p}/index.php",
            lambda p: f"{p}%00",  # Null byte
            lambda p: f"{p}%2f",  # Encoded slash
            lambda p: f"{p}%5c",  # Encoded backslash
            lambda p: f"{p}%3f",  # Encoded question mark
            lambda p: f"{p}%23",  # Encoded hash
            lambda p: f"{p}%25",  # Encoded percent
            lambda p: f"{p}~",  # Tilde
            lambda p: f"{p}!",  # Exclamation
            lambda p: f"{p}@",  # At sign
            lambda p: f"{p}$",  # Dollar
            lambda p: f"{p}^",  # Caret
            lambda p: f"{p}&",  # Ampersand
            lambda p: f"{p}*",  # Asterisk
            lambda p: f"{p}()",  # Parentheses
            lambda p: f"{p}[]",  # Brackets
            lambda p: f"{p}{{}}",  # Braces
        ]
        
        # Header manipulation payloads
        self.header_payloads = [
            {},  # No extra headers
            {"X-Forwarded-For": "127.0.0.1"},
            {"X-Forwarded-For": "127.0.0.1:80"},
            {"X-Forwarded-For": "127.0.0.1, 127.0.0.2"},
            {"X-Forwarded-For": "http://127.0.0.1"},
            {"X-Real-IP": "127.0.0.1"},
            {"X-Originating-IP": "127.0.0.1"},
            {"X-Remote-IP": "127.0.0.1"},
            {"X-Remote-Addr": "127.0.0.1"},
            {"X-Client-IP": "127.0.0.1"},
            {"X-Host": "127.0.0.1"},
            {"X-Forwarded-Host": "127.0.0.1"},
            {"X-Forwarded-Server": "127.0.0.1"},
            {"X-Custom-IP-Authorization": "127.0.0.1"},
            {"X-Original-URL": lambda path: path},
            {"X-Rewrite-URL": lambda path: path},
            {"X-Proxy-User-IP": "127.0.0.1"},
            {"Client-IP": "127.0.0.1"},
            {"True-Client-IP": "127.0.0.1"},
            {"Cluster-Client-IP": "127.0.0.1"},
            {"X-ProxyUser-IP": "127.0.0.1"},
            {"X-HTTP-Method-Override": "GET"},
            {"X-HTTP-Method-Override": "POST"},
            {"X-Method-Override": "GET"},
            {"X-Method-Override": "POST"},
            {"Content-Length": "0"},
            {"Content-Type": "application/x-www-form-urlencoded"},
            {"Transfer-Encoding": "chunked"},
            {"Referer": "https://google.com"},
            {"Referer": lambda url: url},
            {"Origin": "https://google.com"},
            {"Origin": lambda url: url},
            # Multiple headers combination
            {"X-Forwarded-For": "127.0.0.1", "X-Real-IP": "127.0.0.1"},
            {"X-Forwarded-For": "127.0.0.1", "X-Forwarded-Host": "127.0.0.1"},
            {"X-Original-URL": lambda path: path, "X-Rewrite-URL": lambda path: path},
            # WAF bypass headers
            {"X-Forwarded-For": "127.0.0.1", "X-Forwarded-Proto": "https"},
            {"X-Forwarded-For": "127.0.0.1", "X-Forwarded-Port": "443"},
            {"X-Forwarded-For": "localhost"},
            {"X-Forwarded-For": "::1"},  # IPv6 localhost
            {"X-Forwarded-For": "0000:0000:0000:0000:0000:0000:0000:0001"},  # Full IPv6
            {"X-Forwarded-For": "2130706433"},  # Decimal IP for 127.0.0.1
            {"X-Forwarded-For": "0x7f000001"},  # Hex IP for 127.0.0.1
            {"X-Forwarded-For": "0177.0.0.1"},  # Octal IP
            {"X-Forwarded-For": "127.1"},  # Short IP notation
            {"X-Forwarded-For": "10.0.0.1"},  # Private IP
            {"X-Forwarded-For": "172.16.0.1"},  # Private IP
            {"X-Forwarded-For": "192.168.1.1"},  # Private IP
            # Cloudflare specific
            {"CF-Connecting-IP": "127.0.0.1"},
            {"CF-IPCountry": "US"},
            {"CF-RAY": self._generate_cf_ray()},
            {"CF-Visitor": '{"scheme":"https"}'},
            # Akamai specific
            {"Akamai-Origin-Hop": "1"},
            {"X-Akamai-Edgescape": "georegion=246,country_code=US,region_code=CA"},
            # AWS specific
            {"X-Amzn-Trace-Id": self._generate_aws_trace()},
            {"X-AWS-EC2-Client-IP": "127.0.0.1"},
            # Azure specific
            {"X-Azure-ClientIP": "127.0.0.1"},
            {"X-Azure-SocketIP": "127.0.0.1"},
            # Fastly specific
            {"Fastly-Client-IP": "127.0.0.1"},
            {"X-Fastly-Client-IP": "127.0.0.1"},
        ]
        
        # HTTP methods
        self.methods = ["GET", "POST", "HEAD", "OPTIONS", "PUT", "DELETE", "TRACE", "PATCH", "CONNECT"]
        
        # Protocol variations
        self.protocol_versions = ["HTTP/1.0", "HTTP/1.1", "HTTP/2"]
    
    def _random_case(self, text: str) -> str:
        """Randomize case of text"""
        return ''.join(random.choice([c.upper(), c.lower()]) for c in text)
    
    def _generate_cf_ray(self) -> str:
        """Generate realistic Cloudflare Ray ID"""
        return f"{random.randint(100000000000, 999999999999):x}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}"
    
    def _generate_aws_trace(self) -> str:
        """Generate realistic AWS trace ID"""
        return f"Root=1-{int(time.time()):x}-{random.randint(100000000000, 999999999999):x}"
    
    async def try_bypass(self, browser, url: str, original_path: str, max_attempts: int = 50) -> Optional[Dict]:
        """Try various bypass techniques"""
        logger.info(f"🔓 Starting bypass attempts for: {url}")
        
        domain = urlparse(url).netloc
        attempts = 0
        
        # Check if we have successful bypasses for this domain
        if domain in self.successful_bypasses:
            logger.info(f"✅ Using previously successful bypass for {domain}")
            technique = self.successful_bypasses[domain]
            result = await self._apply_bypass_technique(browser, url, original_path, technique)
            if result and result.get('success'):
                return result
        
        # Try all combinations systematically
        for method in self._get_prioritized_methods(domain):
            for path_func in self._get_prioritized_paths(domain):
                for headers_template in self._get_prioritized_headers(domain):
                    attempts += 1
                    if attempts > max_attempts:
                        logger.warning(f"⚠️ Reached max attempts ({max_attempts})")
                        return None
                    
                    # Apply path manipulation
                    try:
                        modified_path = path_func(original_path)
                    except:
                        modified_path = original_path
                    
                    # Build headers
                    headers = {}
                    for key, value in headers_template.items():
                        if callable(value):
                            headers[key] = value(original_path)
                        else:
                            headers[key] = value
                    
                    # Create bypass technique
                    technique = {
                        'method': method,
                        'path': modified_path,
                        'headers': headers
                    }
                    
                    # Try the bypass
                    result = await self._apply_bypass_technique(browser, url, modified_path, technique)
                    
                    if result and result.get('success'):
                        logger.info(f"✅ Bypass successful! Method: {method}, Path: {modified_path[:50]}, Headers: {list(headers.keys())}")
                        
                        # Store successful bypass for future use
                        self.successful_bypasses[domain] = technique
                        
                        # Save to file for persistence
                        self._save_successful_bypass(domain, technique)
                        
                        return result
                    
                    # Small delay between attempts
                    await asyncio.sleep(random.uniform(0.1, 0.3))
        
        logger.warning(f"❌ All bypass attempts failed for {url}")
        return None
    
    def _get_prioritized_methods(self, domain: str) -> List[str]:
        """Get methods prioritized by success rate for domain"""
        # Start with most likely to succeed
        priority = ["GET", "POST", "OPTIONS", "HEAD"]
        others = [m for m in self.methods if m not in priority]
        random.shuffle(others)
        return priority + others
    
    def _get_prioritized_paths(self, domain: str) -> List:
        """Get path manipulations prioritized by success rate"""
        # Start with most effective techniques
        priority = [
            lambda p: p,  # Original
            lambda p: self._random_case(p),  # Case manipulation (very effective)
            lambda p: p[0].upper() + p[1:] if len(p) > 1 else p.upper(),  # Capitalize
            lambda p: f"{p}/.",  # Trailing dot
            lambda p: f"%2e/{p}",  # URL encoded
            lambda p: f"{p}%20",  # Space
        ]
        
        others = [p for p in self.path_payloads if p not in priority]
        random.shuffle(others)
        return priority + others
    
    def _get_prioritized_headers(self, domain: str) -> List[Dict]:
        """Get headers prioritized by success rate"""
        # Start with most effective headers
        priority = [
            {},  # Try without headers first
            {"X-Forwarded-For": "127.0.0.1"},
            {"X-Real-IP": "127.0.0.1"},
            {"X-Original-URL": lambda path: path},
            {"X-Forwarded-For": "127.0.0.1", "X-Real-IP": "127.0.0.1"},
        ]
        
        others = [h for h in self.header_payloads if h not in priority]
        random.shuffle(others)
        return priority + others
    
    async def _apply_bypass_technique(self, browser, base_url: str, path: str, technique: Dict) -> Optional[Dict]:
        """Apply a specific bypass technique"""
        try:
            # Build full URL
            parsed = urlparse(base_url)
            if path.startswith('/'):
                full_url = f"{parsed.scheme}://{parsed.netloc}{path}"
            else:
                full_url = f"{parsed.scheme}://{parsed.netloc}/{path}"
            
            # Log attempt
            logger.debug(f"🔧 Trying: {technique['method']} {full_url[:100]} with headers: {list(technique['headers'].keys())}")
            
            # Set headers
            if technique['headers']:
                await browser.page.set_extra_http_headers(technique['headers'])
            
            # Navigate based on method
            if technique['method'] in ['GET', 'HEAD']:
                response = await browser.page.goto(full_url, wait_until='domcontentloaded', timeout=10000)
            elif technique['method'] == 'POST':
                # For POST, we need to evaluate JavaScript
                response = await browser.page.evaluate(f"""
                    async () => {{
                        const response = await fetch('{full_url}', {{
                            method: 'POST',
                            headers: {json.dumps(technique['headers'])}
                        }});
                        return {{
                            status: response.status,
                            url: response.url
                        }};
                    }}
                """)
            else:
                # For other methods, use fetch API
                response = await browser.page.evaluate(f"""
                    async () => {{
                        const response = await fetch('{full_url}', {{
                            method: '{technique['method']}',
                            headers: {json.dumps(technique['headers'])}
                        }});
                        return {{
                            status: response.status,
                            url: response.url
                        }};
                    }}
                """)
            
            # Check if bypass was successful
            if response:
                status_code = response.status if hasattr(response, 'status') else response.get('status', 0)
                
                if status_code and status_code not in [403, 401, 429, 503]:
                    # Check for anti-bot systems using vision
                    if hasattr(browser, 'proxy_manager') and browser.proxy_manager:
                        is_blocked, block_type, _ = await browser.proxy_manager.detect_anti_bot_with_vision(
                            browser.page, f"checking {full_url}"
                        )
                        
                        if not is_blocked:
                            return {
                                'success': True,
                                'url': full_url,
                                'status': status_code,
                                'technique': technique
                            }
            
        except Exception as e:
            logger.debug(f"⚠️ Bypass attempt failed: {e}")
        
        return None
    
    def _save_successful_bypass(self, domain: str, technique: Dict):
        """Save successful bypass technique for future use"""
        try:
            import json
            filename = "successful_bypasses.json"
            
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
            except:
                data = {}
            
            data[domain] = {
                'method': technique['method'],
                'path_pattern': str(technique.get('path', '')),
                'headers': {k: str(v) for k, v in technique['headers'].items()},
                'timestamp': time.time()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            logger.debug(f"Could not save bypass technique: {e}")
    
    def load_successful_bypasses(self):
        """Load previously successful bypasses"""
        try:
            import json
            with open("successful_bypasses.json", 'r') as f:
                data = json.load(f)
                for domain, technique in data.items():
                    self.successful_bypasses[domain] = technique
                logger.info(f"📚 Loaded {len(data)} successful bypass techniques")
        except:
            pass


class EnhancedSmartBrowserController(BrowserController):
    """Enhanced browser controller with ultra-dynamic fingerprinting and bypass techniques"""
    
    def __init__(self, headless: bool, proxy: dict | None, enable_streaming: bool = False):
        super().__init__(headless, proxy, enable_streaming)
        
        # Initialize enhanced components
        self.fingerprint_evasion = AdvancedFingerprintEvasion()
        self.bypass_engine = Bypass403Engine()
        self.bypass_engine.load_successful_bypasses()
        
        # Initialize proxy manager with vision model
        from anti_bot_detection import AntiBotVisionModel
        self.vision_model = AntiBotVisionModel()
        self.proxy_manager = AdvancedProxyManager(self.vision_model)
        
        # Enhanced tracking
        self.current_fingerprint_profile = None
        self.current_proxy = proxy
        self.fingerprint_rotation_count = 0
        self.last_fingerprint_rotation = time.time()
        self.max_proxy_retries = 10
        self.max_captcha_solve_attempts = 3
        self.navigation_history = []
        
        # Dynamic rotation settings
        self.fingerprint_rotation_interval = random.randint(300, 900)  # 5-15 minutes
        self.proxy_rotation_threshold = random.randint(5, 15)  # Failed requests before rotation

    async def __aenter__(self):
        """Initialize with ultra-dynamic fingerprint evasion"""
        try:
            # Get completely unique fingerprint profile
            self.current_fingerprint_profile = self.fingerprint_evasion.get_random_profile()
            logger.info(f"🎭 Using dynamic fingerprint: {self.current_fingerprint_profile['name']}")
            logger.info(f"🔐 Fingerprint hash: {self.current_fingerprint_profile['fingerprint_hash'][:16]}...")
            
            # Log detailed fingerprint info
            logger.info(f"📱 User Agent: {self.current_fingerprint_profile['user_agent'][:100]}...")
            logger.info(f"🖥️ Viewport: {self.current_fingerprint_profile['viewport']}")
            logger.info(f"🌍 Timezone: {self.current_fingerprint_profile['timezone']}")
            logger.info(f"🔧 Hardware: {self.current_fingerprint_profile['hardware_concurrency']} cores, {self.current_fingerprint_profile['device_memory']}GB RAM")
            
            # Initialize Playwright
            self.play = await async_playwright().start()
            
            # Create dynamic user data directory
            user_data_dir = f"/tmp/browser-profile-{self.current_fingerprint_profile['fingerprint_hash'][:8]}-{random.randint(1000, 9999)}"
            
            # Build dynamic launch arguments (excluding user-data-dir for persistent context)
            launch_args = self._build_dynamic_launch_args(exclude_user_data_dir=True)
            
            # Enhanced launch options
            launch_options = {
                "headless": self.headless,
                "args": launch_args,
                "ignore_default_args": ["--enable-automation"],  # Remove automation flag
            }
            
            # Add proxy if available
            if self.proxy:
                logger.info(f"🔄 Using proxy: {self.proxy}")
                launch_options["proxy"] = self.proxy
            
            # Launch browser with persistent context for better fingerprinting
            self.context = await self.play.chromium.launch_persistent_context(
                user_data_dir,  # Pass as positional argument
                **launch_options,
                # Context-specific settings from fingerprint
                user_agent=self.current_fingerprint_profile["user_agent"],
                viewport=self.current_fingerprint_profile["viewport"],
                locale=self.current_fingerprint_profile["language"],
                timezone_id=self.current_fingerprint_profile["timezone"],
                permissions=["geolocation", "notifications", "camera", "microphone"],
                extra_http_headers=self.current_fingerprint_profile["headers"],
                # Advanced settings
                bypass_csp=True,  # Bypass Content Security Policy
                ignore_https_errors=True,  # Ignore SSL errors
                java_script_enabled=True,
                offline=False,
                color_scheme=random.choice(["light", "dark", "no-preference"]),
                reduced_motion=random.choice(["reduce", "no-preference"]),
                forced_colors=random.choice(["active", "none"]),
                # Device settings
                device_scale_factor=self.current_fingerprint_profile["screen"].get("devicePixelRatio", 1),
                is_mobile="mobile" in self.current_fingerprint_profile["name"].lower(),
                has_touch=self.current_fingerprint_profile.get("max_touch_points", 0) > 0,
            )
            
            # Get browser reference
            self.browser = self.context.browser
            
            # Create new page
            self.page = await self.context.new_page()
            
            # Inject ultra-dynamic fingerprint evasion script
            fingerprint_script = self.fingerprint_evasion.generate_anti_fingerprintjs_script(
                self.current_fingerprint_profile
            )
            await self.page.add_init_script(fingerprint_script)
            
            # Add additional evasion scripts
            await self._inject_additional_evasion_scripts()
            
            # Set up request interception for dynamic header modification
            await self._setup_request_interception()
            
            logger.info("✅ Enhanced browser initialized with ultra-dynamic fingerprinting")
            return self
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced browser: {e}")
            raise


    def _build_dynamic_launch_args(self, exclude_user_data_dir: bool = False) -> List[str]:
        """Build dynamic browser launch arguments with safety checks"""
        try:
            # Safely get viewport dimensions with fallbacks
            viewport_width = max(800, int(self.current_fingerprint_profile.get('viewport', {}).get('width', 1920)))
            viewport_height = max(600, int(self.current_fingerprint_profile.get('viewport', {}).get('height', 1080)))
            
            # Ensure dimensions are reasonable
            viewport_width = min(4000, viewport_width)
            viewport_height = min(3000, viewport_height)
            
            args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor",
                f"--window-size={viewport_width},{viewport_height}",
                "--window-position=0,0",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--password-store=basic",
                "--use-mock-keychain",
            ]
            
            # Safe optional args - avoid any potential range issues
            safe_random_id = random.randint(1000, 9999)  # Always safe range
            
            optional_args = [
                "--disable-gpu" if random.random() < 0.5 else "--enable-gpu-rasterization",
                "--disable-web-security" if random.random() < 0.3 else "",
                "--allow-running-insecure-content" if random.random() < 0.3 else "",
                "--disable-features=IsolateOrigins" if random.random() < 0.4 else "",
                "--disable-site-isolation-trials" if random.random() < 0.4 else "",
                f"--user-data-dir=/tmp/chrome-{safe_random_id}" if (random.random() < 0.2 and not exclude_user_data_dir) else "",
                "--incognito" if random.random() < 0.3 else "",
                "--disable-extensions" if random.random() < 0.7 else "",
                "--disable-sync" if random.random() < 0.8 else "",
            ]
            
            # Filter out empty args
            args.extend([arg for arg in optional_args if arg])
            
            return args
            
        except Exception as e:
            logger.error(f"Error building launch args: {e}")
            # Return minimal safe args
            return [
                "--no-sandbox",
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage",
                "--window-size=1920,1080"
            ]



    async def _inject_additional_evasion_scripts(self):
        """Inject additional evasion scripts"""
        
        # Remove webdriver property
        await self.page.evaluate("""
            () => {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            }
        """)
        
        # Mock permissions
        await self.page.evaluate("""
            () => {
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            }
        """)
        
        # Override console detection
        await self.page.evaluate("""
            () => {
                const originalConsole = window.console;
                Object.defineProperty(window, 'console', {
                    get: () => originalConsole,
                    set: () => {},
                    configurable: false
                });
            }
        """)

    async def _setup_request_interception(self):
        """Set up request interception for dynamic modification"""
        
        async def handle_route(route):
            headers = route.request.headers
            
            # Dynamically modify headers
            if random.random() < 0.1:  # 10% chance to modify
                # Add random header variation
                headers.update(self._generate_dynamic_request_headers())
            
            await route.continue_(headers=headers)
        
        # Enable request interception for all requests
        await self.page.route("**/*", handle_route)

    def _generate_dynamic_request_headers(self) -> Dict:
        """Generate dynamic request headers"""
        headers = {}
        
        # Randomly add headers
        if random.random() < 0.2:
            headers["Cache-Control"] = random.choice(["no-cache", "max-age=0", "no-store"])
        
        if random.random() < 0.1:
            headers["Pragma"] = "no-cache"
        
        if random.random() < 0.05:
            headers["X-Requested-With"] = "XMLHttpRequest"
        
        return headers

    async def smart_navigate(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000) -> bool:
        """Navigate with advanced anti-detection and bypass techniques"""
        site_domain = urlparse(url).netloc
        
        # Check if we need to rotate fingerprint
        if time.time() - self.last_fingerprint_rotation > self.fingerprint_rotation_interval:
            await self._rotate_fingerprint()
        
        for attempt in range(self.max_proxy_retries):
            try:
                logger.info(f"🌐 Smart navigation attempt {attempt + 1}/{self.max_proxy_retries}")
                logger.info(f"🎯 Target: {url}")
                logger.info(f"🔄 Proxy: {self.proxy.get('server', 'None') if self.proxy else 'None'}")
                logger.info(f"🎭 Fingerprint: {self.current_fingerprint_profile['name']}")
                
                start_time = time.time()
                
                # Try direct navigation first
                response = await self.page.goto(url, wait_until=wait_until, timeout=timeout)
                response_time = time.time() - start_time
                
                # Wait for page to stabilize
                await asyncio.sleep(random.uniform(2, 5))
                
                # Handle popups
                await self.handle_popups()
                
                # Check for anti-bot systems using vision
                screenshot_bytes = await self.page.screenshot(type='png')
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                is_antibot, detection_type, suggested_action = await self.proxy_manager.detect_anti_bot_with_vision(
                    self.page, f"navigate to {url}"
                )
                
                if not is_antibot:
                    # Check for 403/blocked status
                    current_url = self.page.url
                    
                    # Check page content for blocking indicators
                    page_content = await self.page.content()
                    if any(indicator in page_content.lower() for indicator in 
                           ['403 forbidden', 'access denied', 'blocked', 'unauthorized']):
                        logger.warning(f"⚠️ Detected blocking content, attempting bypass")
                        
                        # Try bypass techniques
                        parsed_url = urlparse(url)
                        bypass_result = await self.bypass_engine.try_bypass(
                            self, url, parsed_url.path or "/"
                        )
                        
                        if bypass_result and bypass_result.get('success'):
                            logger.info(f"✅ Bypass successful! Navigated to: {bypass_result['url']}")
                            return True
                    else:
                        # Success!
                        logger.info(f"✅ Successfully navigated to: {url}")
                        
                        # Track successful navigation
                        self.navigation_history.append({
                            'url': url,
                            'timestamp': time.time(),
                            'proxy': self.proxy.get('server') if self.proxy else None,
                            'fingerprint': self.current_fingerprint_profile['name']
                        })
                        
                        if self.proxy:
                            proxy_info = next((p for p in self.proxy_manager.proxies 
                                             if p.to_playwright_dict().get('server') == self.proxy.get('server')), None)
                            if proxy_info:
                                self.proxy_manager.mark_proxy_success(proxy_info, response_time)
                        return True
                else:
                    logger.warning(f"🚫 Anti-bot detected: {detection_type}, action: {suggested_action}")
                    
                    # Handle different types of anti-bot detection
                    if detection_type == "cloudflare":
                        # Try Cloudflare-specific bypass
                        await self._handle_cloudflare_challenge()
                        
                    elif detection_type == "captcha":
                        # Try to solve CAPTCHA
                        if self.max_captcha_solve_attempts > 0:
                            solved = await self._solve_captcha(screenshot_b64)
                            if solved:
                                continue
                    
                    elif suggested_action in ["rotate_proxy", "retry"] and attempt < self.max_proxy_retries - 1:
                        # Rotate proxy and fingerprint
                        await self._rotate_proxy_and_fingerprint(site_domain)
                        await asyncio.sleep(random.uniform(5, 15))
                        continue
                    
                    elif suggested_action == "abort":
                        logger.error(f"❌ Aborting due to unresolvable anti-bot: {detection_type}")
                        return False
                    
            except Exception as e:
                logger.error(f"❌ Navigation failed on attempt {attempt + 1}: {e}")
                
                # Try bypass on navigation failure
                if "net::" in str(e) or "timeout" in str(e).lower():
                    parsed_url = urlparse(url)
                    bypass_result = await self.bypass_engine.try_bypass(
                        self, url, parsed_url.path or "/"
                    )
                    
                    if bypass_result and bypass_result.get('success'):
                        logger.info(f"✅ Bypass successful after error! Navigated to: {bypass_result['url']}")
                        return True
                
                await asyncio.sleep(random.uniform(3, 10))
                
        logger.error(f"❌ Failed to navigate to {url} after all retries")
        return False

    async def _rotate_fingerprint(self):
        """Rotate to a new fingerprint profile"""
        logger.info(f"🔄 Rotating fingerprint profile")
        
        # Generate new profile
        self.current_fingerprint_profile = self.fingerprint_evasion.get_random_profile()
        self.fingerprint_rotation_count += 1
        self.last_fingerprint_rotation = time.time()
        
        # Update page with new fingerprint
        fingerprint_script = self.fingerprint_evasion.generate_anti_fingerprintjs_script(
            self.current_fingerprint_profile
        )
        await self.page.add_init_script(fingerprint_script)
        
        # Update viewport
        await self.page.set_viewport_size(self.current_fingerprint_profile["viewport"])
        
        # Update headers
        await self.page.set_extra_http_headers(self.current_fingerprint_profile["headers"])
        
        logger.info(f"✅ Rotated to fingerprint: {self.current_fingerprint_profile['name']}")

    async def _rotate_proxy_and_fingerprint(self, site_domain: str):
        """Rotate both proxy and fingerprint"""
        try:
            # Get new proxy
            new_proxy_info = self.proxy_manager.get_best_proxy(exclude_blocked_for=site_domain)
            if new_proxy_info:
                new_proxy = new_proxy_info.to_playwright_dict()
                logger.info(f"🔄 Rotating to new proxy: {new_proxy['server']}")
                
                # Close current context
                if self.context:
                    await self.context.close()
                
                # Update proxy
                self.proxy = new_proxy
                
                # Re-initialize browser with new proxy and fingerprint
                await self.__aenter__()
                
                logger.info("✅ Browser restarted with new proxy and fingerprint")
            else:
                # Just rotate fingerprint if no proxy available
                await self._rotate_fingerprint()
                
        except Exception as e:
            logger.error(f"❌ Failed to rotate proxy/fingerprint: {e}")

    async def _handle_cloudflare_challenge(self):
        """Handle Cloudflare-specific challenges"""
        logger.info("☁️ Attempting to handle Cloudflare challenge")
        
        try:
            # Wait for challenge to complete
            await asyncio.sleep(random.uniform(5, 10))
            
            # Check if challenge iframe exists
            cf_challenge = await self.page.query_selector('iframe[src*="challenges.cloudflare.com"]')
            if cf_challenge:
                logger.info("🎯 Found Cloudflare challenge iframe")
                
                # Try clicking the checkbox if visible
                checkbox = await self.page.query_selector('input[type="checkbox"]')
                if checkbox:
                    await checkbox.click()
                    await asyncio.sleep(random.uniform(3, 7))
            
            # Wait for redirect
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            
        except Exception as e:
            logger.warning(f"⚠️ Cloudflare challenge handling failed: {e}")

    async def _solve_captcha(self, screenshot_b64: str) -> bool:
        """Attempt to solve CAPTCHA"""
        try:
            result = await self.vision_model.solve_captcha(
                screenshot_b64, 
                self.page.url,
                "unknown"
            )
            
            if result.get("can_solve"):
                logger.info(f"🧩 CAPTCHA solution found: {result.get('solution')}")
                # Implement CAPTCHA solving based on type
                # This would need specific implementation based on CAPTCHA type
                return True
                
        except Exception as e:
            logger.error(f"❌ CAPTCHA solving failed: {e}")
        
        return False

    async def handle_popups(self):
        """Handle various types of popups"""
        try:
            logger.debug("🔍 Checking for popups...")
            
            popup_selectors = [
                '[class*="modal"]', '[class*="popup"]', '[class*="dialog"]',
                '[class*="overlay"]', '[id*="modal"]', '[role="dialog"]',
                '[class*="cookie"]', '[class*="gdpr"]', '[class*="consent"]',
                '[class*="newsletter"]', '[class*="subscribe"]'
            ]
            
            for selector in popup_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            # Look for close button
                            close_selectors = [
                                '[class*="close"]', '[aria-label*="close"]',
                                'button:has-text("×")', 'button:has-text("✕")',
                                'button:has-text("X")', '[title*="close"]',
                                'button:has-text("Accept")', 'button:has-text("OK")',
                                'button:has-text("Got it")', 'button:has-text("Agree")'
                            ]
                            
                            for close_selector in close_selectors:
                                try:
                                    close_btn = await element.query_selector(close_selector)
                                    if close_btn and await close_btn.is_visible():
                                        await close_btn.click()
                                        logger.debug("✅ Closed popup")
                                        await asyncio.sleep(1)
                                        return True
                                except:
                                    continue
                except:
                    continue
            
            # Try pressing Escape
            await self.page.keyboard.press('Escape')
            
        except Exception as e:
            logger.debug(f"⚠️ Popup handling error: {e}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup browser resources"""
        try:
            # Log session statistics
            logger.info(f"📊 Session Statistics:")
            logger.info(f"  - Fingerprint rotations: {self.fingerprint_rotation_count}")
            logger.info(f"  - Successful navigations: {len(self.navigation_history)}")
            logger.info(f"  - Proxy stats: {self.proxy_manager.get_proxy_stats()}")
            
            if self.context:
                await self.context.close()
            if self.play:
                await self.play.stop()
        except Exception as e:
            logger.error(f"❌ Error cleaning up browser: {e}")

    def _generate_sec_ch_ua(self, profile: dict) -> str:
        """Generate realistic Sec-Ch-Ua header"""
        if "Chrome" in profile["user_agent"]:
            version = re.search(r'Chrome/(\d+)', profile["user_agent"])
            if version:
                chrome_version = version.group(1)
                return f'"Not_A Brand";v="8", "Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}"'
        elif "Safari" in profile["user_agent"] and "Chrome" not in profile["user_agent"]:
            return '"Not_A Brand";v="99", "Safari";v="17"'
        elif "Firefox" in profile["user_agent"]:
            return '"Not_A Brand";v="99", "Firefox";v="121"'
        
        return '"Not_A Brand";v="8", "Chromium";v="120"'
    
    async def _restart_browser_with_proxy(self, new_proxy: dict):
        """Restart browser with new proxy"""
        try:
            # Close current context
            if self.context:
                await self.context.close()
            
            # Update proxy
            self.proxy = new_proxy
            
            # Re-initialize browser with new proxy
            await self.__aenter__()
            
            logger.info("✅ Browser restarted with new proxy")
            
        except Exception as e:
            logger.error(f"❌ Failed to restart browser: {e}")
            raise
    
    async def handle_similarweb_popups(self):
        """Handle SimilarWeb popups"""
        try:
            logger.info("🔍 Checking for SimilarWeb popups...")
            await asyncio.sleep(3)
            
            popup_selectors = [
                '[class*="modal"]', '[class*="popup"]', '[class*="dialog"]',
                '[class*="signup"]', '[class*="login"]', '[class*="register"]'
            ]
            
            for selector in popup_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            close_selectors = [
                                '[class*="close"]', '[aria-label*="close"]',
                                'button:has-text("×")', 'button:has-text("✕")'
                            ]
                            
                            for close_selector in close_selectors:
                                try:
                                    close_btn = await element.query_selector(close_selector)
                                    if close_btn and await close_btn.is_visible():
                                        await close_btn.click()
                                        logger.info("✅ Closed popup")
                                        await asyncio.sleep(2)
                                        return True
                                except:
                                    continue
                except:
                    continue
            
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Popup handling failed: {e}")
            return False

    async def extract_similarweb_data_with_vision(self, url: str) -> dict:
        """Extract SimilarWeb data using vision approach"""
        try:
            extractor = SimilarWebExtractor()
            return await extractor.extract_similarweb_data_with_vision(self, url)
        except Exception as e:
            logger.error(f"❌ Vision extraction failed: {e}")
            return {'error': str(e), 'extraction_success': False}

    # Add missing methods from BrowserController
    async def get_page_state(self, include_screenshot: bool = True, highlight_elements: bool = True):
        """Get page state"""
        # Use the same method from your browser_controller.py
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            await asyncio.sleep(1)
            
            url = self.page.url
            title = await self.page.title()
            screenshot = None
            
            if include_screenshot:
                screenshot_bytes = await self.page.screenshot(
                    full_page=False,
                    clip={'x': 0, 'y': 0, 'width': 1250, 'height': 800}
                )
                screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Return a simple PageState-like object
            from browser_controller import PageState
            return PageState(url, title, [], {}, screenshot)
            
        except Exception as e:
            logger.error(f"Failed to get page state: {e}")
            from browser_controller import PageState
            return PageState("", "", [], {}, None)

    async def scroll_page(self, direction: str = "down", amount: int = 500):
        """Scroll the page"""
        if direction == "down":
            await self.page.mouse.wheel(0, amount)
        elif direction == "up":
            await self.page.mouse.wheel(0, -amount)
        await asyncio.sleep(1)
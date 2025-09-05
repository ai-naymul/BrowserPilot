import asyncio
import time
import random
import logging
import re
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from browser_controller import BrowserController
from fingerprint_evasion import AdvancedFingerprintEvasion
from proxy_manager import AdvancedProxyManager, ProxyType
import base64
from typing import Dict
from fingerprint_evasion import DynamicHeaderManager
import time
import asyncio
import random
from urllib.parse import urlparse
logger = logging.getLogger(__name__)

class EnhancedSmartBrowserController(BrowserController):
    """Enhanced browser controller with complete fingerprint evasion - FIXED"""
    
    def __init__(self, headless: bool, proxy: dict | None, enable_streaming: bool = False):
        # Don't call super().__init__() to avoid conflicts
        self.headless = headless
        self.proxy = proxy
        self.enable_streaming = enable_streaming
        
        # Browser objects
        self.play = None
        self.browser = None
        self.page = None
        self.context = None  # ✅ ADD MISSING CONTEXT ATTRIBUTE
        
        # Enhanced components
        self.fingerprint_evasion = AdvancedFingerprintEvasion()
        self.current_fingerprint_profile = None
        
        # Initialize proxy and vision components
        from anti_bot_detection import AntiBotVisionModel
        from proxy_manager import AdvancedProxyManager
        
        self.vision_model = AntiBotVisionModel()
        self.proxy_manager = AdvancedProxyManager(self.vision_model)
        self.current_proxy = proxy
        self.max_proxy_retries = 5
        self.max_captcha_solve_attempts = 3
        self.header_manager = DynamicHeaderManager()
        self.session_state = {
            'visit_count': 0,
            'last_domain': None,
            'session_start': time.time()
        }
    

    async def full_session_reset(self):
        """Complete session reset to prevent fingerprint persistence"""
        try:
            # Clear all storage
            await self.page.evaluate("""
                // Clear all possible storage
                localStorage.clear();
                sessionStorage.clear();
                if ('indexedDB' in window) {
                    const dbs = await indexedDB.databases();
                    dbs.forEach(db => indexedDB.deleteDatabase(db.name));
                }
                // Clear cookies
                document.cookie.split(";").forEach(c => {
                    const eqPos = c.indexOf("=");
                    const name = eqPos > -1 ? c.substr(0, eqPos) : c;
                    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
                });
            """)
            
            # Navigate to blank page to clear state
            await self.page.goto("about:blank")
            await asyncio.sleep(2)
            
            # Reset headers to defaults
            await self.page.set_extra_http_headers({})
            
            logger.info("Full session reset completed")
            
        except Exception as e:
            logger.error(f"Session reset failed: {e}")

    async def _restart_browser_with_proxy(self, new_proxy: dict | None):
        """Enhanced restart with full cleanup"""
        await self.full_session_reset()
        await super()._restart_browser_with_proxy(new_proxy)
        
        # Additional cooling period after restart
        await asyncio.sleep(random.uniform(10, 30))

    async def smart_navigate_with_headers(self, url: str, profile: Dict) -> bool:
        """Navigate with dynamic, contextual headers"""
        parsed_url = urlparse(url)
        current_domain = parsed_url.netloc
        
        # Determine if this is first visit to domain
        is_first_visit = (self.session_state['last_domain'] != current_domain)
        self.session_state['visit_count'] += 1
        
        # Generate contextual headers
        headers = self.header_manager.generate_dynamic_headers(
            profile, url, is_first_visit
        )
        
        # Apply headers before navigation
        await self.page.set_extra_http_headers(headers)
        
        # Log headers for debugging (remove in production)
        logger.debug(f"Headers for {url[:50]}...")
        for key, value in headers.items():
            logger.debug(f"  {key}: {value}")
        
        # Navigate with realistic timing
        if not is_first_visit:
            # Add think time for repeat visits
            think_time = random.uniform(2, 8)
            await asyncio.sleep(think_time)
        
        try:
            response = await self.page.goto(
                url, 
                wait_until='domcontentloaded', 
                timeout=30000
            )
            
            self.session_state['last_domain'] = current_domain
            
            # Simulate human behavior - sometimes scroll or interact
            if random.random() < 0.3:  # 30% chance
                await self._simulate_human_interaction()
            
            return response and response.status < 400
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    async def _simulate_human_interaction(self):
        """Simulate realistic human interaction patterns"""
        # Random scroll
        if random.random() < 0.7:
            scroll_amount = random.randint(100, 800)
            await self.page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(1, 3))
        
        # Random mouse movement (no clicks, just movement)
        if random.random() < 0.4:
            x = random.randint(100, 1000)
            y = random.randint(100, 600) 
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.5, 2))

    async def force_cleanup_with_timeout(self):
        """Enhanced cleanup with timeouts to prevent event loop issues"""
        cleanup_tasks = []
        
        if hasattr(self, 'page') and self.page:
            cleanup_tasks.append(asyncio.create_task(self._safe_close(self.page, 'page')))
        
        if hasattr(self, 'context') and self.context:
            cleanup_tasks.append(asyncio.create_task(self._safe_close(self.context, 'context')))
        
        if hasattr(self, 'browser') and self.browser:
            cleanup_tasks.append(asyncio.create_task(self._safe_close(self.browser, 'browser')))
        
        if hasattr(self, 'play') and self.play:
            cleanup_tasks.append(asyncio.create_task(self._safe_close(self.play, 'playwright', method='stop')))
        
        if cleanup_tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*cleanup_tasks, return_exceptions=True), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Cleanup timeout - forcing termination")

    async def _safe_close(self, obj, name: str, method: str = 'close'):
        """Safely close browser objects with timeout"""
        try:
            close_method = getattr(obj, method)
            await asyncio.wait_for(close_method(), timeout=3.0)
            logger.debug(f"{name} closed successfully")
        except Exception as e:
            logger.error(f"Error closing {name}: {e}")
            
    async def __aenter__(self):
        """Initialize with advanced fingerprint evasion - COMPLETELY FIXED"""
        try:
            # Get random fingerprint profile FIRST
            self.current_fingerprint_profile = self.fingerprint_evasion.get_random_profile()
            logger.info(f"🎭 Using fingerprint profile: {self.current_fingerprint_profile['name']}")
            
            # Initialize Playwright
            self.play = await async_playwright().start()
            
            # ✅ FIXED: Use launch_persistent_context for better stability
            user_data_dir = f"/tmp/stealth-profile-{random.randint(1000, 9999)}"
            
            # Enhanced launch options WITHOUT user-data-dir in args
            launch_options = {
                "headless": self.headless,
                "args": [
                    "--incognito",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    f"--window-size={self.current_fingerprint_profile['viewport']['width']},{self.current_fingerprint_profile['viewport']['height']}",
                    "--window-position=0,0",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--no-first-run",
                    "--disable-default-apps",
                    "--remote-debugging-port=0",
                    # Advanced anti-fingerprinting flags
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                    "--enable-features=NetworkService,NetworkServiceLogging",
                    "--disable-component-extensions-with-background-pages",
                    "--disable-background-networking",
                    "--force-fieldtrials=*BackgroundTracing/default/",
                    "--metrics-recording-only",
                    "--no-report-upload",
                    "--disable-sync",
                    "--disable-features=InterestFeedContentSuggestions",
                    "--disable-dev-tools",
                    "--disable-plugins-discovery"
                ]
            }
            
            # Add proxy to launch options if available
            if self.proxy:
                launch_options["proxy"] = self.proxy
            
            # ✅ FIXED: Use launch_persistent_context instead of launch
            self.context = await self.play.chromium.launch_persistent_context(
                user_data_dir,
                **launch_options,
                # ✅ CORRECT: Set user agent and viewport in context creation
                user_agent=self.current_fingerprint_profile["user_agent"],
                viewport=self.current_fingerprint_profile["viewport"],
                locale=self.current_fingerprint_profile["language"],
                timezone_id=self.current_fingerprint_profile["timezone"],
                permissions=["geolocation", "notifications"],
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": f"{self.current_fingerprint_profile['language']},en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Sec-Ch-Ua": self._generate_sec_ch_ua(self.current_fingerprint_profile),
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": f'"{self.current_fingerprint_profile["platform"]}"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1"
                }
            )
            
            # Get the browser reference from context
            self.browser = self.context.browser
            
            # Create new page from context
            self.page = await self.context.new_page()
            
            # Inject advanced fingerprint evasion script
            fingerprint_script = self.fingerprint_evasion.generate_anti_fingerprintjs_script(
                self.current_fingerprint_profile
            )
            await self.page.add_init_script(fingerprint_script)
            
            logger.info("✅ Enhanced browser initialized successfully")
            return self
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced browser: {e}")
            raise
    

    async def force_cleanup(self):
        """Force cleanup all browser resources"""
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.play:
                await self.play.stop()
            logger.info("🧹 Force cleanup completed")
        except Exception as e:
            logger.error(f"⚠️ Force cleanup error: {e}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup browser resources - COMPLETE"""
        try:
            if hasattr(self, 'page') and self.page:
                await self.page.close()
            if hasattr(self, 'context') and self.context:
                await self.context.close()
            if hasattr(self, 'browser') and self.browser:
                await self.browser.close()
            if hasattr(self, 'play') and self.play:
                await self.play.stop()
            self.page = self.context = self.browser = self.play = None
            try:
                self._initialized = False
            except Exception:
                pass
        except Exception as e:
            logger.error(f"❌ Error cleaning up browser: {e}")


    # async def __aexit__(self, exc_type, exc_val, exc_tb):
    #     """Enhanced cleanup to prevent event loop issues"""
    #     try:
    #         # Stop all running tasks first
    #         if hasattr(self, 'page') and self.page:
    #             try:
    #                 await asyncio.wait_for(self.page.close(), timeout=5.0)
    #             except asyncio.TimeoutError:
    #                 self.logger.warning("Page close timeout")
    #             except Exception as e:
    #                 self.logger.error(f"Page close error: {e}")
            
    #         if hasattr(self, 'context') and self.context:
    #             try:
    #                 await asyncio.wait_for(self.context.close(), timeout=5.0)
    #             except asyncio.TimeoutError:
    #                 self.logger.warning("Context close timeout")
                    
    #         if hasattr(self, 'browser') and self.browser:
    #             try:
    #                 await asyncio.wait_for(self.browser.close(), timeout=5.0)
    #             except asyncio.TimeoutError:
    #                 self.logger.warning("Browser close timeout")
                    
    #         if hasattr(self, 'play') and self.play:
    #             try:
    #                 await asyncio.wait_for(self.play.stop(), timeout=5.0)
    #             except asyncio.TimeoutError:
    #                 self.logger.warning("Playwright stop timeout")
                    
    #         # Force cleanup
    #         import gc
    #         gc.collect()
            
    #     except Exception as e:
    #         self.logger.error(f"Cleanup error: {e}")
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

    # ✅ FIXED: Override smart_navigate to fix coroutine issue
    async def smart_navigate(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000) -> bool:
        """Navigate with proper async handling - FIXED"""
        site_domain = urlparse(url).netloc
        
        for attempt in range(self.max_proxy_retries):
            try:
                logger.info(f"🌐 Enhanced navigation attempt {attempt + 1}/{self.max_proxy_retries}")
                logger.info(f"🎯 Target: {url}")
                logger.info(f"🔄 Proxy: {self.proxy.get('server', 'None') if self.proxy else 'None'}")
                
                start_time = time.time()
                
                # ✅ FIXED: Proper async navigation
                response = await self.page.goto(url, wait_until=wait_until, timeout=timeout)
                response_time = time.time() - start_time
                
                # Wait for page to stabilize
                await asyncio.sleep(random.uniform(3, 6))
                
                # Handle popups
                await self.handle_similarweb_popups()
                
                # Check for anti-bot systems using vision
                screenshot_bytes = await self.page.screenshot(type='png')
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                # ✅ FIXED: Await the async method properly
                is_antibot, detection_type, suggested_action = await self.proxy_manager.detect_anti_bot_with_vision(
                    self.page, f"navigate to {url}"
                )
                
                if not is_antibot:
                    # Success!
                    logger.info(f"✅ Successfully navigated to: {url}")
                    if self.proxy:
                        proxy_info = next((p for p in self.proxy_manager.proxies 
                                         if p.to_playwright_dict().get('server') == self.proxy.get('server')), None)
                        if proxy_info:
                            self.proxy_manager.mark_proxy_success(proxy_info, response_time)
                    return True
                else:
                    logger.warning(f"🚫 Anti-bot detected: {detection_type}, action: {suggested_action}")
                    
                    # Handle different types of anti-bot detection
                    if suggested_action in ["rotate_proxy", "retry"] and attempt < self.max_proxy_retries - 1:
                        # Get new proxy and restart
                        new_proxy_info = self.proxy_manager.get_best_proxy(exclude_blocked_for=site_domain)
                        if new_proxy_info:
                            new_proxy = new_proxy_info.to_playwright_dict()
                            logger.info(f"🔄 Rotating to new proxy: {new_proxy['server']}")
                            await self._restart_browser_with_proxy(new_proxy)
                            await asyncio.sleep(random.uniform(5, 15))
                            continue
                    
                    elif suggested_action == "abort":
                        logger.error(f"❌ Aborting due to unresolvable anti-bot: {detection_type}")
                        return False
                    
            except Exception as e:
                logger.error(f"❌ Navigation failed on attempt {attempt + 1}: {e}")
                await asyncio.sleep(random.uniform(3, 10))
                
        logger.error(f"❌ Failed to navigate to {url} after all retries")
        return False

    async def _restart_browser_with_proxy(self, new_proxy: dict | None):
        """
        Fully tear down the current Playwright stack and rebuild with `new_proxy`.

        Works with SingleBrowserController as well (which uses an `_initialized`
        guard to prevent double init). We explicitly reset that guard here so the
        next __aenter__ actually re-creates the browser/context/page.
        """
        try:
            logger.info("🔄 Closing previous browser before restart...")

            # Best-effort close of page/context/browser (ignore close errors)
            for name in ("page", "context", "browser"):
                obj = getattr(self, name, None)
                if obj:
                    try:
                        await obj.close()
                    except Exception as e:
                        logger.debug(f"⚠️ Error closing {name}: {e}")
                    finally:
                        setattr(self, name, None)

            # Stop Playwright itself
            if getattr(self, "play", None):
                try:
                    await self.play.stop()
                except Exception as e:
                    logger.debug(f"⚠️ Error stopping Playwright: {e}")
                finally:
                    self.play = None

            # Give OS a moment to release ports/files
            await asyncio.sleep(random.uniform(0.5, 1.5))

            # Update proxy BEFORE re-enter so __aenter__ picks it up
            self.proxy = new_proxy

            # Clear init guard so __aenter__ will actually rebuild everything
            try:
                self._initialized = False
            except Exception:
                pass

            # Re-initialize (your __aenter__ handles fingerprint, context, page, etc.)
            await self.__aenter__()

            logger.info("✅ Browser restarted with new proxy")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to restart browser: {e}")
            return False

    # Add all other required methods...
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
            # from similarweb_extractor import SimilarWebExtractor
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

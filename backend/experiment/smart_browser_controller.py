## used to manage browser navigation with intelligent anti-bot detection and proxy rotation

import asyncio
import time
from urllib.parse import urlparse
from browser_controller import BrowserController
from proxy_manager import SmartProxyManager
from anti_bot_detection import AntiBotVisionModel
import logging
import base64
from playwright.async_api import async_playwright
from fingerprint_evasion import AdvancedFingerprintEvasion
import random
import re
from typing import Dict
logger = logging.getLogger(__name__)

class SmartBrowserController(BrowserController):
    def __init__(self, headless: bool, proxy: dict | None, enable_streaming: bool = False):
        super().__init__(headless, proxy, enable_streaming)
        
        # Initialize smart proxy management
        self.vision_model = AntiBotVisionModel()
        self.proxy_manager = SmartProxyManager(self.vision_model)
        self.current_proxy = proxy
        self.max_proxy_retries = 5
        self.proxy_retry_count = 0
        self.max_captcha_solve_attempts = 3
        self.captcha_solve_count = 0
        self.fingerprint_evasion = AdvancedFingerprintEvasion()
        self.current_fingerprint_profile = None
    
    async def smart_navigate(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000) -> bool:
        """Navigate with intelligent anti-bot detection and proxy rotation"""
        site_domain = urlparse(url).netloc
        
        for attempt in range(self.max_proxy_retries):
            try:
                logger.info(f"🌐 Smart navigation attempt {attempt + 1}/{self.max_proxy_retries} to: {url}")
                start_time = time.time()
                
                # Navigate to the page
                response = await self.page.goto(url, wait_until=wait_until, timeout=timeout)
                response_time = time.time() - start_time
                
                # Wait a moment for page to fully load
                await asyncio.sleep(random.uniform(3, 7))
                # Check for fingerprinting attempts
                screenshot_bytes = await self.page.screenshot(type='png')
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                fingerprint_result = await self.vision_model.detect_fingerprintjs_challenge(
                    screenshot_b64, url
                )
                
                if fingerprint_result.get("fingerprinting_detected", False):
                    fingerprint_type = fingerprint_result.get("fingerprint_type", "unknown")
                    recommended_action = fingerprint_result.get("recommended_action", "wait")
                    
                    logger.warning(f"🔍 Fingerprinting detected: {fingerprint_type}")
                    logger.info(f"🎯 Recommended action: {recommended_action}")
                    
                    if recommended_action == "regenerate_fingerprint":
                        await self.regenerate_fingerprint()
                        await asyncio.sleep(random.uniform(5, 10))
                        continue
                    elif recommended_action == "wait":
                        # Wait for fingerprinting to complete
                        logger.info("⏳ Waiting for fingerprinting to complete...")
                        await asyncio.sleep(random.uniform(10, 20))
                    elif recommended_action == "rotate_proxy":
                        # Force proxy rotation
                        if self.current_proxy:
                            proxy_info = next((p for p in self.proxy_manager.proxies if p.to_playwright_dict() == self.current_proxy), None)
                            if proxy_info:
                                self.proxy_manager.mark_proxy_failure(proxy_info, site_domain, "fingerprinting")
                        
                        if attempt < self.max_proxy_retries - 1:
                            new_proxy_info = self.proxy_manager.get_best_proxy(exclude_blocked_for=site_domain)
                            if new_proxy_info:
                                new_proxy = new_proxy_info.to_playwright_dict()
                                logger.info(f"🔄 Rotating proxy due to fingerprinting")
                                await self._restart_browser_with_proxy(new_proxy)
                                await asyncio.sleep(random.uniform(5, 15))
                                continue
                
                # Regular anti-bot detection
                is_antibot, detection_type, suggested_action = await self.proxy_manager.detect_anti_bot_with_vision(
                    self.page, f"navigate to {url}"
                )
                
                if not is_antibot and fingerprint_result.get("page_loading_normally", True):
                    # Success!
                    response_time = time.time() - start_time
                    logger.info(f"✅ Successfully navigated to: {url}")
                    
                    if self.current_proxy:
                        proxy_info = next((p for p in self.proxy_manager.proxies if p.to_playwright_dict() == self.current_proxy), None)
                        if proxy_info:
                            self.proxy_manager.mark_proxy_success(proxy_info, response_time)
                    
                    return True
                
                if is_antibot:
                    logger.warning(f"🚫 Anti-bot detected: {detection_type}, suggested action: {suggested_action}")
                    
                    # Handle based on suggested action
                    if suggested_action == "solve_captcha" and self.captcha_solve_count < self.max_captcha_solve_attempts:
                        success = await self._attempt_captcha_solve(url, detection_type)
                        if success:
                            logger.info("✅ CAPTCHA solved successfully!")
                            if self.current_proxy:
                                proxy_info = next((p for p in self.proxy_manager.proxies if p.to_playwright_dict() == self.current_proxy), None)
                                if proxy_info:
                                    self.proxy_manager.mark_proxy_success(proxy_info, response_time)
                            return True
                        else:
                            self.captcha_solve_count += 1
                    
                    if suggested_action in ["rotate_proxy", "retry"] or self.captcha_solve_count >= self.max_captcha_solve_attempts:
                        # Mark current proxy as failed
                        if self.current_proxy:
                            proxy_info = next((p for p in self.proxy_manager.proxies if p.to_playwright_dict() == self.current_proxy), None)
                            if proxy_info:
                                self.proxy_manager.mark_proxy_failure(proxy_info, site_domain, detection_type)
                        
                        # Try with new proxy
                        if attempt < self.max_proxy_retries - 1:
                            new_proxy_info = self.proxy_manager.get_best_proxy(exclude_blocked_for=site_domain)
                            if new_proxy_info:
                                new_proxy = new_proxy_info.to_playwright_dict()
                                logger.info(f"🔄 Rotating to new proxy: {new_proxy['server']}")
                                await self._restart_browser_with_proxy(new_proxy)
                                await asyncio.sleep(3)  # Wait before retry
                                continue
                            else:
                                logger.error("❌ No available proxies for rotation")
                                return False
                    
                    if suggested_action == "abort":
                        logger.error(f"❌ Aborting navigation due to unresolvable anti-bot: {detection_type}")
                        return False
                        
                else:
                    # Success! No anti-bot detected
                    logger.info(f"✅ Successfully navigated to: {url}")
                    if self.current_proxy:
                        proxy_info = next((p for p in self.proxy_manager.proxies if p.to_playwright_dict() == self.current_proxy), None)
                        if proxy_info:
                            self.proxy_manager.mark_proxy_success(proxy_info, response_time)
                    self.proxy_retry_count = 0
                    self.captcha_solve_count = 0
                    return True
                    
            except Exception as e:
                logger.error(f"❌ Navigation failed on attempt {attempt + 1}: {e}")
                
                # Mark proxy failure and try another
                if self.current_proxy:
                    proxy_info = next((p for p in self.proxy_manager.proxies if p.to_playwright_dict() == self.current_proxy), None)
                    if proxy_info:
                        self.proxy_manager.mark_proxy_failure(proxy_info, site_domain, "connection_error")
                
                if attempt < self.max_proxy_retries - 1:
                    new_proxy_info = self.proxy_manager.get_best_proxy(exclude_blocked_for=site_domain)
                    if new_proxy_info:
                        new_proxy = new_proxy_info.to_playwright_dict()
                        logger.info(f"🔄 Retrying with new proxy due to connection error")
                        await self._restart_browser_with_proxy(new_proxy)
                        await asyncio.sleep(3)
                        continue
        
        logger.error(f"❌ Failed to navigate to {url} after all retries")
        return False
    
    async def _attempt_captcha_solve(self, url: str, detection_type: str) -> bool:
        """Attempt to solve CAPTCHA using vision model"""
        try:
            logger.info(f"🧩 Attempting to solve {detection_type} CAPTCHA...")
            
            # Take screenshot for CAPTCHA analysis
            screenshot_bytes = await self.page.screenshot(type='png')
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Use vision model to solve CAPTCHA
            solution = await self.vision_model.solve_captcha(screenshot_b64, url, detection_type)
            
            if solution.get("can_solve", False) and solution.get("confidence", 0) > 0.7:
                logger.info(f"🎯 CAPTCHA solution found: {solution.get('solution', 'N/A')}")
                
                # Implement CAPTCHA solving logic based on solution type
                success = await self._apply_captcha_solution(solution)
                return success
            else:
                logger.warning(f"❌ Could not solve CAPTCHA: {solution.get('instructions', 'Unknown reason')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error attempting CAPTCHA solve: {e}")
            return False
    
    async def _apply_captcha_solution(self, solution: dict) -> bool:
        """Apply the CAPTCHA solution to the page"""
        try:
            solution_type = solution.get("solution_type", "unknown")
            solution_value = solution.get("solution", "")
            
            if solution_type == "text":
                # Find text input and enter solution
                text_inputs = await self.page.query_selector_all('input[type="text"], input:not([type])')
                for input_elem in text_inputs:
                    if await input_elem.is_visible():
                        await input_elem.fill(solution_value)
                        await asyncio.sleep(1)
                        
                        # Look for submit button
                        submit_buttons = await self.page.query_selector_all('button, input[type="submit"]')
                        for button in submit_buttons:
                            if await button.is_visible():
                                await button.click()
                                await asyncio.sleep(3)
                                return True
            
            elif solution_type == "selection":
                # Handle image selection CAPTCHAs
                logger.warning("🚧 Image selection CAPTCHA solving not fully implemented")
                return False
            
            elif solution_type == "math":
                # Similar to text but specifically for math solutions
                text_inputs = await self.page.query_selector_all('input[type="text"], input:not([type])')
                for input_elem in text_inputs:
                    if await input_elem.is_visible():
                        await input_elem.fill(str(solution_value))
                        await asyncio.sleep(1)
                        
                        submit_buttons = await self.page.query_selector_all('button, input[type="submit"]')
                        for button in submit_buttons:
                            if await button.is_visible():
                                await button.click()
                                await asyncio.sleep(3)
                                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error applying CAPTCHA solution: {e}")
            return False
    
    async def _restart_browser_with_proxy(self, new_proxy: dict):
        """Restart browser with new proxy"""
        try:
            # Close current browser
            if self.browser:
                await self.browser.close()
            
            # Update proxy
            self.current_proxy = new_proxy
            
            # Launch new browser with new proxy
            launch_options = {
                "headless": self.headless,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--window-size=1280,800",
                    "--window-position=0,0",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--no-first-run",
                    "--disable-default-apps",
                    "--remote-debugging-port=0"
                ]
            }
            
            if new_proxy:
                launch_options["proxy"] = new_proxy
            
            self.browser = await self.play.chromium.launch(**launch_options)
            self.page = await self.browser.new_page(viewport={"width": 1280, "height": 800})
            
            # Re-setup CDP streaming if enabled
            if self.enable_streaming:
                await self._setup_cdp_streaming()
            
            # Set headers with randomization
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            logger.info("✅ Browser restarted with new proxy")
            
        except Exception as e:
            logger.error(f"❌ Failed to restart browser with new proxy: {e}")
            raise
    
    def get_proxy_stats(self) -> dict:
        """Get current proxy statistics"""
        stats = self.proxy_manager.get_proxy_stats()
        stats.update({
            "current_proxy": self.current_proxy.get("server", "None") if self.current_proxy else "None",
            "retry_count": self.proxy_retry_count,
            "captcha_solve_count": self.captcha_solve_count
        })
        return stats
    
    # Override the goto method to use smart navigation
    async def goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000):
        """Navigate to a URL with smart anti-bot detection"""
        success = await self.smart_navigate(url, wait_until, timeout)
        if not success:
            raise Exception(f"Failed to navigate to {url} after intelligent retry attempts")
    
    async def __aenter__(self):
        """Initialize browser with incognito mode and advanced fingerprint evasion"""
        self.play = await async_playwright().start()
        
        # Get random fingerprint profile
        self.current_fingerprint_profile = self.fingerprint_evasion.get_random_profile()
        logger.info(f"🎭 Using fingerprint profile: {self.current_fingerprint_profile['name']}")
        
        # Enhanced launch options with incognito mode and fingerprint-specific settings
        launch_options = {
            "headless": self.headless,
            "args": [
                "--incognito",  # ✅ INCOGNITO MODE ADDED
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
                "--disable-plugins-discovery",
                # f"--user-data-dir=/tmp/stealth-profile-{random.randint(1000, 9999)}"
            ]
        }
        
        if self.proxy:
            launch_options["proxy"] = self.proxy
            
        self.browser = await self.play.chromium.launch(**launch_options)
        
        # Create context with fingerprint-specific settings
        context_options = {
            "viewport": self.current_fingerprint_profile["viewport"],
            "user_agent": self.current_fingerprint_profile["user_agent"],
            "locale": self.current_fingerprint_profile["language"],
            "timezone_id": self.current_fingerprint_profile["timezone"],
            "permissions": ["geolocation", "notifications"],
            "extra_http_headers": {
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
        }
        
        if self.proxy:
            context_options["proxy"] = self.proxy
            
        context = await self.browser.new_context(**context_options)
        self.page = await context.new_page()
        
        # Inject advanced fingerprint evasion script
        fingerprint_script = self.fingerprint_evasion.generate_anti_fingerprintjs_script(
            self.current_fingerprint_profile
        )
        await self.page.add_init_script(fingerprint_script)
        
        # Set up CDP streaming if enabled
        if self.enable_streaming:
            await self._setup_cdp_streaming()
        
        return self
    
    # Add these new methods to your SmartBrowserController class:
    def _generate_sec_ch_ua(self, profile: Dict) -> str:
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
    
    async def regenerate_fingerprint(self):
        """Regenerate fingerprint mid-session if needed"""
        logger.info("🔄 Regenerating browser fingerprint...")
        
        # Get new profile
        self.current_fingerprint_profile = self.fingerprint_evasion.get_random_profile()
        
        # Update context with new fingerprint
        new_script = self.fingerprint_evasion.generate_anti_fingerprintjs_script(
            self.current_fingerprint_profile
        )
        
        await self.page.evaluate(new_script)
        logger.info(f"✅ Fingerprint regenerated: {self.current_fingerprint_profile['name']}")
    
    async def handle_similarweb_popups(self) -> bool:
        """Handle SimilarWeb account creation and login popups"""
        try:
            logger.info("🔍 Checking for SimilarWeb popups and modals...")
            
            # Wait a moment for any popups to appear
            await asyncio.sleep(3)
            
            # Check for various popup types
            popup_selectors = [
                # Login/signup modals
                '[class*="modal"]', '[class*="popup"]', '[class*="dialog"]',
                '[class*="overlay"]', '[id*="modal"]', '[id*="popup"]',
                # SimilarWeb specific
                '[class*="signup"]', '[class*="login"]', '[class*="register"]',
                '[class*="account"]', '[class*="trial"]', '[class*="premium"]'
            ]
            
            popup_found = False
            for selector in popup_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            # Try to find and click close button
                            close_selectors = [
                                '[class*="close"]', '[class*="dismiss"]', '[aria-label*="close"]',
                                '[aria-label*="Close"]', 'button[title*="close"]', 'button[title*="Close"]',
                                '.close', 'button:has-text("×")', 'button:has-text("✕")'
                            ]
                            
                            for close_selector in close_selectors:
                                try:
                                    close_btn = await element.query_selector(close_selector)
                                    if close_btn and await close_btn.is_visible():
                                        await close_btn.click()
                                        popup_found = True
                                        logger.info("✅ Closed popup using close button")
                                        await asyncio.sleep(2)
                                        break
                                except:
                                    continue
                            
                            # Try pressing Escape key as fallback
                            if popup_found:
                                await self.page.keyboard.press('Escape')
                                await asyncio.sleep(1)
                                
                            break
                except:
                    continue
            
            # Check for and handle "Continue with Google" or similar buttons
            try:
                continue_buttons = await self.page.query_selector_all('button, a')
                for button in continue_buttons:
                    if await button.is_visible():
                        text = await button.inner_text()
                        if any(phrase in text.lower() for phrase in ['continue without', 'skip', 'no thanks', 'maybe later']):
                            await button.click()
                            logger.info(f"✅ Clicked skip button: {text[:30]}")
                            await asyncio.sleep(2)
                            break
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Popup handling failed: {e}")
            return False

    async def extract_similarweb_data_with_vision(self, url: str) -> dict:
        """Extract SimilarWeb data using pure vision-based approach"""
        try:
            from similarweb_extractor import SimilarWebExtractor
            extractor = SimilarWebExtractor()
            return await extractor.extract_similarweb_data_with_vision(self, url)
        except Exception as e:
            logger.error(f"❌ Vision-based SimilarWeb extraction failed: {e}")
            return {'error': str(e), 'extraction_success': False}

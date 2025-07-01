## used to manage browser navigation with intelligent anti-bot detection and proxy rotation

import asyncio
import time
from urllib.parse import urlparse
from backend.browser_controller import BrowserController
from backend.proxy_manager import SmartProxyManager
from backend.anti_bot_detection import AntiBotVisionModel
import logging
import base64
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
                await asyncio.sleep(2)
                
                # Use vision model to detect anti-bot systems
                is_antibot, detection_type, suggested_action = await self.proxy_manager.detect_anti_bot_with_vision(
                    self.page, f"navigate to {url}"
                )
                
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

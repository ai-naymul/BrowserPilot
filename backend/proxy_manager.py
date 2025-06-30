import os, json, random, time, asyncio, logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import base64

logger = logging.getLogger(__name__)

class ProxyHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    FAILED = "failed"

@dataclass
class ProxyInfo:
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    location: str = "unknown"
    health: ProxyHealth = ProxyHealth.HEALTHY
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0
    blocked_sites: set = None
    response_time: float = 0
    consecutive_failures: int = 0
    
    def __post_init__(self):
        if self.blocked_sites is None:
            self.blocked_sites = set()
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0
    
    def to_playwright_dict(self) -> Dict:
        proxy_dict = {"server": self.server}
        if self.username:
            proxy_dict["username"] = self.username
        if self.password:
            proxy_dict["password"] = self.password
        return proxy_dict

class SmartProxyManager:
    def __init__(self, vision_model=None):
        self.proxies: List[ProxyInfo] = []
        self.current_proxy_index = 0
        self.vision_model = vision_model
        self.max_proxy_retries = 5
        self.max_consecutive_failures = 3
        
        self._load_proxies()
    
    def _load_proxies(self):
        """Load proxies from environment or config"""
        source = os.getenv("SCRAPER_PROXIES", "[]")
        proxy_data = json.loads(source)
        
        for proxy in proxy_data:
            if isinstance(proxy, str):
                self.proxies.append(ProxyInfo(server=proxy))
            elif isinstance(proxy, dict):
                self.proxies.append(ProxyInfo(
                    server=proxy.get("server", ""),
                    username=proxy.get("username"),
                    password=proxy.get("password"),
                    location=proxy.get("location", "unknown")
                ))
        
        logger.info(f"Loaded {len(self.proxies)} proxies for smart rotation")
    
    def get_best_proxy(self, exclude_blocked_for: str = None) -> Optional[ProxyInfo]:
        """Get the best available proxy based on performance metrics"""
        if not self.proxies:
            return None
        
        # Filter out failed and heavily blocked proxies
        available_proxies = [
            p for p in self.proxies 
            if p.health != ProxyHealth.FAILED and 
            p.consecutive_failures < self.max_consecutive_failures and
            (not exclude_blocked_for or exclude_blocked_for not in p.blocked_sites)
        ]
        
        if not available_proxies:
            # Reset consecutive failures and try again
            for proxy in self.proxies:
                proxy.consecutive_failures = 0
            available_proxies = [p for p in self.proxies if p.health != ProxyHealth.FAILED]
        
        if not available_proxies:
            logger.error("No available proxies found!")
            return None
        
        # Sort by success rate and response time
        sorted_proxies = sorted(
            available_proxies,
            key=lambda p: (p.success_rate, -p.response_time, -p.last_used),
            reverse=True
        )
        
        return sorted_proxies[0]
    
    async def detect_anti_bot_with_vision(self, page, goal: str) -> Tuple[bool, str, Optional[str]]:
        """Use vision model to detect anti-bot systems"""
        if not self.vision_model:
            return False, "", None
        
        try:
            # Take screenshot for vision analysis
            screenshot_bytes = await page.screenshot(type='png')
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Get page content for context
            page_title = await page.title()
            page_url = page.url
            
            # Create anti-bot detection prompt
            detection_prompt = f"""
            ANTI-BOT DETECTION TASK:
            
            You are analyzing a webpage screenshot to detect if we've encountered an anti-bot system, CAPTCHA, or access restriction.
            
            Current URL: {page_url}
            Page Title: {page_title}
            Original Goal: {goal}
            
            Look for these indicators:
            1. **Cloudflare protection pages** - "Checking your browser", "Please wait", security checks
            2. **CAPTCHA challenges** - Image puzzles, reCAPTCHA, hCaptcha, text verification
            3. **Access denied pages** - "Access Denied", "Blocked", "Rate Limited"
            4. **Bot detection warnings** - "Automated traffic detected", "Unusual activity"
            5. **Verification pages** - Phone verification, email verification, identity checks
            6. **Error pages** - 403 Forbidden, 429 Rate Limited, 503 Service Unavailable
            7. **Loading/waiting pages** - Indefinite loading, "Please wait while we verify"
            
            Respond with JSON:
            {{
                "is_anti_bot": true/false,
                "detection_type": "cloudflare|captcha|access_denied|rate_limit|verification|error|none",
                "confidence": 0.0-1.0,
                "description": "Brief description of what you see",
                "can_solve": true/false,
                "suggested_action": "rotate_proxy|solve_captcha|wait|retry|abort"
            }}
            """
            
            # Use vision model to analyze
            result = await self.vision_model.analyze_anti_bot_page(
                screenshot_b64, detection_prompt, page_url
            )
            
            if result.get("is_anti_bot", False):
                detection_type = result.get("detection_type", "unknown")
                suggested_action = result.get("suggested_action", "rotate_proxy")
                description = result.get("description", "Anti-bot system detected")
                
                logger.warning(f"🚫 Anti-bot detected: {detection_type} - {description}")
                return True, detection_type, suggested_action
            
            return False, "", None
            
        except Exception as e:
            logger.error(f"Error in vision-based anti-bot detection: {e}")
            return False, "", None
    
    def mark_proxy_success(self, proxy: ProxyInfo, response_time: float = 0):
        """Mark proxy as successful"""
        proxy.success_count += 1
        proxy.consecutive_failures = 0
        proxy.last_used = time.time()
        proxy.response_time = response_time
        proxy.health = ProxyHealth.HEALTHY
        logger.debug(f"✅ Proxy {proxy.server} marked successful")
    
    def mark_proxy_failure(self, proxy: ProxyInfo, site_url: str = None, detection_type: str = None):
        """Mark proxy as failed"""
        proxy.failure_count += 1
        proxy.consecutive_failures += 1
        
        if detection_type in ["cloudflare", "rate_limit"]:
            proxy.blocked_sites.add(site_url)
            proxy.health = ProxyHealth.BLOCKED
            logger.warning(f"🚫 Proxy {proxy.server} blocked by {detection_type} for {site_url}")
        else:
            proxy.health = ProxyHealth.DEGRADED
        
        # Mark as completely failed if too many consecutive failures
        if proxy.consecutive_failures >= self.max_consecutive_failures:
            proxy.health = ProxyHealth.FAILED
            logger.error(f"❌ Proxy {proxy.server} marked as failed after {proxy.consecutive_failures} consecutive failures")
    
    def get_proxy_stats(self) -> Dict:
        """Get comprehensive proxy statistics"""
        if not self.proxies:
            return {"total": 0, "healthy": 0, "blocked": 0, "failed": 0, "available": 0}
        
        stats = {
            "total": len(self.proxies),
            "healthy": len([p for p in self.proxies if p.health == ProxyHealth.HEALTHY]),
            "degraded": len([p for p in self.proxies if p.health == ProxyHealth.DEGRADED]),
            "blocked": len([p for p in self.proxies if p.health == ProxyHealth.BLOCKED]),
            "failed": len([p for p in self.proxies if p.health == ProxyHealth.FAILED]),
            "available": len([p for p in self.proxies if p.health != ProxyHealth.FAILED and p.consecutive_failures < self.max_consecutive_failures])
        }
        return stats

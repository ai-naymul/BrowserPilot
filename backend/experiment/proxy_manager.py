import os
import json
import random
import time
import asyncio
import logging
import requests
import urllib.request
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import base64

logger = logging.getLogger(__name__)

class ProxyType(Enum):
    RESIDENTIAL = "residential"
    MOBILE = "mobile"
    DATACENTER = "datacenter"

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
    proxy_type: ProxyType = ProxyType.RESIDENTIAL
    location: str = "unknown"
    health: ProxyHealth = ProxyHealth.HEALTHY
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0
    blocked_sites: set = field(default_factory=set)
    response_time: float = 0
    consecutive_failures: int = 0
    timeout_failures: int = 0
    redirect_failures: int = 0
    
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

class AdvancedProxyManager:
    def __init__(self, vision_model=None):
        self.proxies: List[ProxyInfo] = []
        self.residential_proxies: List[ProxyInfo] = []
        self.mobile_proxies: List[ProxyInfo] = []
        self.current_proxy_index = 0
        self.vision_model = vision_model
        self.max_proxy_retries = 5
        self.max_consecutive_failures = 3
        self.timeout_threshold = 50  # 50 seconds
        
        # Load all proxy types
        self._load_webshare_residential_proxies()
        self._load_oxylabs_mobile_proxies()
        self._organize_proxies()

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
        
    def _load_webshare_residential_proxies(self):
        """Load Webshare residential proxies"""
        try:
            # Method 1: From environment variable
            webshare_config = os.getenv("WEBSHARE_PROXY_CONFIG")
            if webshare_config:
                config = json.loads(webshare_config)
                proxy_info = ProxyInfo(
                    server="http://p.webshare.io:80",
                    username=config["username"],
                    password=config["password"],
                    proxy_type=ProxyType.RESIDENTIAL,
                    location="rotating"
                )
                self.residential_proxies.append(proxy_info)
                logger.info("✅ Loaded Webshare rotating proxy from environment")
                return
            
            # Method 2: From your provided format
            webshare_username = "npgyhuvj-rotate"
            webshare_password = "hxwwky71phsg"
            
            proxy_info = ProxyInfo(
                server="http://p.webshare.io:80",
                username=webshare_username,
                password=webshare_password,
                proxy_type=ProxyType.RESIDENTIAL,
                location="rotating_residential"
            )
            self.residential_proxies.append(proxy_info)
            
            # Method 3: Load from Webshare proxy file if exists
            proxy_files = ["Webshare-10-proxies.txt", "webshare_proxies.txt"]
            for proxy_file in proxy_files:
                if os.path.exists(proxy_file):
                    with open(proxy_file, "r") as f:
                        for line in f:
                            if line.strip():
                                parts = line.strip().split(':')
                                if len(parts) >= 4:
                                    ip, port, username, password = parts[:4]
                                    proxy_info = ProxyInfo(
                                        server=f"http://{ip}:{port}",
                                        username=username,
                                        password=password,
                                        proxy_type=ProxyType.RESIDENTIAL,
                                        location="webshare_static"
                                    )
                                    self.residential_proxies.append(proxy_info)
                    break
            
            logger.info(f"✅ Loaded {len(self.residential_proxies)} Webshare residential proxies")
            
        except Exception as e:
            logger.error(f"❌ Error loading Webshare proxies: {e}")

    def _load_oxylabs_mobile_proxies(self):
        """Load Oxylabs mobile proxies"""
        try:
            # Method 1: From environment variable
            oxylabs_config = os.getenv("OXYLABS_PROXY_CONFIG")
            if oxylabs_config:
                config = json.loads(oxylabs_config)
                for proxy_config in config:
                    proxy_info = ProxyInfo(
                        server=proxy_config["server"],
                        username=proxy_config["username"], 
                        password=proxy_config["password"],
                        proxy_type=ProxyType.MOBILE,
                        location=proxy_config.get("location", "mobile")
                    )
                    self.mobile_proxies.append(proxy_info)
                logger.info(f"✅ Loaded {len(self.mobile_proxies)} Oxylabs mobile proxies from environment")
                return
            
            # Method 2: Default Oxylabs mobile proxy setup
            oxylabs_username = os.getenv("OXYLABS_USERNAME", "perspectivity_Jy142")
            oxylabs_password = os.getenv("OXYLABS_PASSWORD", "5Q1=HlWWpnYueGq")
            
            # Add mobile proxy endpoints
            mobile_endpoints = [
                "pr.oxylabs.io:7777",  # Residential (can be used as mobile-like)
                "unblock.oxylabs.io:60000"  # Web Unblocker
            ]
            
            for endpoint in mobile_endpoints:
                proxy_info = ProxyInfo(
                    server=f"http://{endpoint}",
                    username=f"customer-{oxylabs_username}",
                    password=oxylabs_password,
                    proxy_type=ProxyType.MOBILE,
                    location="oxylabs_mobile"
                )
                self.mobile_proxies.append(proxy_info)
            
            logger.info(f"✅ Loaded {len(self.mobile_proxies)} Oxylabs mobile proxies")
            
        except Exception as e:
            logger.error(f"❌ Error loading Oxylabs proxies: {e}")

    def _organize_proxies(self):
        """Organize all proxies by priority"""
        # Combine all proxies with residential first, then mobile
        self.proxies = self.residential_proxies + self.mobile_proxies
        
        # Shuffle within each type for randomization
        random.shuffle(self.residential_proxies)
        random.shuffle(self.mobile_proxies)
        
        logger.info(f"📊 Proxy Summary:")
        logger.info(f"   Residential: {len(self.residential_proxies)}")
        logger.info(f"   Mobile: {len(self.mobile_proxies)}")
        logger.info(f"   Total: {len(self.proxies)}")

    def get_best_proxy(self, prefer_type: ProxyType = ProxyType.RESIDENTIAL, exclude_blocked_for: str = None) -> Optional[ProxyInfo]:
        """Get best proxy with intelligent selection"""
        
        # First try preferred type (residential)
        preferred_proxies = [p for p in self.proxies if p.proxy_type == prefer_type]
        available_preferred = [
            p for p in preferred_proxies
            if p.health != ProxyHealth.FAILED and 
               p.consecutive_failures < self.max_consecutive_failures and
               (not exclude_blocked_for or exclude_blocked_for not in p.blocked_sites)
        ]
        
        if available_preferred:
            # Sort by performance metrics
            sorted_proxies = sorted(
                available_preferred,
                key=lambda p: (
                    p.success_rate,
                    -p.response_time,
                    -p.timeout_failures,
                    -p.redirect_failures,
                    -p.last_used
                ),
                reverse=True
            )
            logger.info(f"🎯 Selected {prefer_type.value} proxy: {sorted_proxies[0].server}")
            return sorted_proxies[0]
        
        # Fallback to other types
        other_type = ProxyType.MOBILE if prefer_type == ProxyType.RESIDENTIAL else ProxyType.RESIDENTIAL
        other_proxies = [p for p in self.proxies if p.proxy_type == other_type]
        available_other = [
            p for p in other_proxies
            if p.health != ProxyHealth.FAILED and 
               p.consecutive_failures < self.max_consecutive_failures and
               (not exclude_blocked_for or exclude_blocked_for not in p.blocked_sites)
        ]
        
        if available_other:
            sorted_other = sorted(
                available_other,
                key=lambda p: (p.success_rate, -p.response_time, -p.last_used),
                reverse=True
            )
            logger.info(f"🔄 Fallback to {other_type.value} proxy: {sorted_other[0].server}")
            return sorted_other[0]
        
        # Last resort: reset failures and try again
        logger.warning("⚠️ No healthy proxies available, resetting failure counters")
        for proxy in self.proxies:
            if proxy.consecutive_failures > 0:
                proxy.consecutive_failures = max(0, proxy.consecutive_failures - 1)
                proxy.health = ProxyHealth.DEGRADED
        
        # Try again after reset
        available_reset = [p for p in self.proxies if p.health != ProxyHealth.FAILED]
        if available_reset:
            return available_reset[0]
        
        logger.error("❌ No proxies available at all!")
        return None

    async def detect_proxy_issues(self, page, proxy_info: ProxyInfo, start_time: float, url: str) -> Tuple[bool, str, str]:
        """Detect various proxy-related issues"""
        current_time = time.time()
        elapsed_time = current_time - start_time
        current_url = page.url
        
        # Check for timeout
        if elapsed_time > self.timeout_threshold:
            logger.warning(f"⏰ Timeout detected: {elapsed_time:.1f}s > {self.timeout_threshold}s")
            return True, "timeout", "rotate_proxy"
        
        # Check for unwanted redirects
        if "similarweb.com/website/" in current_url and url != current_url:
            logger.warning(f"🔄 Unwanted redirect detected: {current_url}")
            return True, "redirect", "rotate_proxy"
        
        # Use vision model for anti-bot detection
        if self.vision_model:
            try:
                screenshot_bytes = await page.screenshot(type='png')
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                result = await self.vision_model.analyze_similarweb_specific(screenshot_b64, current_url)
                
                if result.get("is_blocked", False):
                    block_type = result.get("block_type", "unknown")
                    recommended_action = result.get("recommended_action", "rotate_proxy")
                    logger.warning(f"🚫 Anti-bot detected via vision: {block_type}")
                    return True, block_type, recommended_action
                    
            except Exception as e:
                logger.debug(f"Vision detection error: {e}")
        
        return False, "", ""

    def mark_proxy_failure(self, proxy: ProxyInfo, site_url: str = None, failure_type: str = None):
        """Enhanced proxy failure tracking"""
        proxy.failure_count += 1
        proxy.consecutive_failures += 1
        
        # Track specific failure types
        if failure_type == "timeout":
            proxy.timeout_failures += 1
        elif failure_type == "redirect":
            proxy.redirect_failures += 1
        
        # Site-specific blocking
        if site_url and failure_type in ["cloudflare", "rate_limit", "access_denied", "blocked"]:
            proxy.blocked_sites.add(site_url)
            proxy.health = ProxyHealth.BLOCKED
            logger.warning(f"🚫 {proxy.proxy_type.value} proxy {proxy.server} blocked for {site_url}")
        else:
            proxy.health = ProxyHealth.DEGRADED
        
        # Mark as failed if too many consecutive failures
        if proxy.consecutive_failures >= self.max_consecutive_failures:
            proxy.health = ProxyHealth.FAILED
            logger.error(f"❌ {proxy.proxy_type.value} proxy {proxy.server} marked as failed")

    def mark_proxy_success(self, proxy: ProxyInfo, response_time: float = 0):
        """Mark proxy as successful"""
        proxy.success_count += 1
        proxy.consecutive_failures = 0
        proxy.timeout_failures = max(0, proxy.timeout_failures - 1)  # Reduce timeout failures on success
        proxy.redirect_failures = max(0, proxy.redirect_failures - 1)  # Reduce redirect failures
        proxy.last_used = time.time()
        proxy.response_time = response_time
        proxy.health = ProxyHealth.HEALTHY
        
        # Clear site-specific blocks on consistent success
        if proxy.success_count % 5 == 0:  # Every 5 successes
            proxy.blocked_sites.clear()
        
        logger.debug(f"✅ {proxy.proxy_type.value} proxy success: {proxy.server} (SR: {proxy.success_rate:.2%})")

    def get_proxy_stats(self) -> Dict:
        """Get comprehensive proxy statistics"""
        if not self.proxies:
            return {"total": 0, "available": 0}
        
        residential_stats = self._get_type_stats(ProxyType.RESIDENTIAL)
        mobile_stats = self._get_type_stats(ProxyType.MOBILE)
        
        return {
            "total": len(self.proxies),
            "residential": residential_stats,
            "mobile": mobile_stats,
            "available": sum(1 for p in self.proxies 
                           if p.health != ProxyHealth.FAILED and 
                              p.consecutive_failures < self.max_consecutive_failures),
            "timeout_threshold": self.timeout_threshold
        }

    def _get_type_stats(self, proxy_type: ProxyType) -> Dict:
        """Get statistics for specific proxy type"""
        type_proxies = [p for p in self.proxies if p.proxy_type == proxy_type]
        if not type_proxies:
            return {"count": 0, "available": 0, "success_rate": 0}
        
        available = sum(1 for p in type_proxies 
                       if p.health != ProxyHealth.FAILED and 
                          p.consecutive_failures < self.max_consecutive_failures)
        
        total_requests = sum(p.success_count + p.failure_count for p in type_proxies)
        total_successes = sum(p.success_count for p in type_proxies)
        success_rate = (total_successes / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "count": len(type_proxies),
            "available": available,
            "success_rate": round(success_rate, 1),
            "total_requests": total_requests
        }

    def test_proxy_connectivity(self, proxy_info: ProxyInfo) -> bool:
        """Test if proxy is working"""
        try:
            if proxy_info.proxy_type == ProxyType.RESIDENTIAL:
                # Test Webshare proxy
                response = requests.get(
                    "https://ipv4.webshare.io/",
                    proxies={
                        "http": f"http://{proxy_info.username}:{proxy_info.password}@{proxy_info.server.replace('http://', '')}",
                        "https": f"http://{proxy_info.username}:{proxy_info.password}@{proxy_info.server.replace('http://', '')}"
                    },
                    timeout=10
                )
                return response.status_code == 200
                
            elif proxy_info.proxy_type == ProxyType.MOBILE:
                # Test Oxylabs proxy
                entry = f'http://{proxy_info.username}:{proxy_info.password}@{proxy_info.server.replace("http://", "")}'
                query = urllib.request.ProxyHandler({
                    'http': entry,
                    'https': entry,
                })
                execute = urllib.request.build_opener(query)
                response = execute.open('https://ip.oxylabs.io/location')
                return response.getcode() == 200
                
        except Exception as e:
            logger.debug(f"Proxy test failed for {proxy_info.server}: {e}")
            return False
        
        return False

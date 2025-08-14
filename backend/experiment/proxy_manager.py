# import os
# import json
# import random
# import time
# import asyncio
# import logging
# import requests
# import urllib.request
# from typing import Dict, List, Optional, Tuple
# from dataclasses import dataclass, field
# from enum import Enum
# import base64
# import hashlib
# from collections import defaultdict
# from pathlib import Path

# logger = logging.getLogger(__name__)

# class ProxyType(Enum):
#     RESIDENTIAL = "residential"
#     MOBILE = "mobile"
#     DATACENTER = "datacenter"
#     ROTATING = "rotating"
#     STICKY = "sticky"

# class ProxyHealth(Enum):
#     HEALTHY = "healthy"
#     DEGRADED = "degraded"
#     BLOCKED = "blocked"
#     FAILED = "failed"
#     UNTESTED = "untested"

# @dataclass
# class ProxyInfo:
#     server: str
#     username: Optional[str] = None
#     password: Optional[str] = None
#     proxy_type: ProxyType = ProxyType.RESIDENTIAL
#     location: str = "unknown"
#     health: ProxyHealth = ProxyHealth.UNTESTED
#     success_count: int = 0
#     failure_count: int = 0
#     last_used: float = 0
#     blocked_sites: set = field(default_factory=set)
#     response_time: float = 0
#     consecutive_failures: int = 0
#     timeout_failures: int = 0
#     redirect_failures: int = 0
#     antibot_detections: int = 0
#     last_rotation: float = 0
#     session_id: str = ""
#     fingerprint_hash: str = ""
#     similarweb_success: int = 0  # Track SimilarWeb-specific success
#     similarweb_failures: int = 0  # Track SimilarWeb-specific failures
    
#     def __post_init__(self):
#         # Generate unique session ID
#         if not self.session_id:
#             data = f"{self.server}_{time.time()}_{random.random()}"
#             self.session_id = hashlib.md5(data.encode()).hexdigest()[:16]
    
#     @property
#     def success_rate(self) -> float:
#         total = self.success_count + self.failure_count
#         return self.success_count / total if total > 0 else 0.5  # Default to 50% for untested
    
#     @property
#     def similarweb_success_rate(self) -> float:
#         """SimilarWeb-specific success rate"""
#         total = self.similarweb_success + self.similarweb_failures
#         return self.similarweb_success / total if total > 0 else 0.5
    
#     @property
#     def health_score(self) -> float:
#         """Calculate overall health score (0-100)"""
#         base_score = self.success_rate * 100
        
#         # Penalties
#         if self.consecutive_failures > 0:
#             base_score -= self.consecutive_failures * 10
#         if self.timeout_failures > 0:
#             base_score -= self.timeout_failures * 5
#         if self.antibot_detections > 0:
#             base_score -= self.antibot_detections * 15
#         if self.health == ProxyHealth.BLOCKED:
#             base_score -= 50
#         elif self.health == ProxyHealth.DEGRADED:
#             base_score -= 25
#         elif self.health == ProxyHealth.FAILED:
#             base_score = 0
        
#         # Bonuses for SimilarWeb success
#         if self.similarweb_success > 0:
#             base_score += self.similarweb_success_rate * 20
        
#         # Response time bonus
#         if self.response_time > 0 and self.response_time < 2:
#             base_score += 10
#         if self.success_count > 10 and self.success_rate > 0.8:
#             base_score += 15
        
#         return max(0, min(100, base_score))
    
#     def to_playwright_dict(self) -> Dict:
#         proxy_dict = {"server": self.server}
#         if self.username:
#             proxy_dict["username"] = self.username
#         if self.password:
#             proxy_dict["password"] = self.password
#         return proxy_dict
    
#     def should_rotate(self) -> bool:
#         """Check if proxy should be rotated"""
#         # Time-based rotation
#         if time.time() - self.last_rotation > random.randint(300, 900):  # 5-15 minutes
#             return True
        
#         # Failure-based rotation
#         if self.consecutive_failures >= 3:
#             return True
        
#         # Anti-bot detection rotation
#         if self.antibot_detections >= 2:
#             return True
        
#         # SimilarWeb-specific rotation
#         if self.similarweb_failures >= 3:
#             return True
        
#         # Health-based rotation
#         if self.health_score < 30:
#             return True
        
#         return False

# class AdvancedProxyManager:
#     def __init__(self, vision_model=None):
#         self.proxies: List[ProxyInfo] = []
#         self.residential_proxies: List[ProxyInfo] = []
#         self.mobile_proxies: List[ProxyInfo] = []
#         self.datacenter_proxies: List[ProxyInfo] = []
#         self.current_proxy_index = 0
#         self.vision_model = vision_model
        
#         # Enhanced settings
#         self.max_proxy_retries = 10
#         self.max_consecutive_failures = 3
#         self.timeout_threshold = 30  # seconds
#         self.proxy_rotation_strategy = "smart"  # smart, random, sequential, weighted
        
#         # Statistics tracking
#         self.domain_stats = defaultdict(lambda: defaultdict(int))
#         self.proxy_performance = defaultdict(lambda: defaultdict(float))
#         self.similarweb_specific_stats = defaultdict(lambda: defaultdict(int))
        
#         # Load all proxy sources
#         self._load_all_proxies()
#         self._organize_proxies()
        
#         # Load saved proxy performance if exists
#         self._load_saved_performance()
        
#         logger.info(f"📊 Proxy Manager initialized with {len(self.proxies)} proxies")

#     def _load_all_proxies(self):
#         """Load proxies from all available sources"""
#         # Load from environment variables
#         self._load_env_proxies()
        
#         # Load from proxy files
#         self._load_proxy_files()
        
#         # Load provider-specific proxies
#         self._load_webshare_residential_proxies()
#         self._load_oxylabs_mobile_proxies()
#         # self._load_brightdata_proxies()
#         # self._load_smartproxy_proxies()
        
#         # Load free proxy lists (with caution)
#         if os.getenv("USE_FREE_PROXIES", "false").lower() == "true":
#             self._load_free_proxy_lists()

#     def _load_env_proxies(self):
#         """Load proxies from environment variables"""
#         # Generic proxy format: PROXY_LIST=http://user:pass@host:port,http://...
#         proxy_list = os.getenv("PROXY_LIST", "")
#         if proxy_list:
#             for proxy_str in proxy_list.split(","):
#                 if proxy_str.strip():
#                     self._parse_proxy_string(proxy_str.strip())

#     def _parse_proxy_string(self, proxy_str: str, proxy_type: ProxyType = ProxyType.RESIDENTIAL):
#         """Parse proxy string in various formats"""
#         try:
#             if "@" in proxy_str:
#                 # Format: http://user:pass@host:port
#                 import re
#                 match = re.match(r'(https?://)([^:]+):([^@]+)@([^:]+):(\d+)', proxy_str)
#                 if match:
#                     protocol, username, password, host, port = match.groups()
#                     proxy_info = ProxyInfo(
#                         server=f"{protocol}{host}:{port}",
#                         username=username,
#                         password=password,
#                         proxy_type=proxy_type,
#                         location="dynamic"
#                     )
#                     self.proxies.append(proxy_info)
#             else:
#                 # Format: host:port:user:pass or http://host:port
#                 parts = proxy_str.replace("http://", "").replace("https://", "").split(":")
#                 if len(parts) >= 4:
#                     host, port, username, password = parts[:4]
#                     proxy_info = ProxyInfo(
#                         server=f"http://{host}:{port}",
#                         username=username,
#                         password=password,
#                         proxy_type=proxy_type,
#                         location="dynamic"
#                     )
#                     self.proxies.append(proxy_info)
#                 elif len(parts) == 2:
#                     host, port = parts
#                     proxy_info = ProxyInfo(
#                         server=f"http://{host}:{port}",
#                         proxy_type=ProxyType.DATACENTER,
#                         location="public"
#                     )
#                     self.proxies.append(proxy_info)
#         except Exception as e:
#             logger.debug(f"Could not parse proxy string {proxy_str}: {e}")

#     def _load_proxy_files(self):
#         """Load proxies from text files"""
#         proxy_files = [
#             "proxies.txt",
#             "residential_proxies.txt",
#             "mobile_proxies.txt",
#             "datacenter_proxies.txt",
#             "rotating_proxies.txt",
#             "Webshare-10-proxies.txt"  # Your specific file
#         ]
        
#         for filename in proxy_files:
#             if os.path.exists(filename):
#                 proxy_type = ProxyType.RESIDENTIAL  # Default
#                 if "mobile" in filename:
#                     proxy_type = ProxyType.MOBILE
#                 elif "datacenter" in filename:
#                     proxy_type = ProxyType.DATACENTER
#                 elif "rotating" in filename:
#                     proxy_type = ProxyType.ROTATING
#                 elif "Webshare" in filename:
#                     proxy_type = ProxyType.RESIDENTIAL
                
#                 try:
#                     with open(filename, 'r') as f:
#                         for line in f:
#                             line = line.strip()
#                             if line and not line.startswith("#"):
#                                 self._parse_proxy_string(line, proxy_type)
#                     logger.info(f"✅ Loaded proxies from {filename}")
#                 except Exception as e:
#                     logger.error(f"Error loading {filename}: {e}")

#     def _load_webshare_residential_proxies(self):
#         """Load Webshare residential proxies with dynamic configuration"""
#         try:
#             # Method 1: From environment
#             webshare_config = os.getenv("WEBSHARE_PROXY_CONFIG")
#             if webshare_config:
#                 config = json.loads(webshare_config)
#                 for i in range(config.get("count", 1)):
#                     proxy_info = ProxyInfo(
#                         server=config.get("server", "http://p.webshare.io:80"),
#                         username=f"{config['username']}-session-{random.randint(10000, 99999)}",
#                         password=config["password"],
#                         proxy_type=ProxyType.ROTATING if "rotate" in config["username"] else ProxyType.STICKY,
#                         location="rotating_residential"
#                     )
#                     self.residential_proxies.append(proxy_info)
            
#             # Method 2: From credentials
#             webshare_username = os.getenv("WEBSHARE_USERNAME", "npgyhuvj-rotate")
#             webshare_password = os.getenv("WEBSHARE_PASSWORD", "hxwwky71phsg")
            
#             if webshare_username and webshare_password:
#                 # Create multiple sessions for rotation
#                 num_sessions = 10  # Create more sessions for better rotation
#                 for i in range(num_sessions):
#                     session_id = f"session-{random.randint(10000, 99999)}"
#                     proxy_info = ProxyInfo(
#                         server="http://p.webshare.io:80",
#                         username=f"{webshare_username}-{session_id}",
#                         password=webshare_password,
#                         proxy_type=ProxyType.ROTATING,
#                         location=f"webshare_session_{i}"
#                     )
#                     self.residential_proxies.append(proxy_info)
            
#             logger.info(f"✅ Loaded {len(self.residential_proxies)} Webshare residential proxies")
            
#         except Exception as e:
#             logger.error(f"❌ Error loading Webshare proxies: {e}")

#     def _load_oxylabs_mobile_proxies(self):
#         """Load Oxylabs mobile proxies with dynamic endpoints"""
#         try:
#             oxylabs_username = os.getenv("OXYLABS_USERNAME")
#             oxylabs_password = os.getenv("OXYLABS_PASSWORD")
            
#             if oxylabs_username and oxylabs_password:
#                 # Multiple Oxylabs endpoints for different purposes
#                 endpoints = [
#                     ("pr.oxylabs.io:7777", ProxyType.RESIDENTIAL, "residential"),
#                     # ("unblock.oxylabs.io:60000", ProxyType.ROTATING, "unblocker"),
#                     # ("realtime.oxylabs.io:60000", ProxyType.MOBILE, "realtime"),
#                 ]
                
#                 for endpoint, proxy_type, location in endpoints:
#                     # Create multiple sessions
#                     for i in range(5):
#                         session_id = random.randint(100000, 999999)
#                         proxy_info = ProxyInfo(
#                             server=f"http://{endpoint}",
#                             username=f"customer-{oxylabs_username}-session-{session_id}",
#                             password=oxylabs_password,
#                             proxy_type=proxy_type,
#                             location=f"oxylabs_{location}_{i}"
#                         )
#                         self.mobile_proxies.append(proxy_info)
                
#                 logger.info(f"✅ Loaded {len(self.mobile_proxies)} Oxylabs mobile proxies")
            
#         except Exception as e:
#             logger.error(f"❌ Error loading Oxylabs proxies: {e}")

#     def _load_brightdata_proxies(self):
#         """Load BrightData (formerly Luminati) proxies"""
#         try:
#             brightdata_username = os.getenv("BRIGHTDATA_USERNAME")
#             brightdata_password = os.getenv("BRIGHTDATA_PASSWORD")
            
#             if brightdata_username and brightdata_password:
#                 endpoints = [
#                     ("zproxy.lum-superproxy.io:22225", ProxyType.RESIDENTIAL),
#                     ("brd.superproxy.io:22225", ProxyType.DATACENTER),
#                     ("mobile.superproxy.io:22225", ProxyType.MOBILE),
#                 ]
                
#                 for endpoint, proxy_type in endpoints:
#                     for i in range(5):
#                         session_id = f"session_{random.randint(1000000, 9999999)}"
#                         proxy_info = ProxyInfo(
#                             server=f"http://{endpoint}",
#                             username=f"{brightdata_username}-session-{session_id}",
#                             password=brightdata_password,
#                             proxy_type=proxy_type,
#                             location=f"brightdata_{proxy_type.value}_{i}"
#                         )
#                         self.proxies.append(proxy_info)
                
#                 logger.info(f"✅ Loaded BrightData proxies")
#         except Exception as e:
#             logger.debug(f"BrightData proxies not configured: {e}")

#     def _load_smartproxy_proxies(self):
#         """Load SmartProxy proxies"""
#         try:
#             smartproxy_username = os.getenv("SMARTPROXY_USERNAME")
#             smartproxy_password = os.getenv("SMARTPROXY_PASSWORD")
            
#             if smartproxy_username and smartproxy_password:
#                 endpoints = [
#                     ("gate.smartproxy.com:10000", ProxyType.RESIDENTIAL),
#                     ("gate.smartproxy.com:20000", ProxyType.DATACENTER),
#                     ("gate.smartproxy.com:30000", ProxyType.MOBILE),
#                 ]
                
#                 for endpoint, proxy_type in endpoints:
#                     for i in range(5):
#                         proxy_info = ProxyInfo(
#                             server=f"http://{endpoint}",
#                             username=smartproxy_username,
#                             password=smartproxy_password,
#                             proxy_type=proxy_type,
#                             location=f"smartproxy_{proxy_type.value}_{i}"
#                         )
#                         self.proxies.append(proxy_info)
                
#                 logger.info(f"✅ Loaded SmartProxy proxies")
#         except Exception as e:
#             logger.debug(f"SmartProxy proxies not configured: {e}")

#     def _load_free_proxy_lists(self):
#         """Load free proxy lists (use with caution)"""
#         try:
#             # This is risky for production but can be useful for testing
#             free_proxy_apis = [
#                 "https://www.proxy-list.download/api/v1/get?type=http",
#                 "https://api.proxyscrape.com/v2/?request=get&protocol=http",
#             ]
            
#             for api_url in free_proxy_apis:
#                 try:
#                     response = requests.get(api_url, timeout=5)
#                     if response.status_code == 200:
#                         for line in response.text.splitlines()[:10]:  # Limit to 10 free proxies
#                             if ":" in line:
#                                 proxy_info = ProxyInfo(
#                                     server=f"http://{line.strip()}",
#                                     proxy_type=ProxyType.DATACENTER,
#                                     location="free_proxy",
#                                     health=ProxyHealth.UNTESTED
#                                 )
#                                 self.datacenter_proxies.append(proxy_info)
#                 except:
#                     pass
            
#             if self.datacenter_proxies:
#                 logger.info(f"⚠️ Loaded {len(self.datacenter_proxies)} free proxies (use with caution)")
#         except Exception as e:
#             logger.debug(f"Could not load free proxies: {e}")

#     def _organize_proxies(self):
#         """Organize all proxies with smart categorization"""
#         # Combine all proxies
#         all_proxies = self.residential_proxies + self.mobile_proxies + self.datacenter_proxies + self.proxies
        
#         # Remove duplicates based on server + credentials
#         seen = set()
#         unique_proxies = []
#         for proxy in all_proxies:
#             key = f"{proxy.server}_{proxy.username}_{proxy.password}"
#             if key not in seen:
#                 seen.add(key)
#                 unique_proxies.append(proxy)
        
#         self.proxies = unique_proxies
        
#         # Sort by proxy type priority (for SimilarWeb, residential is best)
#         self.proxies.sort(key=lambda p: (
#             0 if p.proxy_type == ProxyType.RESIDENTIAL else
#             1 if p.proxy_type == ProxyType.ROTATING else
#             2 if p.proxy_type == ProxyType.MOBILE else
#             3 if p.proxy_type == ProxyType.STICKY else
#             4  # DATACENTER
#         ))
        
#         logger.info(f"📊 Proxy Summary:")
#         logger.info(f"   Total unique proxies: {len(self.proxies)}")
        
#         # Count by type
#         type_counts = defaultdict(int)
#         for proxy in self.proxies:
#             type_counts[proxy.proxy_type.value] += 1
        
#         for proxy_type, count in type_counts.items():
#             logger.info(f"   {proxy_type.capitalize()}: {count}")

#     def get_best_proxy(self, prefer_type: ProxyType = None, exclude_blocked_for: str = None, 
#                       strategy: str = None, for_similarweb: bool = False) -> Optional[ProxyInfo]:
#         """Get best proxy using intelligent selection strategy"""
        
#         strategy = strategy or self.proxy_rotation_strategy
        
#         # For SimilarWeb, prioritize residential proxies
#         if for_similarweb or (exclude_blocked_for and "similarweb" in exclude_blocked_for.lower()):
#             prefer_type = prefer_type or ProxyType.RESIDENTIAL
#             # Use SimilarWeb-specific success rate for selection
            
#         # Filter available proxies
#         available = []
#         for proxy in self.proxies:
#             # Skip failed proxies
#             if proxy.health == ProxyHealth.FAILED:
#                 continue
            
#             # Skip proxies with too many consecutive failures
#             if proxy.consecutive_failures >= self.max_consecutive_failures:
#                 continue
            
#             # Skip blocked proxies for specific domain
#             if exclude_blocked_for and exclude_blocked_for in proxy.blocked_sites:
#                 continue
            
#             # For SimilarWeb, skip proxies with poor SimilarWeb performance
#             if for_similarweb and proxy.similarweb_failures > 5:
#                 continue
            
#             # Filter by preferred type if specified
#             if prefer_type and proxy.proxy_type != prefer_type:
#                 # For SimilarWeb, allow fallback to mobile if no residential available
#                 if not (for_similarweb and proxy.proxy_type == ProxyType.MOBILE):
#                     continue
            
#             available.append(proxy)
        
#         if not available:
#             # Reset some proxies if all are exhausted
#             self._reset_failed_proxies()
#             available = [p for p in self.proxies if p.health != ProxyHealth.FAILED]
        
#         if not available:
#             logger.error("❌ No proxies available!")
#             return None
        
#         # Select based on strategy
#         if strategy == "random":
#             selected = random.choice(available)
        
#         elif strategy == "sequential":
#             # Round-robin selection
#             selected = available[self.current_proxy_index % len(available)]
#             self.current_proxy_index += 1
        
#         elif strategy == "weighted":
#             # Weight by success rate and health score
#             if for_similarweb:
#                 # Use SimilarWeb-specific weighting
#                 weights = [max(0.1, (p.similarweb_success_rate * 0.7 + p.health_score / 100 * 0.3)) 
#                           for p in available]
#             else:
#                 weights = [max(0.1, p.health_score / 100) for p in available]
#             selected = random.choices(available, weights=weights)[0]
        
#         else:  # smart (default)
#             # Sort by multiple factors
#             if for_similarweb:
#                 # SimilarWeb-specific sorting
#                 available.sort(key=lambda p: (
#                     -p.similarweb_success_rate,  # Best SimilarWeb success rate first
#                     -p.health_score,  # Higher health score
#                     p.similarweb_failures,  # Fewer SimilarWeb failures
#                     p.antibot_detections,  # Fewer anti-bot detections
#                     p.response_time if p.response_time > 0 else 999,  # Lower response time
#                     p.last_used,  # Least recently used
#                     random.random()  # Random tiebreaker
#                 ))
#             else:
#                 available.sort(key=lambda p: (
#                     -p.health_score,  # Higher health score first
#                     -p.success_rate,  # Higher success rate
#                     p.response_time if p.response_time > 0 else 999,  # Lower response time
#                     p.antibot_detections,  # Fewer anti-bot detections
#                     p.last_used,  # Least recently used
#                     random.random()  # Random tiebreaker
#                 ))
#             selected = available[0]
        
#         # Update last used time
#         selected.last_used = time.time()
        
#         # Generate new session if rotating
#         if selected.proxy_type == ProxyType.ROTATING and selected.should_rotate():
#             selected = self._rotate_proxy_session(selected)
        
#         logger.info(f"🎯 Selected {selected.proxy_type.value} proxy: {selected.server} (Health: {selected.health_score:.1f}%, SW Success: {selected.similarweb_success_rate:.1%})")
#         return selected

#     def _rotate_proxy_session(self, proxy: ProxyInfo) -> ProxyInfo:
#         """Rotate proxy session for sticky session proxies"""
#         if "-session-" in proxy.username:
#             # Update session ID
#             base_username = proxy.username.split("-session-")[0]
#             new_session = f"session-{random.randint(10000, 99999)}"
#             proxy.username = f"{base_username}-{new_session}"
#             proxy.last_rotation = time.time()
#             proxy.consecutive_failures = 0
#             proxy.antibot_detections = 0
#             logger.info(f"🔄 Rotated proxy session: {new_session}")
        
#         return proxy

#     def _reset_failed_proxies(self):
#         """Reset some failed proxies to give them another chance"""
#         reset_count = 0
#         for proxy in self.proxies:
#             if proxy.health == ProxyHealth.FAILED and time.time() - proxy.last_used > 300:  # 5 minutes
#                 proxy.health = ProxyHealth.DEGRADED
#                 proxy.consecutive_failures = max(0, proxy.consecutive_failures - 2)
#                 proxy.similarweb_failures = max(0, proxy.similarweb_failures - 1)
#                 reset_count += 1
        
#         if reset_count > 0:
#             logger.info(f"♻️ Reset {reset_count} failed proxies")

#     async def detect_anti_bot_with_vision(self, page, goal: str) -> Tuple[bool, str, Optional[str]]:
#         """Enhanced anti-bot detection with vision model"""
#         if not self.vision_model:
#             return False, "", None
        
#         try:
#             # Take screenshot for analysis
#             screenshot_bytes = await page.screenshot(type='png')
#             screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
#             # Get page info
#             page_title = await page.title()
#             page_url = page.url
            
#             # Enhanced detection prompt for SimilarWeb
#             detection_prompt = f"""
#             ADVANCED ANTI-BOT DETECTION TASK (SimilarWeb Focus):
            
#             Analyze this webpage for ANY anti-bot systems, CAPTCHAs, or access restrictions.
#             Current URL: {page_url}
#             Page Title: {page_title}
#             Goal: {goal}
            
#             DETECTION TARGETS:
            
#             1. **SimilarWeb Specific Blocks**
#                 - "Create an account" modal
#                 - "Sign in to continue" popup
#                 - "Upgrade to see more data" message
#                 - Rate limiting messages
#                 - "Too many requests" errors
            
#             2. **Cloudflare Protection**
#                 - "Checking your browser", "Please wait"
#                 - "Just a moment", "Verifying you are human"
#                 - Ray ID visible
#                 - Orange/yellow loading animations
            
#             3. **CAPTCHA Systems**
#                 - reCAPTCHA (Google): checkboxes, image grids
#                 - hCaptcha: similar to reCAPTCHA with different styling
#                 - FunCaptcha: rotating images
#                 - GeeTest: sliding puzzles
#                 - Text CAPTCHAs: distorted text
            
#             4. **Access Restrictions**
#                 - "403 Forbidden", "Access Denied"
#                 - "401 Unauthorized", "Authentication Required"
#                 - "429 Too Many Requests", "Rate Limited"
#                 - Geographic restrictions
#                 - IP blocking messages
            
#             5. **Bot Detection Services**
#                 - PerimeterX: "Please verify you are human"
#                 - DataDome: specific blocking pages
#                 - Kasada: invisible challenges
#                 - Shape Security: form protection
#                 - Akamai Bot Manager: various messages
            
#             6. **Fingerprinting Detection**
#                 - Blank page that's loading indefinitely
#                 - "Verifying browser" messages
#                 - Unusual delays without visible content
            
#             Respond with JSON:
#             {{
#                 "is_anti_bot": true/false,
#                 "detection_type": "cloudflare|captcha|access_denied|rate_limit|bot_detection|fingerprinting|auth_required|none",
#                 "specific_service": "similarweb_login|cloudflare|recaptcha|hcaptcha|perimeterx|etc",
#                 "confidence": 0.0-1.0,
#                 "description": "What you see",
#                 "bypass_difficulty": "easy|medium|hard|impossible",
#                 "suggested_action": "rotate_proxy|solve_captcha|wait|retry|use_browser|change_headers|abort"
#             }}
#             """
            
#             # Analyze with vision model
#             result = await self.vision_model.analyze_anti_bot_page(
#                 screenshot_b64, detection_prompt, page_url
#             )
            
#             if result.get("is_anti_bot", False):
#                 detection_type = result.get("detection_type", "unknown")
#                 specific_service = result.get("specific_service", "unknown")
#                 suggested_action = result.get("suggested_action", "rotate_proxy")
                
#                 logger.warning(f"🚫 Anti-bot detected: {specific_service} ({detection_type})")
#                 logger.info(f"   Bypass difficulty: {result.get('bypass_difficulty', 'unknown')}")
#                 logger.info(f"   Suggested action: {suggested_action}")
                
#                 return True, detection_type, suggested_action
            
#             return False, "", None
            
#         except Exception as e:
#             logger.error(f"Error in vision-based anti-bot detection: {e}")
#             return False, "", None

#     def mark_proxy_failure(self, proxy: ProxyInfo, site_url: str = None, failure_type: str = None):
#         """Enhanced proxy failure tracking with intelligent marking"""
#         proxy.failure_count += 1
#         proxy.consecutive_failures += 1
        
#         # Track SimilarWeb-specific failures
#         if site_url and "similarweb" in site_url.lower():
#             proxy.similarweb_failures += 1
#             self.similarweb_specific_stats[proxy.session_id]["failures"] += 1
        
#         # Track specific failure types
#         if failure_type == "timeout":
#             proxy.timeout_failures += 1
#         elif failure_type == "redirect":
#             proxy.redirect_failures += 1
#         elif failure_type in ["cloudflare", "captcha", "bot_detection", "fingerprinting"]:
#             proxy.antibot_detections += 1
        
#         # Update domain-specific stats
#         if site_url:
#             domain = self._extract_domain(site_url)
#             self.domain_stats[domain][f"proxy_{proxy.session_id}_failures"] += 1
            
#             # Site-specific blocking
#             if failure_type in ["cloudflare", "rate_limit", "access_denied", "blocked"]:
#                 proxy.blocked_sites.add(domain)
#                 logger.warning(f"🚫 Proxy {proxy.session_id} blocked for {domain}")
        
#         # Update health status
#         if proxy.consecutive_failures >= self.max_consecutive_failures:
#             proxy.health = ProxyHealth.FAILED
#             logger.error(f"❌ Proxy {proxy.session_id} marked as FAILED")
#         elif proxy.antibot_detections >= 3:
#             proxy.health = ProxyHealth.BLOCKED
#             logger.warning(f"⚠️ Proxy {proxy.session_id} marked as BLOCKED (anti-bot)")
#         elif proxy.consecutive_failures >= 2:
#             proxy.health = ProxyHealth.DEGRADED
        
#         # Track performance metrics
#         self.proxy_performance[proxy.session_id]["failures"] += 1
#         self.proxy_performance[proxy.session_id]["last_failure"] = time.time()

#     def mark_proxy_success(self, proxy: ProxyInfo, response_time: float = 0, site_url: str = None):
#         """Mark proxy as successful with performance tracking"""
#         proxy.success_count += 1
#         proxy.consecutive_failures = 0
#         proxy.timeout_failures = max(0, proxy.timeout_failures - 1)
#         proxy.redirect_failures = max(0, proxy.redirect_failures - 1)
#         proxy.antibot_detections = max(0, proxy.antibot_detections - 1)
#         proxy.last_used = time.time()
        
#         # Track SimilarWeb-specific success
#         if site_url and "similarweb" in site_url.lower():
#             proxy.similarweb_success += 1
#             self.similarweb_specific_stats[proxy.session_id]["successes"] += 1
        
#         # Update response time with moving average
#         if response_time > 0:
#             if proxy.response_time > 0:
#                 proxy.response_time = (proxy.response_time * 0.7) + (response_time * 0.3)
#             else:
#                 proxy.response_time = response_time
        
#         # Update health
#         if proxy.health != ProxyHealth.HEALTHY:
#             if proxy.success_count > 5 and proxy.success_rate > 0.7:
#                 proxy.health = ProxyHealth.HEALTHY
#                 logger.info(f"✅ Proxy {proxy.session_id} restored to HEALTHY")
        
#         # Clear site blocks on consistent success
#         if proxy.success_count % 10 == 0:
#             if len(proxy.blocked_sites) > 0:
#                 proxy.blocked_sites.clear()
#                 logger.info(f"🔓 Cleared blocked sites for proxy {proxy.session_id}")
        
#         # Update domain stats
#         if site_url:
#             domain = self._extract_domain(site_url)
#             self.domain_stats[domain][f"proxy_{proxy.session_id}_successes"] += 1
        
#         # Track performance
#         self.proxy_performance[proxy.session_id]["successes"] += 1
#         self.proxy_performance[proxy.session_id]["last_success"] = time.time()
#         self.proxy_performance[proxy.session_id]["avg_response_time"] = proxy.response_time
        
#         logger.debug(f"✅ Proxy success: {proxy.session_id} (SR: {proxy.success_rate:.2%}, SW SR: {proxy.similarweb_success_rate:.2%}, RT: {proxy.response_time:.2f}s)")

#     def _extract_domain(self, url: str) -> str:
#         """Extract domain from URL"""
#         from urllib.parse import urlparse
#         parsed = urlparse(url)
#         return parsed.netloc or url

#     def get_proxy_stats(self) -> Dict:
#         """Get comprehensive proxy statistics with SimilarWeb focus"""
#         if not self.proxies:
#             return {"total": 0, "available": 0, "health_summary": {}}
        
#         stats = {
#             "total": len(self.proxies),
#             "by_type": defaultdict(int),
#             "by_health": defaultdict(int),
#             "available": 0,
#             "average_success_rate": 0,
#             "average_response_time": 0,
#             "similarweb_performance": {
#                 "total_attempts": 0,
#                 "total_successes": 0,
#                 "success_rate": 0
#             },
#             "top_performers": [],
#             "worst_performers": [],
#             "domain_stats": dict(self.domain_stats)
#         }
        
#         total_success_rate = 0
#         total_response_time = 0
#         response_time_count = 0
#         total_sw_attempts = 0
#         total_sw_successes = 0
        
#         for proxy in self.proxies:
#             # Count by type
#             stats["by_type"][proxy.proxy_type.value] += 1
            
#             # Count by health
#             stats["by_health"][proxy.health.value] += 1
            
#             # Count available
#             if proxy.health not in [ProxyHealth.FAILED, ProxyHealth.BLOCKED]:
#                 if proxy.consecutive_failures < self.max_consecutive_failures:
#                     stats["available"] += 1
            
#             # Calculate averages
#             total_success_rate += proxy.success_rate
#             if proxy.response_time > 0:
#                 total_response_time += proxy.response_time
#                 response_time_count += 1
            
#             # SimilarWeb specific stats
#             total_sw_attempts += proxy.similarweb_success + proxy.similarweb_failures
#             total_sw_successes += proxy.similarweb_success
        
#         # Calculate averages
#         stats["average_success_rate"] = (total_success_rate / len(self.proxies)) * 100 if self.proxies else 0
#         stats["average_response_time"] = total_response_time / response_time_count if response_time_count > 0 else 0
        
#         # SimilarWeb performance
#         stats["similarweb_performance"]["total_attempts"] = total_sw_attempts
#         stats["similarweb_performance"]["total_successes"] = total_sw_successes
#         stats["similarweb_performance"]["success_rate"] = (total_sw_successes / total_sw_attempts * 100) if total_sw_attempts > 0 else 0
        
#         # Get top and worst performers for SimilarWeb
#         sw_sorted = sorted(self.proxies, key=lambda p: (p.similarweb_success_rate, p.health_score), reverse=True)
#         stats["top_performers"] = [
#             {
#                 "id": p.session_id,
#                 "type": p.proxy_type.value,
#                 "health_score": p.health_score,
#                 "success_rate": p.success_rate,
#                 "sw_success_rate": p.similarweb_success_rate,
#                 "sw_successes": p.similarweb_success
#             }
#             for p in sw_sorted[:5]
#         ]
        
#         stats["worst_performers"] = [
#             {
#                 "id": p.session_id,
#                 "type": p.proxy_type.value,
#                 "health_score": p.health_score,
#                 "failures": p.consecutive_failures,
#                 "sw_failures": p.similarweb_failures
#             }
#             for p in sw_sorted[-5:] if p.health_score < 50 or p.similarweb_failures > 0
#         ]
        
#         return stats

#     def export_proxy_performance(self, filename: str = "proxy_performance.json"):
#         """Export proxy performance data for analysis"""
#         data = {
#             "timestamp": time.time(),
#             "stats": self.get_proxy_stats(),
#             "proxy_details": [
#                 {
#                     "id": p.session_id,
#                     "type": p.proxy_type.value,
#                     "health": p.health.value,
#                     "health_score": p.health_score,
#                     "success_rate": p.success_rate,
#                     "response_time": p.response_time,
#                     "success_count": p.success_count,
#                     "failure_count": p.failure_count,
#                     "antibot_detections": p.antibot_detections,
#                     "blocked_sites": list(p.blocked_sites),
#                     "similarweb_success": p.similarweb_success,
#                     "similarweb_failures": p.similarweb_failures,
#                     "similarweb_success_rate": p.similarweb_success_rate
#                 }
#                 for p in self.proxies
#             ],
#             "performance_metrics": dict(self.proxy_performance),
#             "similarweb_specific": dict(self.similarweb_specific_stats)
#         }
        
#         try:
#             with open(filename, 'w') as f:
#                 json.dump(data, f, indent=2)
#             logger.info(f"📊 Exported proxy performance to {filename}")
#         except Exception as e:
#             logger.error(f"Failed to export proxy performance: {e}")
    
#     def _load_saved_performance(self):
#         """Load previously saved proxy performance data"""
#         try:
#             if Path("proxy_performance.json").exists():
#                 with open("proxy_performance.json", 'r') as f:
#                     data = json.load(f)
                    
#                 # Load SimilarWeb specific stats
#                 if "similarweb_specific" in data:
#                     for proxy_id, stats in data["similarweb_specific"].items():
#                         self.similarweb_specific_stats[proxy_id] = defaultdict(int, stats)
                
#                 # Update proxy health based on saved data
#                 if "proxy_details" in data:
#                     saved_proxies = {p["id"]: p for p in data["proxy_details"]}
#                     for proxy in self.proxies:
#                         if proxy.session_id in saved_proxies:
#                             saved = saved_proxies[proxy.session_id]
#                             proxy.similarweb_success = saved.get("similarweb_success", 0)
#                             proxy.similarweb_failures = saved.get("similarweb_failures", 0)
#                             proxy.success_count = saved.get("success_count", 0)
#                             proxy.failure_count = saved.get("failure_count", 0)
                
#                 logger.info(f"📚 Loaded saved proxy performance data")
#         except Exception as e:
#             logger.debug(f"Could not load saved performance: {e}")

#     def reset_all_proxies(self):
#         """Reset all proxies to fresh state"""
#         for proxy in self.proxies:
#             proxy.health = ProxyHealth.UNTESTED
#             proxy.consecutive_failures = 0
#             proxy.antibot_detections = 0
#             proxy.timeout_failures = 0
#             proxy.redirect_failures = 0
#             proxy.blocked_sites.clear()
#         logger.info("🔄 Reset all proxies to fresh state")

#     def get_similarweb_optimized_proxy(self) -> Optional[ProxyInfo]:
#         """Get proxy specifically optimized for SimilarWeb"""
#         return self.get_best_proxy(
#             prefer_type=ProxyType.RESIDENTIAL,
#             exclude_blocked_for="similarweb.com",
#             strategy="smart",
#             for_similarweb=True
#         )

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
    session_id: int = 0
    
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

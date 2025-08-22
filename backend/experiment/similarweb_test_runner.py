#!/usr/bin/env python3
"""
Complete SimilarWeb Scraper Test Runner - 100 URLs with Detailed Analysis
"""

import asyncio
import json
import csv
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import sys
import os
import re
from playwright.async_api import async_playwright
from smart_browser_controller import EnhancedSmartBrowserController
from proxy_manager import AdvancedProxyManager
from anti_bot_detection import AntiBotVisionModel
from fingerprint_evasion import AdvancedFingerprintEvasion
from similarweb_extractor import SimilarWebExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('similarweb_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimilarWebTestResult:
    def __init__(self):
        self.url = ""
        self.domain = ""
        self.success = False
        self.extraction_success = False
        self.error = ""
        self.anti_bot_detected = False
        self.anti_bot_type = ""
        self.captcha_encountered = False
        self.proxy_used = ""
        self.fingerprint_profile = ""
        self.attempts = 0
        self.total_time = 0
        self.navigation_time = 0
        self.extraction_time = 0
        self.data_extracted = {}
        self.metrics_found = []
        self.confidence_score = 0.0
        self.page_validated = False
        self.timestamp = time.time()

class EnhancedSmartBrowserController(EnhancedSmartBrowserController):
    """Enhanced browser controller with complete fingerprint evasion"""
    
    def __init__(self, headless: bool, proxy: dict | None, enable_streaming: bool = False):
        super().__init__(headless, proxy, enable_streaming)
        self.fingerprint_evasion = AdvancedFingerprintEvasion()
        self.current_fingerprint_profile = None

    async def __aenter__(self):
        """Initialize with advanced fingerprint evasion - FIXED VERSION"""
        # Get random fingerprint profile BEFORE browser initialization
        self.current_fingerprint_profile = self.fingerprint_evasion.get_random_profile()
        logger.info(f"🎭 Using fingerprint profile: {self.current_fingerprint_profile['name']}")
        
        # Initialize Playwright
        self.play = await async_playwright().start()
        
        # Enhanced launch options with incognito mode
        launch_options = {
            "headless": self.headless,
            "args": [
                "--incognito",  # Incognito mode
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
        
        # ✅ CORRECT: Create context with user agent and fingerprint settings
        context_options = {
            "viewport": self.current_fingerprint_profile["viewport"],
            "user_agent": self.current_fingerprint_profile["user_agent"],  # Set user agent HERE
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
        self.context = context
        # Inject advanced fingerprint evasion script
        fingerprint_script = self.fingerprint_evasion.generate_anti_fingerprintjs_script(
            self.current_fingerprint_profile
        )
        await self.page.add_init_script(fingerprint_script)
        
        # Set up CDP streaming if enabled
        if self.enable_streaming:
            await self._setup_cdp_streaming()
        
        return self

    async def handle_similarweb_popups(self):
        """Handle SimilarWeb account creation and login popups"""
        try:
            logger.info("🔍 Checking for SimilarWeb popups...")
            await asyncio.sleep(3)
            
            popup_selectors = [
                '[class*="modal"]', '[class*="popup"]', '[class*="dialog"]',
                '[class*="signup"]', '[class*="login"]', '[class*="register"]',
                '[class*="overlay"]', '[id*="modal"]'
            ]
            
            for selector in popup_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            close_selectors = [
                                '[class*="close"]', '[aria-label*="close"]',
                                'button:has-text("×")', 'button:has-text("✕")',
                                'button[title*="close"]'
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
            
            # Try pressing Escape as fallback
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

class SimilarWebScraper:
    def __init__(self, use_proxies: bool = True, headless: bool = False):
        self.use_proxies = use_proxies
        self.headless = headless
        self.proxy_manager = AdvancedProxyManager()
        self.extractor = SimilarWebExtractor()
        self.results = []
        
        # ✅ ADD: Session tracking
        # self.current_browser = None
        # self.session_start_time = None
        # self.requests_in_session = 0
        
        self.stats = {
            'total_attempts': 0,
            'successful_navigations': 0,
            'successful_extractions': 0,
            'anti_bot_encounters': 0,
            'captcha_encounters': 0,
            'proxy_rotations': 0,
            'session_rotations': 0,
            # Add these new metrics
            'residential_proxy_success': 0,
            'mobile_proxy_success': 0,
            'residential_proxy_failures': 0,
            'mobile_proxy_failures': 0,
            'bypass_attempts': 0,
            'bypass_successes': 0,
            'fingerprint_rotations': 0,
            'html_saves': 0,
            'vision_analysis_calls': 0
        }

    def generate_test_urls(self, count: int = 100) -> List[str]:
        """Generate comprehensive test URLs for SimilarWeb"""
        base_domains = [
            # Tech Giants & Platforms (20)
            "google.com", "youtube.com", "facebook.com", "amazon.com", "microsoft.com",
            "apple.com", "netflix.com", "twitter.com", "instagram.com", "linkedin.com",
            "tiktok.com", "snapchat.com", "discord.com", "reddit.com", "pinterest.com",
            "whatsapp.com", "telegram.org", "zoom.us", "skype.com", "viber.com",
            
            # E-commerce & Marketplace (15)
            "shopify.com", "ebay.com", "etsy.com", "alibaba.com", "aliexpress.com",
            "walmart.com", "target.com", "bestbuy.com", "homedepot.com", "costco.com",
            "ikea.com", "nike.com", "adidas.com", "zara.com", "hm.com",
            
            # Software & Development (15)
            "github.com", "stackoverflow.com", "adobe.com", "salesforce.com", "oracle.com",
            "ibm.com", "slack.com", "dropbox.com", "notion.so", "figma.com",
            "canva.com", "atlassian.com", "asana.com", "trello.com", "jira.com",
            
            # Media & Content (10)
            "wikipedia.org", "medium.com", "wordpress.com", "blogger.com", "tumblr.com",
            "quora.com", "buzzfeed.com", "huffpost.com", "cnn.com", "bbc.com",
            
            # Finance & Crypto (10)
            "paypal.com", "stripe.com", "square.com", "coinbase.com", "robinhood.com",
            "binance.com", "kraken.com", "chase.com", "bankofamerica.com", "wellsfargo.com",
            
            # Travel & Services (10)
            "booking.com", "expedia.com", "airbnb.com", "uber.com", "lyft.com",
            "tripadvisor.com", "kayak.com", "priceline.com", "hotels.com", "marriott.com",
            
            # Entertainment & Gaming (10)
            "spotify.com", "soundcloud.com", "twitch.tv", "steam.com", "epicgames.com",
            "roblox.com", "minecraft.net", "ea.com", "activision.com", "ubisoft.com",
            
            # News & Information (10)
            "nytimes.com", "wsj.com", "reuters.com", "bloomberg.com", "forbes.com",
            "techcrunch.com", "theverge.com", "wired.com", "arstechnica.com", "mashable.com"
        ]
        selected_domains = random.sample(base_domains, min(count, len(base_domains)))
        test_urls = [f"https://www.similarweb.com/website/{domain}/" for domain in selected_domains]
        
        random.shuffle(test_urls)
        return test_urls[:count]

    async def test_single_url(self, url: str, test_number: int, total_tests: int) -> SimilarWebTestResult:
        """Test scraping with existing browser session"""
        result = SimilarWebTestResult()
        result.url = url
        result.domain = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        
        logger.info(f"\n🎯 Test {test_number}/{total_tests}: {result.domain}")
        
        start_time = time.time()
        
        # ✅ CHANGE: Use existing browser instead of creating new one
        try:
            browser = self.current_browser  # Use existing browser
            
            result.fingerprint_profile = browser.current_fingerprint_profile['name']
            result.proxy_used = getattr(browser, 'proxy', {}).get('server', 'None') if hasattr(browser, 'proxy') else 'None'
            
            logger.info(f"🎭 Profile: {result.fingerprint_profile}")
            logger.info(f"🔄 Proxy: {result.proxy_used}")
            
            # Navigation phase
            nav_start = time.time()
            nav_success = await browser.smart_navigate(url)
            result.navigation_time = time.time() - nav_start
            result.attempts = 1
            
            if not nav_success:
                result.error = "Smart navigation failed"
                logger.error("❌ Navigation failed")
                return result
            
            logger.info(f"✅ Navigation successful ({result.navigation_time:.1f}s)")
            
            # Handle popups
            popup_handled = await browser.handle_similarweb_popups()
            logger.info(f"🔍 Popup handling: {'✅ Success' if popup_handled else '⚠️ No popups'}")
            
            # Extraction phase  
            extract_start = time.time()
            extracted_data = await browser.extract_similarweb_data_with_vision(url)
            result.extraction_time = time.time() - extract_start
            
            if extracted_data.get('extraction_success', False):
                result.success = True
                result.extraction_success = True
                result.data_extracted = extracted_data
                
                # Extract metrics found
                metrics = extracted_data.get('data', {})
                result.metrics_found = [k for k, v in metrics.items() if v and v != 'null']
                result.confidence_score = extracted_data.get('confidence_scores', {}).get('primary', 0.0)
                
                logger.info(f"✅ Extraction successful ({result.extraction_time:.1f}s)")
                logger.info(f"📊 Metrics found: {result.metrics_found}")
                
                self.stats['successful_extractions'] += 1

                
            else:
                result.error = extracted_data.get('error', 'Data extraction failed')
                logger.warning(f"❌ Extraction failed: {result.error}")
            
            self.stats['successful_navigations'] += 1
            
        except Exception as e:
            result.error = str(e)
            logger.error(f"❌ Test failed with exception: {e}")
        
        result.total_time = time.time() - start_time
        self.stats['total_attempts'] += 1
        
        return result

    async def test_single_url_fresh(self, url: str, test_number: int, total_tests: int, browser) -> SimilarWebTestResult:
        """Test scraping with fresh browser instance"""
        result = SimilarWebTestResult()
        result.url = url
        result.domain = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        
        logger.info(f"\n🎯 Test {test_number}/{total_tests}: {result.domain} (Fresh Browser)")
        
        start_time = time.time()
        
        try:
            result.fingerprint_profile = browser.current_fingerprint_profile['name']
            result.proxy_used = getattr(browser, 'proxy', {}).get('server', 'None') if hasattr(browser, 'proxy') else 'None'
            # After getting proxy info
            if result.proxy_used != 'None':
                proxy_type = 'mobile' if 'mobile' in result.proxy_used.lower() else 'residential'
                if result.success:
                    self.stats[f'{proxy_type}_proxy_success'] += 1
                else:
                    self.stats[f'{proxy_type}_proxy_failures'] += 1
            
            logger.info(f"🎭 Fresh Profile: {result.fingerprint_profile}")
            logger.info(f"🔄 Fresh Proxy: {result.proxy_used}")
            
            # Navigation phase
            nav_start = time.time()
            nav_success = await browser.smart_navigate(url)
            result.navigation_time = time.time() - nav_start
            result.attempts = 1
            
            if not nav_success:
                result.error = "Smart navigation failed"
                logger.error("❌ Navigation failed")
                return result
            
            logger.info(f"✅ Navigation successful ({result.navigation_time:.1f}s)")
            
            # Handle popups
            popup_handled = await browser.handle_similarweb_popups()
            logger.info(f"🔍 Popup handling: {'✅ Success' if popup_handled else '⚠️ No popups'}")
            
            # Extraction phase  
            extract_start = time.time()
            extracted_data = await browser.extract_similarweb_data_with_vision(url)
            result.extraction_time = time.time() - extract_start
            
            if extracted_data.get('extraction_success', False):
                result.success = True
                result.extraction_success = True
                result.data_extracted = extracted_data
                
                # Extract metrics found
                metrics = extracted_data.get('data', {})
                result.metrics_found = [k for k, v in metrics.items() if v and v != 'null']
                result.confidence_score = extracted_data.get('confidence_scores', {}).get('primary', 0.0)
                
                logger.info(f"✅ Extraction successful ({result.extraction_time:.1f}s)")
                logger.info(f"📊 Metrics found: {result.metrics_found}")
                
                self.stats['successful_extractions'] += 1
                if extracted_data.get('extraction_success', False):
                    # Save HTML
                    await self._save_page_html(browser, result.domain, url)

            else:
                result.error = extracted_data.get('error', 'Data extraction failed')
                logger.warning(f"❌ Extraction failed: {result.error}")
            
            self.stats['successful_navigations'] += 1
            
        except Exception as e:
            result.error = str(e)
            logger.error(f"❌ Test failed with exception: {e}")
        
        result.total_time = time.time() - start_time
        self.stats['total_attempts'] += 1
        
        return result

    async def _save_page_html(self, browser, domain: str, url: str):
        """Save HTML content of successfully scraped page"""
        try:
            # Create output directory
            html_dir = Path("scraped_html")
            html_dir.mkdir(exist_ok=True)
            
            # Get page content
            html_content = await browser.page.content()
            
            # Clean domain name for filename
            clean_domain = re.sub(r'[^a-zA-Z0-9_-]', '_', domain)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{clean_domain}_{timestamp}.html"
            
            # Save HTML
            html_file = html_dir / filename
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"💾 Saved HTML: {html_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save HTML for {domain}: {e}")
    async def run_comprehensive_test(self, num_urls: int = 100) -> Dict:
        """Run comprehensive test with fresh browser for each URL"""
        logger.info(f"🚀 Starting fresh browser approach test with {num_urls} URLs")
        
        test_urls = self.generate_test_urls(num_urls)
        results = []
        
        test_start_time = time.time()
        
        for i, url in enumerate(test_urls, 1):
            try:
                # ✅ ALWAYS create fresh browser for each test
                logger.info(f"🔄 Creating fresh browser session for test {i}")
                
                # Get new proxy for this test
                proxy = self._get_proxy_for_session() if self.use_proxies else None
                
                # Create completely new browser instance
                browser = EnhancedSmartBrowserController(
                    headless=self.headless,
                    proxy=proxy,
                    enable_streaming=False
                )
                
                # Start fresh browser session
                await browser.__aenter__()
                
                # Test with fresh browser
                result = await self.test_single_url_fresh(url, i, len(test_urls), browser)
                results.append(result)
                
                # ✅ ALWAYS close browser after each test
                logger.info(f"🗑️ Closing browser session for test {i}")
                await browser.__aexit__(None, None, None)
                
                # Update stats
                self.stats['session_rotations'] += 1
                
                # Realistic delay between tests (fresh user sessions)
                if i < len(test_urls):
                    delay = random.uniform(30, 120)  # 30-120 seconds between fresh sessions
                    logger.info(f"⏱️ Fresh session delay: {delay:.1f}s")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"❌ Test {i} failed: {e}")
                results.append(self._create_error_result(url, str(e)))
        
        # Clean up final session
        if hasattr(self, 'current_browser') and self.current_browser:
            await self.current_browser.__aexit__(None, None, None)
        
        total_test_time = time.time() - test_start_time
        
        # Analysis and saving (keep existing code)
        analysis = self.analyze_results(results, total_test_time)
        failure_analysis = self.analyze_failures(results)
        self.save_comprehensive_results(results, analysis, failure_analysis)
        
        return {
            'results': results,
            'analysis': analysis,
            'failure_analysis': failure_analysis,
            'total_time': total_test_time
        }

    def _should_rotate_session(self) -> bool:
        """Check if current session should be rotated"""
        if not self.current_browser:
            return True
        
        # Check fingerprint evasion session
        if self.current_browser.fingerprint_evasion.should_end_session():
            return True
        
        # Rotate after too many requests in session
        if self.requests_in_session > 12:
            return True
        
        # Rotate after session duration
        if self.session_start_time and (time.time() - self.session_start_time) > 3600:  # 1 hour
            return True
        
        return False

    def _get_proxy_for_session(self):
        """Get proxy for new session - don't rotate too frequently"""
        proxy_info = self.proxy_manager.get_best_proxy(exclude_blocked_for="similarweb.com")
        if proxy_info:
            return proxy_info.to_playwright_dict()
        return None

    def _create_error_result(self, url: str, error: str) -> SimilarWebTestResult:
        """Create error result object"""
        result = SimilarWebTestResult()
        result.url = url
        result.domain = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        result.success = False
        result.error = error
        result.total_time = 0
        return result

    def analyze_results(self, results: List[SimilarWebTestResult], total_time: float) -> Dict:
        """Comprehensive results analysis"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        successful_extractions = sum(1 for r in results if r.extraction_success)
        
        # Calculate all possible metrics coverage
        all_metrics = set()
        for result in results:
            if result.data_extracted.get('data'):
                all_metrics.update(result.data_extracted['data'].keys())
        
        metric_coverage = {}
        for metric in all_metrics:
            coverage_count = sum(1 for r in results 
                            if metric in r.metrics_found)
            metric_coverage[metric] = {
                'found_count': coverage_count,
                'coverage_rate': coverage_count / total_tests * 100 if total_tests > 0 else 0
            }
        
        # Proxy performance analysis
        proxy_performance = {}
        for result in results:
            proxy = result.proxy_used
            if proxy not in proxy_performance:
                proxy_performance[proxy] = {'total': 0, 'success': 0, 'avg_time': 0}
            
            proxy_performance[proxy]['total'] += 1
            if result.success:
                proxy_performance[proxy]['success'] += 1
            proxy_performance[proxy]['avg_time'] += result.total_time
        
        # Calculate success rates and average times
        for proxy, stats in proxy_performance.items():
            stats['success_rate'] = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
            stats['avg_time'] = stats['avg_time'] / stats['total'] if stats['total'] > 0 else 0
        
        # Add proxy type analysis
        proxy_type_performance = {
            'residential': {
                'total_attempts': self.stats['residential_proxy_success'] + self.stats['residential_proxy_failures'],
                'successes': self.stats['residential_proxy_success'],
                'success_rate': 0
            },
            'mobile': {
                'total_attempts': self.stats['mobile_proxy_success'] + self.stats['mobile_proxy_failures'], 
                'successes': self.stats['mobile_proxy_success'],
                'success_rate': 0
            }
        }
        
        for proxy_type in proxy_type_performance:
            total = proxy_type_performance[proxy_type]['total_attempts']
            if total > 0:
                proxy_type_performance[proxy_type]['success_rate'] = \
                    (proxy_type_performance[proxy_type]['successes'] / total) * 100
        
        # ✅ FIXED: Return the complete analysis dictionary
        return {
            'total_tests': total_tests,
            'successful_navigations': successful_tests,
            'successful_extractions': successful_extractions,
            'navigation_success_rate': (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            'extraction_success_rate': (successful_extractions / total_tests) * 100 if total_tests > 0 else 0,
            'overall_success_rate': (successful_extractions / total_tests) * 100 if total_tests > 0 else 0,
            'metric_coverage': metric_coverage,
            'proxy_performance': proxy_performance,
            'proxy_type_performance': proxy_type_performance,  # ✅ ADDED HERE
            'average_time_per_test': total_time / total_tests if total_tests > 0 else 0,
            'total_test_time': total_time,
            'test_stats': self.stats,
            'html_files_saved': self.stats.get('html_saves', 0)  # ✅ ADDED HERE
        }

    def analyze_failures(self, results: List[SimilarWebTestResult]) -> Dict:
        """Detailed failure pattern analysis"""
        failures = [r for r in results if not r.success]
        
        failure_analysis = {
            'total_failures': len(failures),
            'failure_rate': (len(failures) / len(results)) * 100 if results else 0,
            'failure_types': {},
            'proxy_failures': {},
            'fingerprint_failures': {},
            'error_patterns': {},
            'time_based_failures': {},
            'recommendations': []
        }
        
        for result in failures:
            # Categorize error types
            error = result.error.lower()
            if 'navigation' in error:
                failure_analysis['failure_types']['navigation'] = failure_analysis['failure_types'].get('navigation', 0) + 1
            elif 'extraction' in error:
                failure_analysis['failure_types']['extraction'] = failure_analysis['failure_types'].get('extraction', 0) + 1
            elif 'timeout' in error:
                failure_analysis['failure_types']['timeout'] = failure_analysis['failure_types'].get('timeout', 0) + 1
            elif 'proxy' in error or 'connection' in error:
                failure_analysis['failure_types']['proxy'] = failure_analysis['failure_types'].get('proxy', 0) + 1
            else:
                failure_analysis['failure_types']['other'] = failure_analysis['failure_types'].get('other', 0) + 1
            
            # Track proxy-specific failures
            proxy = result.proxy_used
            failure_analysis['proxy_failures'][proxy] = failure_analysis['proxy_failures'].get(proxy, 0) + 1
            
            # Track fingerprint-specific failures
            fp = result.fingerprint_profile
            failure_analysis['fingerprint_failures'][fp] = failure_analysis['fingerprint_failures'].get(fp, 0) + 1
            
            # Track specific error messages
            failure_analysis['error_patterns'][result.error] = failure_analysis['error_patterns'].get(result.error, 0) + 1
        
        # Generate recommendations
        total_tests = len(results)
        if failure_analysis['failure_types'].get('navigation', 0) > total_tests * 0.3:
            failure_analysis['recommendations'].append("High navigation failure rate - consider increasing delays or rotating proxies more frequently")
        
        if failure_analysis['failure_types'].get('proxy', 0) > total_tests * 0.2:
            failure_analysis['recommendations'].append("Proxy issues detected - consider refreshing proxy pool or using different proxy provider")
        
        if failure_analysis['failure_types'].get('timeout', 0) > total_tests * 0.15:
            failure_analysis['recommendations'].append("Timeout issues - consider increasing timeout values or optimizing network conditions")
        
        return failure_analysis

    def save_comprehensive_results(self, results: List[SimilarWebTestResult], analysis: Dict, failure_analysis: Dict):
        """Save comprehensive test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)
        
        # Save detailed JSON results
        json_file = results_dir / f"similarweb_comprehensive_{timestamp}.json"
        json_data = []
        
        for result in results:
            json_data.append({
                'url': result.url,
                'domain': result.domain,
                'success': result.success,
                'extraction_success': result.extraction_success,
                'error': result.error,
                'anti_bot_detected': result.anti_bot_detected,
                'anti_bot_type': result.anti_bot_type,
                'proxy_used': result.proxy_used,
                'fingerprint_profile': result.fingerprint_profile,
                'total_time': result.total_time,
                'navigation_time': result.navigation_time,
                'extraction_time': result.extraction_time,
                'metrics_found': result.metrics_found,
                'confidence_score': result.confidence_score,
                'page_validated': result.page_validated,
                'timestamp': result.timestamp
            })
        
        with open(json_file, 'w') as f:
            json.dump({
                'test_configuration': {
                    'total_urls': len(results),
                    'use_proxies': self.use_proxies,
                    'headless': self.headless,
                    'timestamp': timestamp
                },
                'analysis': analysis,
                'failure_analysis': failure_analysis,
                'detailed_results': json_data
            }, f, indent=2)
        
        # Save detailed CSV
        csv_file = results_dir / f"similarweb_detailed_{timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Domain', 'URL', 'Success', 'Extraction_Success', 'Error', 
                'Proxy', 'Fingerprint', 'Total_Time', 'Navigation_Time', 'Extraction_Time',
                'Metrics_Found', 'Confidence_Score', 'Page_Validated'
            ])
            
            for result in results:
                writer.writerow([
                    result.domain,
                    result.url,
                    result.success,
                    result.extraction_success,
                    result.error,
                    result.proxy_used,
                    result.fingerprint_profile,
                    f"{result.total_time:.2f}",
                    f"{result.navigation_time:.2f}",
                    f"{result.extraction_time:.2f}",
                    '; '.join(result.metrics_found),
                    f"{result.confidence_score:.3f}",
                    result.page_validated
                ])
        
        logger.info(f"📄 Comprehensive results saved to:")
        logger.info(f"  📊 JSON: {json_file}")
        logger.info(f"  📈 CSV: {csv_file}")
        
        # Print comprehensive summary
        self.print_comprehensive_summary(analysis, failure_analysis)

    def print_comprehensive_summary(self, analysis: Dict, failure_analysis: Dict):
        """Print detailed test summary"""
        print(f"\n" + "="*80)
        print(f"📊 SIMILARWEB COMPREHENSIVE TEST RESULTS")
        print(f"="*80)
        print(f"🎯 Total Tests: {analysis['total_tests']}")
        print(f"✅ Successful Navigations: {analysis['successful_navigations']} ({analysis['navigation_success_rate']:.1f}%)")
        print(f"📊 Successful Extractions: {analysis['successful_extractions']} ({analysis['extraction_success_rate']:.1f}%)")
        print(f"🎉 Overall Success Rate: {analysis['overall_success_rate']:.1f}%")
        print(f"⏱️ Average Time per Test: {analysis['average_time_per_test']:.1f}s")
        print(f"🕒 Total Test Time: {analysis['total_test_time']:.1f}s")
        
        print(f"\n📈 METRIC COVERAGE:")
        for metric, coverage in analysis['metric_coverage'].items():
            print(f"   {metric}: {coverage['found_count']}/{analysis['total_tests']} ({coverage['coverage_rate']:.1f}%)")
        
        print(f"\n🔄 PROXY PERFORMANCE:")
        for proxy, stats in analysis['proxy_performance'].items():
            print(f"   {proxy}: {stats['success']}/{stats['total']} ({stats['success_rate']:.1f}%) - Avg: {stats['avg_time']:.1f}s")
        
        print(f"\n❌ FAILURE ANALYSIS:")
        print(f"   Total Failures: {failure_analysis['total_failures']} ({failure_analysis['failure_rate']:.1f}%)")
        print(f"   Failure Types:")
        for fail_type, count in failure_analysis['failure_types'].items():
            print(f"     {fail_type}: {count}")
        
        if failure_analysis['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(failure_analysis['recommendations'], 1):
                print(f"   {i}. {rec}")

async def main():
    """Main test function with enhanced argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SimilarWeb Comprehensive Scraper Test")
    parser.add_argument("--num-urls", type=int, default=100, help="Number of URLs to test (default: 100)")
    parser.add_argument("--no-proxies", action="store_true", help="Disable proxy usage")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    
    # Check environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY environment variable not set!")
        print("Please set your Google AI API key:")
        print("export GOOGLE_API_KEY='your_api_key_here'")
        return
    
    try:
        scraper = SimilarWebScraper(
            use_proxies=not args.no_proxies,
            headless=args.headless
        )
        
        await scraper.run_comprehensive_test(args.num_urls)
        
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

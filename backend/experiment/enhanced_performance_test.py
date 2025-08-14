# #!/usr/bin/env python3
# """
# Enhanced Performance Test Runner for Unbeatable Scraper
# Tests 100+ URLs with advanced anti-bot evasion and detailed analytics
# """

# import asyncio
# import json
# import csv
# import time
# import random
# import logging
# from datetime import datetime
# from pathlib import Path
# from typing import List, Dict, Optional
# import sys
# import os

# # Import your enhanced components
# from run_agent import UnbeatableScraper, STEALTH_CONFIG, RELIABILITY_CONFIG
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('performance_test.log'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# class EnhancedPerformanceTest:
#     def __init__(self, config_type: str = "stealth"):
#         """Initialize with different configuration profiles"""
#         self.configs = {
#             "stealth": STEALTH_CONFIG,
#             "reliability": RELIABILITY_CONFIG,
#             "speed": {
#                 "headless": True,
#                 "use_proxies": False,
#                 "bypass_403": False,
#                 "solve_captchas": False,
#                 "fingerprint_rotation_interval": 3600
#             }
#         }
        
#         self.config = self.configs.get(config_type, STEALTH_CONFIG)
#         self.scraper = UnbeatableScraper(self.config)
#         self.results = []
        
#     async def run_comprehensive_test(self, 
#                                    urls: List[str], 
#                                    goals: List[str] = None,
#                                    output_formats: List[str] = None) -> Dict:
#         """Run comprehensive performance test on multiple URLs"""
        
#         logger.info(f"🚀 Starting Enhanced Performance Test")
#         logger.info(f"📊 Testing {len(urls)} URLs")
#         logger.info(f"🔧 Configuration: {self.config}")
        
#         if goals is None:
#             goals = ["Extract all visible content and data"] * len(urls)
#         if output_formats is None:
#             output_formats = ["json"] * len(urls)
            
#         start_time = time.time()
#         results = []
        
#         for i, (url, goal, fmt) in enumerate(zip(urls, goals, output_formats), 1):
#             logger.info(f"\n🎯 Test {i}/{len(urls)}: {url}")
            
#             test_start = time.time()
            
#             try:
#                 result = await self.scraper.scrape(
#                     url=url,
#                     goal=goal,
#                     output_format=fmt
#                 )
                
#                 # Enhanced result tracking
#                 enhanced_result = {
#                     "test_number": i,
#                     "url": url,
#                     "goal": goal,
#                     "format": fmt,
#                     "success": result["success"],
#                     "total_time": time.time() - test_start,
#                     "data_size": len(str(result.get("data", ""))) if result.get("data") else 0,
#                     "metadata": result.get("metadata", {}),
#                     "errors": result.get("errors", []),
#                     "proxy_rotations": self.scraper.stats.get("proxies_rotated", 0),
#                     "fingerprint_rotations": self.scraper.stats.get("fingerprints_rotated", 0),
#                     "bypasses_used": self.scraper.stats.get("bypasses_used", 0),
#                     "captchas_solved": self.scraper.stats.get("captchas_solved", 0),
#                     "anti_bot_encounters": self.scraper.stats.get("anti_bot_encounters", 0),
#                     "timestamp": time.time()
#                 }
                
#                 results.append(enhanced_result)
                
#                 # Progress logging
#                 success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
#                 logger.info(f"✅ Success: {enhanced_result['success']}")
#                 logger.info(f"⏱️  Time: {enhanced_result['total_time']:.1f}s")
#                 logger.info(f"📊 Success Rate: {success_rate:.1f}% ({sum(1 for r in results if r['success'])}/{len(results)})")
                
#             except Exception as e:
#                 enhanced_result = {
#                     "test_number": i,
#                     "url": url,
#                     "success": False,
#                     "total_time": time.time() - test_start,
#                     "errors": [str(e)],
#                     "timestamp": time.time()
#                 }
#                 results.append(enhanced_result)
#                 logger.error(f"❌ Test failed: {e}")
            
#             # Intelligent delay
#             if i < len(urls):
#                 delay = self._calculate_delay(enhanced_result, i, len(results))
#                 logger.info(f"⏱️ Waiting {delay:.1f}s before next test...")
#                 await asyncio.sleep(delay)
        
#         total_time = time.time() - start_time
        
#         # Comprehensive analysis
#         analysis = self._analyze_performance(results, total_time)
        
#         # Save results
#         self._save_results(results, analysis)
        
#         return {
#             "results": results,
#             "analysis": analysis,
#             "total_time": total_time,
#             "scraper_stats": self.scraper.stats
#         }
    
#     def _calculate_delay(self, result: Dict, current_test: int, total_results: int) -> float:
#         """Calculate intelligent delay based on success/failure patterns"""
#         base_delay = random.uniform(5, 15)
        
#         # Increase delay after failures
#         if not result["success"]:
#             base_delay *= random.uniform(2, 4)
        
#         # Reduce delay for consecutive successes
#         recent_results = total_results  # Last 5 results
#         # if len(recent_results) >= 3:
#         #     recent_successes = sum(1 for r in recent_results if r.get("success", False))
#         #     if recent_successes >= 3:
#         #         base_delay *= 0.7
        
#         # Add randomization to avoid patterns
#         return base_delay + random.uniform(0, 5)
    
#     def _analyze_performance(self, results: List[Dict], total_time: float) -> Dict:
#         """Comprehensive performance analysis"""
#         successful = [r for r in results if r["success"]]
#         failed = [r for r in results if not r["success"]]
        
#         analysis = {
#             "summary": {
#                 "total_tests": len(results),
#                 "successful": len(successful),
#                 "failed": len(failed),
#                 "success_rate": (len(successful) / len(results) * 100) if results else 0,
#                 "total_time": total_time,
#                 "avg_time_per_test": total_time / len(results) if results else 0
#             },
#             "timing_analysis": {
#                 "fastest_success": min([r["total_time"] for r in successful]) if successful else 0,
#                 "slowest_success": max([r["total_time"] for r in successful]) if successful else 0,
#                 "avg_success_time": sum([r["total_time"] for r in successful]) / len(successful) if successful else 0,
#                 "avg_failure_time": sum([r["total_time"] for r in failed]) / len(failed) if failed else 0
#             },
#             "evasion_effectiveness": {
#                 "total_proxy_rotations": sum([r.get("proxy_rotations", 0) for r in results]),
#                 "total_fingerprint_rotations": sum([r.get("fingerprint_rotations", 0) for r in results]),
#                 "total_bypasses_used": sum([r.get("bypasses_used", 0) for r in results]),
#                 "total_captchas_solved": sum([r.get("captchas_solved", 0) for r in results]),
#                 "anti_bot_encounter_rate": sum([r.get("anti_bot_encounters", 0) for r in results]) / len(results) * 100 if results else 0
#             },
#             "data_extraction": {
#                 "total_data_extracted": sum([r.get("data_size", 0) for r in successful]),
#                 "avg_data_per_success": sum([r.get("data_size", 0) for r in successful]) / len(successful) if successful else 0,
#                 "largest_extraction": max([r.get("data_size", 0) for r in successful]) if successful else 0
#             },
#             "failure_analysis": self._analyze_failures(failed),
#             "recommendations": self._generate_recommendations(results, successful, failed)
#         }
        
#         return analysis
    
#     def _analyze_failures(self, failed_results: List[Dict]) -> Dict:
#         """Analyze failure patterns"""
#         if not failed_results:
#             return {"no_failures": True}
        
#         error_patterns = {}
#         for result in failed_results:
#             for error in result.get("errors", []):
#                 error_type = self._categorize_error(error)
#                 error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
        
#         return {
#             "total_failures": len(failed_results),
#             "error_patterns": error_patterns,
#             "most_common_error": max(error_patterns.items(), key=lambda x: x[1])[0] if error_patterns else None
#         }
    
#     def _categorize_error(self, error: str) -> str:
#         """Categorize error types"""
#         error_lower = error.lower()
#         if "timeout" in error_lower:
#             return "timeout"
#         elif "navigation" in error_lower:
#             return "navigation"
#         elif "proxy" in error_lower or "connection" in error_lower:
#             return "proxy"
#         elif "captcha" in error_lower:
#             return "captcha"
#         elif "blocked" in error_lower or "403" in error_lower:
#             return "blocked"
#         else:
#             return "other"
    
#     def _generate_recommendations(self, all_results: List[Dict], successful: List[Dict], failed: List[Dict]) -> List[str]:
#         """Generate optimization recommendations"""
#         recommendations = []
        
#         if len(failed) > len(successful):
#             recommendations.append("High failure rate detected - consider using RELIABILITY_CONFIG")
        
#         if sum([r.get("anti_bot_encounters", 0) for r in all_results]) > len(all_results) * 0.3:
#             recommendations.append("High anti-bot encounter rate - increase fingerprint rotation frequency")
        
#         avg_time = sum([r["total_time"] for r in successful]) / len(successful) if successful else 0
#         if avg_time > 30:
#             recommendations.append("Slow average response time - consider optimizing proxy selection")
        
#         proxy_rotations = sum([r.get("proxy_rotations", 0) for r in all_results])
#         if proxy_rotations < len(all_results) * 0.1:
#             recommendations.append("Low proxy rotation - consider more aggressive proxy rotation")
        
#         return recommendations
    
#     def _save_results(self, results: List[Dict], analysis: Dict):
#         """Save comprehensive results"""
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
#         # Create results directory
#         results_dir = Path("performance_results")
#         results_dir.mkdir(exist_ok=True)
        
#         # Save JSON results
#         json_file = results_dir / f"enhanced_performance_{timestamp}.json"
#         with open(json_file, 'w') as f:
#             json.dump({
#                 "test_configuration": self.config,
#                 "analysis": analysis,
#                 "detailed_results": results,
#                 "scraper_stats": self.scraper.stats
#             }, f, indent=2)
        
#         # Save CSV summary
#         csv_file = results_dir / f"performance_summary_{timestamp}.csv"
#         with open(csv_file, 'w', newline='') as f:
#             writer = csv.writer(f)
#             writer.writerow([
#                 'Test_Number', 'URL', 'Success', 'Total_Time', 'Data_Size',
#                 'Proxy_Rotations', 'Fingerprint_Rotations', 'Bypasses_Used', 
#                 'Captchas_Solved', 'Errors'
#             ])
            
#             for result in results:
#                 writer.writerow([
#                     result.get('test_number', ''),
#                     result.get('url', ''),
#                     result.get('success', False),
#                     f"{result.get('total_time', 0):.2f}",
#                     result.get('data_size', 0),
#                     result.get('proxy_rotations', 0),
#                     result.get('fingerprint_rotations', 0),
#                     result.get('bypasses_used', 0),
#                     result.get('captchas_solved', 0),
#                     '; '.join(result.get('errors', []))
#                 ])
        
#         logger.info(f"📄 Results saved:")
#         logger.info(f"  📊 JSON: {json_file}")
#         logger.info(f"  📈 CSV: {csv_file}")
        
#         # Print summary
#         self._print_summary(analysis)
    
#     def _print_summary(self, analysis: Dict):
#         """Print comprehensive summary"""
#         print(f"\n" + "="*80)
#         print(f"📊 ENHANCED PERFORMANCE TEST RESULTS")
#         print(f"="*80)
        
#         summary = analysis["summary"]
#         print(f"🎯 Total Tests: {summary['total_tests']}")
#         print(f"✅ Successful: {summary['successful']} ({summary['success_rate']:.1f}%)")
#         print(f"❌ Failed: {summary['failed']}")
#         print(f"⏱️ Total Time: {summary['total_time']:.1f}s")
#         print(f"📈 Avg Time per Test: {summary['avg_time_per_test']:.1f}s")
        
#         timing = analysis["timing_analysis"]
#         print(f"\n⏱️ TIMING ANALYSIS:")
#         print(f"  Fastest Success: {timing['fastest_success']:.1f}s")
#         print(f"  Slowest Success: {timing['slowest_success']:.1f}s")
#         print(f"  Avg Success Time: {timing['avg_success_time']:.1f}s")
        
#         evasion = analysis["evasion_effectiveness"]
#         print(f"\n🛡️ EVASION EFFECTIVENESS:")
#         print(f"  Proxy Rotations: {evasion['total_proxy_rotations']}")
#         print(f"  Fingerprint Rotations: {evasion['total_fingerprint_rotations']}")
#         print(f"  Bypasses Used: {evasion['total_bypasses_used']}")
#         print(f"  CAPTCHAs Solved: {evasion['total_captchas_solved']}")
#         print(f"  Anti-bot Encounter Rate: {evasion['anti_bot_encounter_rate']:.1f}%")
        
#         if analysis["recommendations"]:
#             print(f"\n💡 RECOMMENDATIONS:")
#             for i, rec in enumerate(analysis["recommendations"], 1):
#                 print(f"  {i}. {rec}")

# def generate_diverse_test_urls(count: int = 100) -> List[str]:
#     """Generate diverse URLs for comprehensive testing"""
    
#     categories = {
#         "tech_giants": [
#             "google.com", "youtube.com", "facebook.com", "amazon.com", 
#             "microsoft.com", "apple.com", "netflix.com", "twitter.com"
#         ],
#         "ecommerce": [
#             "shopify.com", "ebay.com", "etsy.com", "walmart.com", 
#             "target.com", "bestbuy.com", "alibaba.com"
#         ],
#         "news_media": [
#             "cnn.com", "bbc.com", "nytimes.com", "reuters.com", 
#             "techcrunch.com", "theverge.com", "wired.com"
#         ],
#         "social_platforms": [
#             "linkedin.com", "instagram.com", "tiktok.com", "reddit.com", 
#             "pinterest.com", "discord.com", "telegram.org"
#         ],
#         "development_tools": [
#             "github.com", "stackoverflow.com", "gitlab.com", 
#             "bitbucket.org", "codepen.io", "replit.com"
#         ]
#     }
    
#     # Distribute URLs across categories
#     urls_per_category = count // len(categories)
#     test_urls = []
    
#     for category, domains in categories.items():
#         category_urls = random.sample(domains, min(urls_per_category, len(domains)))
#         for domain in category_urls:
#             # Mix direct access and SimilarWeb analysis
#             if random.random() < 0.3:  # 30% direct access
#                 test_urls.append(f"https://www.{domain}")
#             else:  # 70% SimilarWeb analysis
#                 test_urls.append(f"https://www.similarweb.com/website/{domain}/")
    
#     # Fill remaining slots
#     remaining = count - len(test_urls)
#     if remaining > 0:
#         all_domains = [d for domains in categories.values() for d in domains]
#         extra_domains = random.sample(all_domains, remaining)
#         for domain in extra_domains:
#             test_urls.append(f"https://www.{domain}")
    
#     random.shuffle(test_urls)
#     return test_urls[:count]

# async def main():
#     """Main execution function"""
#     import argparse
    
#     parser = argparse.ArgumentParser(description="Enhanced Performance Test for Unbeatable Scraper")
#     parser.add_argument("--num-urls", type=int, default=100, help="Number of URLs to test")
#     parser.add_argument("--config", choices=["stealth", "reliability", "speed"], 
#                        default="stealth", help="Configuration profile")
#     parser.add_argument("--custom-urls", type=str, help="File with custom URLs (one per line)")
    
#     args = parser.parse_args()
#     args.num_urls = 10
#     args.config = "stealth"  # Ensure at least 1 URL
#     # Check environment
#     if not os.getenv("GOOGLE_API_KEY"):
#         print("❌ ERROR: GOOGLE_API_KEY environment variable not set!")
#         return
    
#     try:
#         # Initialize test
#         test_runner = EnhancedPerformanceTest(args.config)
        
#         # Load URLs
#         if args.custom_urls and Path(args.custom_urls).exists():
#             with open(args.custom_urls, 'r') as f:
#                 urls = [line.strip() for line in f if line.strip()]
#         else:
#             urls = generate_diverse_test_urls(args.num_urls)
        
#         # Run comprehensive test
#         results = await test_runner.run_comprehensive_test(urls)
        
#         print(f"\n🎉 Enhanced performance test completed!")
#         print(f"📊 Overall Success Rate: {results['analysis']['summary']['success_rate']:.1f}%")
        
#     except KeyboardInterrupt:
#         logger.info("🛑 Test interrupted by user")
#     except Exception as e:
#         logger.error(f"❌ Test failed: {e}")
#         raise

# if __name__ == "__main__":
#     asyncio.run(main())



#!/usr/bin/env python3
"""
Enhanced SimilarWeb Scraper Test Runner - Ultra-Dynamic Version
Tests 100 URLs with complete fingerprinting, proxy rotation, and bypass techniques
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
import base64
from collections import defaultdict
from urllib.parse import urlparse

from playwright.async_api import async_playwright
from smart_browser_controller import EnhancedSmartBrowserController
from proxy_manager import AdvancedProxyManager, ProxyType
from anti_bot_detection import AntiBotVisionModel
from fingerprint_evasion import AdvancedFingerprintEvasion

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('similarweb_test_enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimilarWebExtractor:
    """Basic SimilarWeb data extractor"""
    
    def __init__(self):
        self.vision_model = AntiBotVisionModel()
    
    async def extract_similarweb_data_with_vision(self, browser, url: str) -> Dict:
        """Extract SimilarWeb data using vision approach"""
        try:
            # Take screenshot for analysis
            screenshot_bytes = await browser.page.screenshot(type='png')
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Check if we're on a valid SimilarWeb page
            page_title = await browser.page.title()
            page_url = browser.page.url
            
            # SimilarWeb-specific analysis
            analysis = await self.vision_model.analyze_similarweb_specific(screenshot_b64, page_url)
            
            if analysis.get('is_blocked', False):
                return {
                    'extraction_success': False,
                    'error': f"Page blocked: {analysis.get('block_type', 'unknown')}",
                    'analysis': analysis
                }
            
            # Extract visible metrics from page
            extracted_data = await self._extract_metrics_from_page(browser)
            
            return {
                'extraction_success': True,
                'data': extracted_data,
                'validation_results': {
                    'is_valid_similarweb_page': 'similarweb' in page_url.lower(),
                    'title': page_title
                },
                'confidence_scores': {'primary': 0.8},
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"❌ Vision extraction failed: {e}")
            return {'extraction_success': False, 'error': str(e)}
    
    async def _extract_metrics_from_page(self, browser) -> Dict:
        """Extract metrics from SimilarWeb page"""
        try:
            # Use JavaScript to extract data from page
            data = await browser.page.evaluate("""
                () => {
                    const metrics = {};
                    
                    // Look for global rank
                    const rankElements = document.querySelectorAll('[data-automation*="rank"], .rank, [class*="rank"]');
                    for (const el of rankElements) {
                        if (el.textContent && el.textContent.includes('#')) {
                            metrics.global_rank = el.textContent.trim();
                            break;
                        }
                    }
                    
                    // Look for visits data
                    const visitElements = document.querySelectorAll('[data-automation*="visit"], [class*="visit"], [class*="traffic"]');
                    for (const el of visitElements) {
                        const text = el.textContent;
                        if (text && (text.includes('M') || text.includes('K') || text.includes('B'))) {
                            metrics.total_visits = text.trim();
                            break;
                        }
                    }
                    
                    // Look for bounce rate
                    const bounceElements = document.querySelectorAll('[data-automation*="bounce"], [class*="bounce"]');
                    for (const el of bounceElements) {
                        const text = el.textContent;
                        if (text && text.includes('%')) {
                            metrics.bounce_rate = text.trim();
                            break;
                        }
                    }
                    
                    // Look for page views
                    const pageViewElements = document.querySelectorAll('[data-automation*="page"], [class*="pageview"]');
                    for (const el of pageViewElements) {
                        const text = el.textContent;
                        if (text && /\d+\.\d+/.test(text)) {
                            metrics.pages_per_visit = text.trim();
                            break;
                        }
                    }
                    
                    // Look for visit duration
                    const durationElements = document.querySelectorAll('[data-automation*="duration"], [class*="duration"]');
                    for (const el of durationElements) {
                        const text = el.textContent;
                        if (text && (text.includes(':') || text.includes('min') || text.includes('sec'))) {
                            metrics.avg_visit_duration = text.trim();
                            break;
                        }
                    }
                    
                    return metrics;
                }
            """)
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting metrics: {e}")
            return {}

class EnhancedSimilarWebTestResult:
    """Enhanced test result tracking"""
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
        self.proxy_type = ""
        self.proxy_session_id = ""
        self.fingerprint_profile = ""
        self.fingerprint_hash = ""
        self.attempts = 0
        self.bypass_techniques_used = []
        self.total_time = 0
        self.navigation_time = 0
        self.extraction_time = 0
        self.data_extracted = {}
        self.metrics_found = []
        self.confidence_score = 0.0
        self.page_validated = False
        self.timestamp = time.time()
        self.user_agent_used = ""
        self.headers_used = []

class UltraDynamicSimilarWebScraper:
    """Ultra-Dynamic SimilarWeb Scraper with all enhancements"""
    
    def __init__(self, use_proxies: bool = True, headless: bool = False, 
                 browser_data_path: str = "browsers.json"):
        self.use_proxies = use_proxies
        self.headless = headless
        self.browser_data_path = browser_data_path
        
        # Initialize enhanced components
        self.vision_model = AntiBotVisionModel()
        self.proxy_manager = AdvancedProxyManager(self.vision_model)
        self.extractor = SimilarWebExtractor()
        self.fingerprint_evasion = AdvancedFingerprintEvasion(browser_data_path)
        
        # Results tracking
        self.results = []
        self.stats = {
            'total_attempts': 0,
            'successful_navigations': 0,
            'successful_extractions': 0,
            'anti_bot_encounters': 0,
            'captcha_encounters': 0,
            'proxy_rotations': 0,
            'fingerprint_rotations': 0,
            'bypass_techniques_used': defaultdict(int),
            'unique_fingerprints': set(),
            'unique_proxies': set()
        }
        
        # Performance tracking
        self.performance_tracker = {
            'proxy_performance': defaultdict(lambda: {'success': 0, 'failure': 0}),
            'fingerprint_performance': defaultdict(lambda: {'success': 0, 'failure': 0}),
            'bypass_success': defaultdict(int)
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
        
        # Shuffle and select domains
        selected_domains = random.sample(base_domains, min(count, len(base_domains)))
        test_urls = [f"https://www.similarweb.com/website/{domain}/" for domain in selected_domains]
        
        random.shuffle(test_urls)
        return test_urls[:count]
    
    async def test_single_url(self, url: str, test_number: int, total_tests: int) -> EnhancedSimilarWebTestResult:
        """Test scraping a single URL with ultra-dynamic features"""
        result = EnhancedSimilarWebTestResult()
        result.url = url
        result.domain = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎯 Test {test_number}/{total_tests}: {result.domain}")
        logger.info(f"📍 URL: {url}")
        logger.info(f"{'='*80}")
        
        start_time = time.time()
        
        # Get optimized proxy for SimilarWeb
        proxy = None
        proxy_info = None
        if self.use_proxies:
            proxy_info = self.proxy_manager.get_best_proxy()
            if proxy_info:
                proxy = proxy_info.to_playwright_dict()
                result.proxy_used = proxy.get('server', 'None')
                result.proxy_type = proxy_info.proxy_type.value
                result.proxy_session_id = proxy_info.session_id
                self.stats['unique_proxies'].add(proxy_info.session_id)
                logger.info(f"🔄 Proxy: {result.proxy_used} (Type: {result.proxy_type}, Session: {result.proxy_session_id})")
            else:
                result.proxy_used = 'None - No proxies available'
                logger.warning("⚠️ No proxies available")
        else:
            result.proxy_used = 'Disabled'
        
        try:
            # Initialize browser with ultra-dynamic fingerprinting
            async with EnhancedSmartBrowserController(
                headless=self.headless,
                proxy=proxy,
                enable_streaming=False
            ) as browser:
                # Record fingerprint details
                result.fingerprint_profile = browser.current_fingerprint_profile['name']
                result.fingerprint_hash = browser.current_fingerprint_profile.get('fingerprint_hash', '')[:16]
                result.user_agent_used = browser.current_fingerprint_profile['user_agent'][:100] + "..."
                result.headers_used = list(browser.current_fingerprint_profile.get('headers', {}).keys())
                
                self.stats['unique_fingerprints'].add(result.fingerprint_hash)
                
                logger.info(f"🎭 Fingerprint: {result.fingerprint_profile}")
                logger.info(f"🔐 Hash: {result.fingerprint_hash}")
                logger.info(f"📱 UA: {result.user_agent_used}")
                logger.info(f"📋 Headers: {', '.join(result.headers_used[:5])}")
                
                # Navigation phase with smart bypass
                nav_start = time.time()
                nav_success = await browser.smart_navigate(url)
                result.navigation_time = time.time() - nav_start
                result.attempts = 1
                
                # Track bypass techniques if used
                if hasattr(browser, 'bypass_engine') and browser.bypass_engine.bypass_attempts:
                    result.bypass_techniques_used = browser.bypass_engine.bypass_attempts[-5:]  # Last 5 attempts
                    for technique in result.bypass_techniques_used:
                        self.stats['bypass_techniques_used'][str(technique)] += 1
                
                if not nav_success:
                    result.error = "Smart navigation failed after all bypass attempts"
                    logger.error(f"❌ Navigation failed (Time: {result.navigation_time:.1f}s)")
                    
                    # Mark proxy failure for SimilarWeb
                    if proxy_info:
                        self.proxy_manager.mark_proxy_failure(
                            proxy_info, 
                            site_url=url, 
                            failure_type="navigation"
                        )
                        self.performance_tracker['proxy_performance'][result.proxy_session_id]['failure'] += 1
                    
                    # Mark fingerprint failure
                    self.performance_tracker['fingerprint_performance'][result.fingerprint_hash]['failure'] += 1
                    
                    return result
                
                logger.info(f"✅ Navigation successful ({result.navigation_time:.1f}s)")
                
                # Check for anti-bot detection
                if hasattr(browser, 'proxy_manager'):
                    screenshot_bytes = await browser.page.screenshot(type='png')
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    is_antibot, detection_type, _ = await browser.proxy_manager.detect_anti_bot_with_vision(
                        browser.page, f"scraping {url}"
                    )
                    
                    if is_antibot:
                        result.anti_bot_detected = True
                        result.anti_bot_type = detection_type
                        self.stats['anti_bot_encounters'] += 1
                        logger.warning(f"🚫 Anti-bot detected: {detection_type}")
                
                # Handle popups
                popup_handled = await browser.handle_popups()
                logger.info(f"🔍 Popup handling: {'✅ Success' if popup_handled else '⚠️ No popups'}")
                
                # Extraction phase
                extract_start = time.time()
                extracted_data = await self.extractor.extract_similarweb_data_with_vision(browser, url)
                result.extraction_time = time.time() - extract_start
                
                if extracted_data.get('extraction_success', False):
                    result.success = True
                    result.extraction_success = True
                    result.data_extracted = extracted_data
                    result.page_validated = extracted_data.get('validation_results', {}).get('is_valid_similarweb_page', False)
                    
                    # Extract metrics found
                    metrics = extracted_data.get('data', {})
                    result.metrics_found = [k for k, v in metrics.items() if v and v != 'null']
                    result.confidence_score = extracted_data.get('confidence_scores', {}).get('primary', 0.0)
                    
                    logger.info(f"✅ Extraction successful ({result.extraction_time:.1f}s)")
                    logger.info(f"📊 Metrics found: {', '.join(result.metrics_found)}")
                    logger.info(f"🎯 Confidence: {result.confidence_score:.2f}")
                    
                    self.stats['successful_extractions'] += 1
                    
                    # Mark proxy success for SimilarWeb
                    if proxy_info:
                        self.proxy_manager.mark_proxy_success(
                            proxy_info, 
                            response_time=result.total_time,
                            # site_url=url
                        )
                        self.performance_tracker['proxy_performance'][result.proxy_session_id]['success'] += 1
                    
                    # Mark fingerprint success
                    self.performance_tracker['fingerprint_performance'][result.fingerprint_hash]['success'] += 1
                    
                else:
                    result.error = extracted_data.get('error', 'Data extraction failed')
                    logger.warning(f"⚠️ Extraction failed: {result.error}")
                    
                    # Mark proxy failure for extraction
                    if proxy_info:
                        self.proxy_manager.mark_proxy_failure(
                            proxy_info, 
                            site_url=url, 
                            failure_type="extraction"
                        )
                
                self.stats['successful_navigations'] += 1
                
        except Exception as e:
            result.error = str(e)
            logger.error(f"❌ Test failed with exception: {e}")
            
            # Mark proxy failure
            if proxy_info:
                self.proxy_manager.mark_proxy_failure(
                    proxy_info, 
                    site_url=url, 
                    failure_type="exception"
                )
        
        result.total_time = time.time() - start_time
        self.stats['total_attempts'] += 1
        
        logger.info(f"⏱️ Total time: {result.total_time:.1f}s")
        logger.info(f"📈 Running success rate: {(self.stats['successful_extractions'] / self.stats['total_attempts'] * 100):.1f}%")
        
        return result
    
    async def run_comprehensive_test(self, num_urls: int = 100) -> Dict:
        """Run comprehensive test with ultra-dynamic features"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 ULTRA-DYNAMIC SIMILARWEB TEST SUITE")
        logger.info(f"{'='*80}")
        logger.info(f"📊 Testing {num_urls} URLs")
        logger.info(f"🔄 Using proxies: {self.use_proxies}")
        logger.info(f"🖥️ Headless mode: {self.headless}")
        logger.info(f"📂 Browser data: {self.browser_data_path}")
        logger.info(f"🔌 Total proxies: {len(self.proxy_manager.proxies)}")
        logger.info(f"{'='*80}\n")
        
        test_urls = self.generate_test_urls(num_urls)
        results = []
        
        test_start_time = time.time()
        
        for i, url in enumerate(test_urls, 1):
            result = await self.test_single_url(url, i, len(test_urls))
            results.append(result)
            
            # Export proxy performance periodically
            if i % 10 == 0:
                self.proxy_manager.export_proxy_performance(f"proxy_performance_checkpoint_{i}.json")
            
            # Intelligent delay between requests
            if i < len(test_urls):
                if result.success:
                    # Shorter delay on success with randomization
                    delay = random.uniform(5, 15)
                else:
                    # Longer delay on failure with more randomization
                    delay = random.uniform(15, 35)
                
                # Add extra delay if anti-bot was detected
                if result.anti_bot_detected:
                    delay += random.uniform(10, 20)
                    self.stats['proxy_rotations'] += 1
                
                logger.info(f"\n⏱️ Waiting {delay:.1f}s before next test...")
                await asyncio.sleep(delay)
                
                # Rotate fingerprint periodically
                if i % 5 == 0:
                    self.stats['fingerprint_rotations'] += 1
                    logger.info(f"🔄 Fingerprint rotation #{self.stats['fingerprint_rotations']}")
        
        total_test_time = time.time() - test_start_time
        
        # Comprehensive analysis
        analysis = self.analyze_results(results, total_test_time)
        failure_analysis = self.analyze_failures(results)
        performance_analysis = self.analyze_performance()
        
        # Save all results
        self.save_comprehensive_results(results, analysis, failure_analysis, performance_analysis)
        
        # Export final proxy performance
        self.proxy_manager.export_proxy_performance("proxy_performance_final.json")
        
        return {
            'results': results,
            'analysis': analysis,
            'failure_analysis': failure_analysis,
            'performance_analysis': performance_analysis,
            'total_time': total_test_time
        }
    
    def analyze_results(self, results: List[EnhancedSimilarWebTestResult], total_time: float) -> Dict:
        """Comprehensive results analysis with enhanced metrics"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        successful_extractions = sum(1 for r in results if r.extraction_success)
        
        # Calculate metrics coverage
        all_metrics = set()
        for result in results:
            if result.data_extracted.get('data'):
                all_metrics.update(result.data_extracted['data'].keys())
        
        metric_coverage = {}
        for metric in all_metrics:
            coverage_count = sum(1 for r in results if metric in r.metrics_found)
            metric_coverage[metric] = {
                'found_count': coverage_count,
                'coverage_rate': coverage_count / total_tests * 100 if total_tests > 0 else 0
            }
        
        # Enhanced proxy performance analysis
        proxy_performance = {}
        for session_id, perf in self.performance_tracker['proxy_performance'].items():
            total_attempts = perf['success'] + perf['failure']
            if total_attempts > 0:
                proxy_performance[session_id] = {
                    'success_rate': perf['success'] / total_attempts * 100,
                    'total_attempts': total_attempts,
                    'successes': perf['success'],
                    'failures': perf['failure']
                }
        
        # Time analysis
        successful_results = [r for r in results if r.success]
        avg_navigation_time = sum(r.navigation_time for r in successful_results) / len(successful_results) if successful_results else 0
        avg_extraction_time = sum(r.extraction_time for r in successful_results) / len(successful_results) if successful_results else 0
        avg_total_time = sum(r.total_time for r in successful_results) / len(successful_results) if successful_results else 0
        
        return {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'successful_extractions': successful_extractions,
                'success_rate': successful_tests / total_tests * 100 if total_tests > 0 else 0,
                'extraction_rate': successful_extractions / total_tests * 100 if total_tests > 0 else 0,
                'total_test_time': total_time,
                'avg_time_per_test': total_time / total_tests if total_tests > 0 else 0
            },
            'performance': {
                'avg_navigation_time': avg_navigation_time,
                'avg_extraction_time': avg_extraction_time,
                'avg_total_time_per_success': avg_total_time,
                'anti_bot_encounters': self.stats['anti_bot_encounters'],
                'captcha_encounters': self.stats['captcha_encounters']
            },
            'metrics_coverage': metric_coverage,
            'proxy_performance': proxy_performance,
            'fingerprint_stats': {
                'unique_fingerprints_used': len(self.stats['unique_fingerprints']),
                'fingerprint_rotations': self.stats['fingerprint_rotations']
            },
            'bypass_techniques': dict(self.stats['bypass_techniques_used'])
        }
    
    def analyze_failures(self, results: List[EnhancedSimilarWebTestResult]) -> Dict:
        """Analyze failure patterns and causes"""
        failed_results = [r for r in results if not r.success]
        
        failure_by_type = defaultdict(int)
        failure_by_proxy_type = defaultdict(int)
        failure_by_anti_bot = defaultdict(int)
        common_errors = defaultdict(int)
        
        for result in failed_results:
            # Categorize failures
            if result.anti_bot_detected:
                failure_by_type['anti_bot'] += 1
                failure_by_anti_bot[result.anti_bot_type] += 1
            elif 'navigation' in result.error.lower():
                failure_by_type['navigation'] += 1
            elif 'extraction' in result.error.lower():
                failure_by_type['extraction'] += 1
            elif 'timeout' in result.error.lower():
                failure_by_type['timeout'] += 1
            else:
                failure_by_type['other'] += 1
            
            # Proxy type analysis
            failure_by_proxy_type[result.proxy_type] += 1
            
            # Common error patterns
            common_errors[result.error[:100]] += 1
        
        return {
            'total_failures': len(failed_results),
            'failure_by_type': dict(failure_by_type),
            'failure_by_proxy_type': dict(failure_by_proxy_type),
            'failure_by_anti_bot': dict(failure_by_anti_bot),
            'common_errors': dict(sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:10]),
            'failure_patterns': self._analyze_failure_patterns(failed_results)
        }
    
    def _analyze_failure_patterns(self, failed_results: List[EnhancedSimilarWebTestResult]) -> Dict:
        """Analyze patterns in failures"""
        patterns = {
            'proxy_related': 0,
            'fingerprint_related': 0,
            'site_specific': defaultdict(int),
            'time_based': {'long_navigation': 0, 'long_extraction': 0}
        }
        
        for result in failed_results:
            # Check for proxy-related failures
            if any(keyword in result.error.lower() for keyword in ['proxy', 'connection', 'timeout']):
                patterns['proxy_related'] += 1
            
            # Check for fingerprint-related failures
            if any(keyword in result.error.lower() for keyword in ['fingerprint', 'detection', 'automation']):
                patterns['fingerprint_related'] += 1
            
            # Site-specific failures
            patterns['site_specific'][result.domain] += 1
            
            # Time-based analysis
            if result.navigation_time > 60:  # Long navigation
                patterns['time_based']['long_navigation'] += 1
            if result.extraction_time > 30:  # Long extraction
                patterns['time_based']['long_extraction'] += 1
        
        return patterns
    
    def analyze_performance(self) -> Dict:
        """Analyze performance metrics"""
        proxy_stats = self.proxy_manager.get_proxy_stats()
        
        # Fingerprint performance
        fingerprint_performance = {}
        for hash_id, perf in self.performance_tracker['fingerprint_performance'].items():
            total = perf['success'] + perf['failure']
            if total > 0:
                fingerprint_performance[hash_id] = {
                    'success_rate': perf['success'] / total * 100,
                    'total_uses': total,
                    'successes': perf['success'],
                    'failures': perf['failure']
                }
        
        return {
            'proxy_stats': proxy_stats,
            'fingerprint_performance': fingerprint_performance,
            'bypass_effectiveness': dict(self.stats['bypass_techniques_used']),
            'resource_utilization': {
                'unique_proxies_used': len(self.stats['unique_proxies']),
                'unique_fingerprints_used': len(self.stats['unique_fingerprints']),
                'proxy_rotations': self.stats['proxy_rotations'],
                'fingerprint_rotations': self.stats['fingerprint_rotations']
            }
        }
    
    def save_comprehensive_results(self, results: List[EnhancedSimilarWebTestResult], 
                                 analysis: Dict, failure_analysis: Dict, 
                                 performance_analysis: Dict):
        """Save comprehensive test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory
        results_dir = Path(f"test_results_{timestamp}")
        results_dir.mkdir(exist_ok=True)
        
        # Save detailed results JSON
        detailed_results = {
            'test_metadata': {
                'timestamp': timestamp,
                'test_config': {
                    'use_proxies': self.use_proxies,
                    'headless': self.headless,
                    'browser_data_path': self.browser_data_path
                },
                'total_tests': len(results)
            },
            'results': [self._result_to_dict(r) for r in results],
            'analysis': analysis,
            'failure_analysis': failure_analysis,
            'performance_analysis': performance_analysis
        }
        
        with open(results_dir / f"detailed_results_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        # Save CSV summary
        self._save_csv_summary(results, results_dir / f"results_summary_{timestamp}.csv")
        
        # Save performance report
        self._save_performance_report(analysis, failure_analysis, performance_analysis, 
                                    results_dir / f"performance_report_{timestamp}.txt")
        
        logger.info(f"📁 Results saved to: {results_dir}")
    
    def _result_to_dict(self, result: EnhancedSimilarWebTestResult) -> Dict:
        """Convert result object to dictionary"""
        return {
            'url': result.url,
            'domain': result.domain,
            'success': result.success,
            'extraction_success': result.extraction_success,
            'error': result.error,
            'anti_bot_detected': result.anti_bot_detected,
            'anti_bot_type': result.anti_bot_type,
            'proxy_used': result.proxy_used,
            'proxy_type': result.proxy_type,
            'proxy_session_id': result.proxy_session_id,
            'fingerprint_profile': result.fingerprint_profile,
            'fingerprint_hash': result.fingerprint_hash,
            'attempts': result.attempts,
            'bypass_techniques_used': result.bypass_techniques_used,
            'total_time': result.total_time,
            'navigation_time': result.navigation_time,
            'extraction_time': result.extraction_time,
            'metrics_found': result.metrics_found,
            'confidence_score': result.confidence_score,
            'page_validated': result.page_validated,
            'timestamp': result.timestamp,
            'data_extracted': result.data_extracted
        }
    
    def _save_csv_summary(self, results: List[EnhancedSimilarWebTestResult], filepath: Path):
        """Save CSV summary of results"""
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'domain', 'success', 'extraction_success', 'total_time', 
                'navigation_time', 'extraction_time', 'proxy_type', 
                'anti_bot_detected', 'anti_bot_type', 'metrics_count', 
                'confidence_score', 'error'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'domain': result.domain,
                    'success': result.success,
                    'extraction_success': result.extraction_success,
                    'total_time': round(result.total_time, 2),
                    'navigation_time': round(result.navigation_time, 2),
                    'extraction_time': round(result.extraction_time, 2),
                    'proxy_type': result.proxy_type,
                    'anti_bot_detected': result.anti_bot_detected,
                    'anti_bot_type': result.anti_bot_type,
                    'metrics_count': len(result.metrics_found),
                    'confidence_score': round(result.confidence_score, 2),
                    'error': result.error[:200]  # Truncate long errors
                })
    
    def _save_performance_report(self, analysis: Dict, failure_analysis: Dict, 
                               performance_analysis: Dict, filepath: Path):
        """Save human-readable performance report"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("ULTRA-DYNAMIC SIMILARWEB SCRAPER - PERFORMANCE REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            # Summary
            summary = analysis['summary']
            f.write("SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Tests: {summary['total_tests']}\n")
            f.write(f"Successful Tests: {summary['successful_tests']}\n")
            f.write(f"Success Rate: {summary['success_rate']:.1f}%\n")
            f.write(f"Extraction Rate: {summary['extraction_rate']:.1f}%\n")
            f.write(f"Total Test Time: {summary['total_test_time']:.1f}s\n")
            f.write(f"Avg Time per Test: {summary['avg_time_per_test']:.1f}s\n\n")
            
            # Performance Metrics
            perf = analysis['performance']
            f.write("PERFORMANCE METRICS\n")
            f.write("-" * 20 + "\n")
            f.write(f"Avg Navigation Time: {perf['avg_navigation_time']:.1f}s\n")
            f.write(f"Avg Extraction Time: {perf['avg_extraction_time']:.1f}s\n")
            f.write(f"Anti-bot Encounters: {perf['anti_bot_encounters']}\n")
            f.write(f"CAPTCHA Encounters: {perf['captcha_encounters']}\n\n")
            
            # Failure Analysis
            f.write("FAILURE ANALYSIS\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Failures: {failure_analysis['total_failures']}\n")
            f.write("Failure by Type:\n")
            for fail_type, count in failure_analysis['failure_by_type'].items():
                f.write(f"  {fail_type}: {count}\n")
            f.write("\n")
            
            # Top Metrics Coverage
            f.write("METRICS COVERAGE (Top 10)\n")
            f.write("-" * 20 + "\n")
            sorted_metrics = sorted(analysis['metrics_coverage'].items(), 
                                  key=lambda x: x[1]['coverage_rate'], reverse=True)
            for metric, data in sorted_metrics[:10]:
                f.write(f"{metric}: {data['coverage_rate']:.1f}% ({data['found_count']} tests)\n")
            f.write("\n")
            
            # Proxy Performance (Top 5)
            f.write("TOP PROXY PERFORMANCE\n")
            f.write("-" * 20 + "\n")
            sorted_proxies = sorted(analysis['proxy_performance'].items(),
                                  key=lambda x: x[1]['success_rate'], reverse=True)
            for session_id, perf in sorted_proxies[:5]:
                f.write(f"{session_id}: {perf['success_rate']:.1f}% "
                       f"({perf['successes']}/{perf['total_attempts']})\n")

async def main():
    """Main execution function"""
    # Configuration
    config = {
        'num_urls': 20,  # Start with smaller number for testing
        'use_proxies': True,
        'headless': False,  # Set to True for production
        'browser_data_path': 'browsers.json'
    }
    
    logger.info("🚀 Starting Ultra-Dynamic SimilarWeb Scraper Test Suite")
    
    # Initialize scraper
    scraper = UltraDynamicSimilarWebScraper(
        use_proxies=config['use_proxies'],
        headless=config['headless'],
        browser_data_path=config['browser_data_path']
    )
    
    try:
        # Run comprehensive test
        results = await scraper.run_comprehensive_test(config['num_urls'])
        
        # Print final summary
        analysis = results['analysis']
        summary = analysis['summary']
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🏁 TEST SUITE COMPLETED!")
        logger.info(f"{'='*80}")
        logger.info(f"📊 Total Tests: {summary['total_tests']}")
        logger.info(f"✅ Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"📈 Extraction Rate: {summary['extraction_rate']:.1f}%")
        logger.info(f"⏱️ Total Time: {summary['total_test_time']:.1f}s")
        logger.info(f"🔄 Unique Proxies Used: {len(scraper.stats['unique_proxies'])}")
        logger.info(f"🎭 Unique Fingerprints Used: {len(scraper.stats['unique_fingerprints'])}")
        logger.info(f"🚫 Anti-bot Encounters: {analysis['performance']['anti_bot_encounters']}")
        logger.info(f"{'='*80}")
        
        return results
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
        return None
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        raise

if __name__ == "__main__":
    # Set event loop policy for Windows
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run the test suite
    asyncio.run(main())

#!/usr/bin/env python3
"""
SimilarWeb 1000 Tools Test Runner - Production Scale
Enhanced with proper error handling, retry queues, and comprehensive logging
"""

import asyncio
import json
import csv
import time
import random
import logging
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import motor.motor_asyncio
from pymongo import DESCENDING
import traceback
import gc

# Import your existing components
from smart_browser_controller import EnhancedSmartBrowserController
from proxy_manager import AdvancedProxyManager, ProxyType
from html_validator import SimilarWebValidator  # New component
from domain_filter import DomainFilter  # New component
from similarweb_extractor import SimilarWebExtractor
from fingerprint_evasion import AdvancedFingerprintEvasion
from playwright.async_api import async_playwright
# Enhanced logging setup
def setup_comprehensive_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    log_dir = data_dir / f"logs_1k_run_{timestamp}"
    log_dir.mkdir(exist_ok=True)
    
    # Configure detailed logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    
    # Main log file
    main_handler = logging.FileHandler(log_dir / "main_scraper.log", encoding='utf-8')
    main_handler.setFormatter(logging.Formatter(log_format))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    # Setup loggers
    loggers = {}
    for logger_name in ['main', 'proxy', 'browser', 'validation', 'extraction', 'database']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.addHandler(main_handler)
        logger.addHandler(console_handler)
        loggers[logger_name] = logger
    
    return loggers, log_dir

@dataclass
class ScrapingAttempt:
    attempt_number: int
    timestamp: float
    proxy_used: str
    success: bool
    error: Optional[str] = None
    response_time: float = 0.0
    html_saved: bool = False
    validation_passed: bool = False
    data_extracted: bool = False

@dataclass
class ToolResult:
    tool_id: str
    name: str
    url: str
    domain: str
    similarweb_url: str
    etv: float = 0.0
    attempts: List[ScrapingAttempt] = field(default_factory=list)
    final_success: bool = False
    final_error: Optional[str] = None
    html_files: List[str] = field(default_factory=list)
    extracted_data: Optional[Dict] = None
    total_time: float = 0.0
    queue_processed: str = "primary"



class SingleBrowserController(EnhancedSmartBrowserController):
    """Fixed browser controller that prevents double browser instances"""
    
    def __init__(self, headless: bool, proxy: dict | None, enable_streaming: bool = False):
        super().__init__(headless, proxy, enable_streaming)
        self.fingerprint_evasion = AdvancedFingerprintEvasion()
        self.current_fingerprint_profile = None

    async def __aenter__(self):
        """Initialize with single browser instance - NO persistent context"""
        # Prevent double initialization
        if hasattr(self, '_initialized') and self._initialized:
            return self
        
        # Get random fingerprint profile BEFORE browser initialization
        self.current_fingerprint_profile = self.fingerprint_evasion.get_random_profile()
        logging.info(f"Using fingerprint profile: {self.current_fingerprint_profile['name']}")
        
        # Initialize Playwright
        self.play = await async_playwright().start()
        
        # Enhanced launch options with incognito mode
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
        
        if self.proxy:
            launch_options["proxy"] = self.proxy
            
        # SINGLE BROWSER APPROACH - like test runner
        self.browser = await self.play.chromium.launch(**launch_options)
        
        # Create context with fingerprint settings
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
            
        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()
        
        # Inject fingerprint evasion script
        fingerprint_script = self.fingerprint_evasion.generate_anti_fingerprintjs_script(
            self.current_fingerprint_profile
        )
        await self.page.add_init_script(fingerprint_script)
        
        self._initialized = True
        return self



class SimilarWeb1000Scraper:
    def __init__(self, mongodb_uri: str, headless: bool = True):
        self.mongodb_uri = mongodb_uri
        self.headless = headless
        
        # Setup logging
        self.loggers, self.log_dir = setup_comprehensive_logging()
        self.logger = self.loggers['main']
        
        # Initialize components
        self.proxy_manager = AdvancedProxyManager()
        self.validator = SimilarWebValidator()
        self.extractor = SimilarWebExtractor()
        
        # Create output directories under ./data
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = data_dir / f"similarweb_1k_{self.timestamp}"
        self.html_dir = self.output_dir / "html_files"
        self.results_dir = self.output_dir / "results"
        
        for directory in [self.output_dir, self.html_dir, self.results_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Results tracking
        self.results: List[ToolResult] = []
        self.primary_queue: List[Dict] = []
        self.retry_queue_1: List[ToolResult] = []
        self.retry_queue_2: List[ToolResult] = []
        
        # Statistics
        self.stats = {
            'total_tools_fetched': 0,
            'valid_domains': 0,
            'invalid_domains': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'html_files_saved': 0,
            'total_attempts': 0,
            'proxy_rotations': 0,
            'validation_passes': 0,
            'validation_failures': 0,
            'start_time': None,
            'end_time': None
        }
        
        self.logger.info(f"Scraper initialized - Output: {self.output_dir}")
    
    async def connect_mongodb(self):
        """Connect to MongoDB with error handling"""
        try:
            client = motor.motor_asyncio.AsyncIOMotorClient(self.mongodb_uri)
            await client.admin.command('ping')
            self.loggers['database'].info("MongoDB connection successful")
            return client
        except Exception as e:
            self.loggers['database'].error(f"MongoDB connection failed: {e}")
            raise
    
    async def fetch_top_tools(self, limit: int = 1000) -> List[Dict]:
        """Fetch top tools by ETV from MongoDB (motor)"""
        try:
            client = await self.connect_mongodb()
            db = client.get_default_database()
            if db is None:
                # Fallback if DB name isn't in the URI
                from urllib.parse import urlparse
                db = client["AIAggregator"]

            collection = db["FutureTools"]  # capital F and T
            self.loggers['database'].info(f"Fetching top {limit} tools by ETV...")

            query = {
                'stats.traffic_data.organic.etv': {'$gt': 0},
                'url': {'$type': 'string', '$nin': ['', None]},
            }

            projection = {
                '_id': 1, 'name': 1, 'url': 1,
                'stats.traffic_data.organic.etv': 1,
                'category': 1, 'description': 1
            }

            cursor = (collection.find(query, projection)
                    .sort([('stats.traffic_data.organic.etv', DESCENDING)])
                    .limit(limit))

            tools = await cursor.to_list(length=limit)

            self.stats['total_tools_fetched'] = len(tools)
            self.loggers['database'].info(f"Fetched {len(tools)} tools from MongoDB")
            return tools

        except Exception as e:
            self.loggers['database'].error(f"Error fetching tools: {e}")
            raise
        finally:
            try:
                client.close()
            except Exception:
                pass

    
    def filter_and_prepare_tools(self, tools: List[Dict]) -> List[Dict]:
        """Filter tools and prepare for scraping"""
        valid_tools = []
        
        for tool in tools:
            url = tool.get('url', '')
            
            if DomainFilter.is_valid_for_similarweb(url):
                domain = DomainFilter.extract_domain(url)
                if domain:
                    tool['etv'] = tool.get('stats', {}).get('traffic_data', {}).get('organic', {}).get('etv', 0.0)
                    tool['domain'] = domain
                    tool['similarweb_url'] = f"https://www.similarweb.com/website/{domain}/"
                    valid_tools.append(tool)
                    self.stats['valid_domains'] += 1
                else:
                    self.stats['invalid_domains'] += 1
                    self.logger.debug(f"Domain extraction failed: {url}")
            else:
                self.stats['invalid_domains'] += 1
                self.logger.debug(f"Invalid domain filtered: {url}")
        
        self.logger.info(f"Valid tools for scraping: {len(valid_tools)}/{len(tools)}")
        return valid_tools
    
    
    

    async def scrape_single_tool(self, tool_data: Dict, max_attempts: int = 5) -> ToolResult:
        """Scrape single tool with comprehensive error handling"""
        tool_id = str(tool_data.get('_id', ''))
        name = tool_data.get('name', 'Unknown')
        url = tool_data.get('url', '')
        domain = tool_data.get('domain', '')
        similarweb_url = tool_data.get('similarweb_url', '')
        etv = tool_data.get('etv', 0.0)
        
        result = ToolResult(
            tool_id=tool_id, name=name, url=url, domain=domain,
            similarweb_url=similarweb_url, etv=etv
        )
        
        start_time = time.time()
        self.logger.info(f"Scraping {name} ({domain}) - ETV: {etv}")
        
        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"Attempt {attempt}/{max_attempts} for {name}")
            
            attempt_record = ScrapingAttempt(
                attempt_number=attempt,
                timestamp=time.time(),
                proxy_used="None",
                success=False
            )
            
            try:
                # Get proxy - prioritize residential for large scale
                proxy = None
                proxy_info = None
                if self.proxy_manager.proxies:
                    proxy_info = self.proxy_manager.get_best_proxy(
                        prefer_type=ProxyType.RESIDENTIAL,
                        exclude_blocked_for="similarweb.com"
                    )
                    if proxy_info:
                        proxy = proxy_info.to_playwright_dict()
                        attempt_record.proxy_used = proxy.get('server', 'Unknown')
                        self.loggers['proxy'].info(f"Using proxy: {attempt_record.proxy_used}")
                
                # Use proper async context manager - this prevents double browser instances
                async with SingleBrowserController(
                    headless=self.headless,
                    proxy=proxy,
                    enable_streaming=False
                ) as browser:
                    
                    # Navigate with timeout
                    nav_start = time.time()
                    try:
                        nav_success = await asyncio.wait_for(
                            browser.smart_navigate(similarweb_url),
                            timeout=120.0  # 2 minute timeout
                        )
                        attempt_record.response_time = time.time() - nav_start
                        
                        if not nav_success:
                            attempt_record.error = "Smart navigation failed"
                            continue
                            
                    except asyncio.TimeoutError:
                        attempt_record.error = "Navigation timeout (120s)"
                        attempt_record.response_time = time.time() - nav_start
                        continue
                    
                    # Handle popups
                    await browser.handle_similarweb_popups()
                    await asyncio.sleep(3)  # Allow page to settle
                    
                    # VISION-FIRST VALIDATION (before saving HTML)
                    self.logger.info(f"Validating page for {name} using vision...")
                    validation_result = await self.validator.validate_page_before_saving(browser, domain)
                    
                    if validation_result.get('should_save_html', False):
                        attempt_record.validation_passed = True
                        self.stats['validation_passes'] += 1
                        
                        # Save HTML only after validation passes
                        try:
                            html_content = await browser.page.content()
                            html_filename = f"{domain}_{attempt}_{int(time.time())}.html"
                            html_path = self.html_dir / html_filename
                            
                            # Save with metadata
                            with open(html_path, 'w', encoding='utf-8') as f:
                                f.write(f"<!-- Tool: {name} -->\n")
                                f.write(f"<!-- Domain: {domain} -->\n")
                                f.write(f"<!-- ETV: {etv} -->\n")
                                f.write(f"<!-- Validation: PASSED -->\n")
                                f.write(f"<!-- Found Metrics: {validation_result.get('found_metrics', [])} -->\n")
                                f.write("<!-- ================================== -->\n\n")
                                f.write(html_content)
                            
                            attempt_record.html_saved = True
                            result.html_files.append(str(html_path))
                            self.stats['html_files_saved'] += 1
                            
                            self.logger.info(f"HTML saved for {name}: {html_filename}")
                            attempt_record.data_extracted = True
                            attempt_record.success = True
                            result.final_success = True
                                    
                            # Mark proxy success
                            if proxy and proxy_info:
                                self.proxy_manager.mark_proxy_success(proxy_info, attempt_record.response_time)
                                    
                                self.logger.info(f"SUCCESS: {name} - Data extracted")
                                self.stats['successful_scrapes'] += 1
                                break  # Success - exit retry loop
                        
                        except Exception as e:
                            attempt_record.error = f"HTML save error: {str(e)}"
                            self.logger.error(f"Failed to save HTML for {name}: {e}")
                            
                    else:
                        # Validation failed - don't save HTML
                        attempt_record.validation_passed = False
                        self.stats['validation_failures'] += 1
                        blocking_type = validation_result.get('blocking_type', 'unknown')
                        attempt_record.error = f"Page validation failed: {blocking_type}"
                        self.logger.warning(f"Validation failed for {name}: {blocking_type}")
                        
                        # Mark proxy failure for certain blocking types
                        if blocking_type in ['login_required', 'upgrade_needed'] and proxy and proxy_info:
                            self.proxy_manager.mark_proxy_failure(proxy_info, "similarweb.com", blocking_type)
            
            except Exception as e:
                attempt_record.error = f"Browser error: {str(e)}"
                self.logger.error(f"Browser error for {name}: {e}")
                
                if proxy and proxy_info:
                    self.proxy_manager.mark_proxy_failure(proxy_info, "similarweb.com", "browser_error")
            
            finally:
                # Browser cleanup is handled automatically by async context manager
                # Just do garbage collection and record attempt
                gc.collect()
                result.attempts.append(attempt_record)
                self.stats['total_attempts'] += 1
            
            # Success break or delay before retry
            if result.final_success:
                break
            elif attempt < max_attempts:
                delay = random.uniform(20, 40)  # Longer delays for 1K scraping
                self.logger.info(f"Waiting {delay:.1f}s before retry...")
                await asyncio.sleep(delay)
        
        # Final result processing
        result.total_time = time.time() - start_time
        if not result.final_success:
            result.final_error = result.attempts[-1].error if result.attempts else "Unknown error"
            self.stats['failed_scrapes'] += 1
            self.logger.warning(f"FAILED: {name} after {len(result.attempts)} attempts")
        
        return result
    
    async def process_queue(self, queue: List, queue_name: str, max_attempts: int):
        """Process a queue with progress tracking and proper error handling"""
        results = []
        total = len(queue)
        
        self.logger.info(f"Processing {queue_name}: {total} items, {max_attempts} attempts each")
        
        for i, item in enumerate(queue, 1):
            self.logger.info(f"{queue_name} Progress: {i}/{total} ({self.safe_percentage(i, total):.1f}%)")
            
            try:
                if isinstance(item, dict):
                    result = await self.scrape_single_tool(item, max_attempts)
                    result.queue_processed = queue_name
                else:
                    # Retry queue item
                    result = await self.scrape_single_tool({
                        '_id': item.tool_id,
                        'name': item.name,
                        'url': item.url,
                        'domain': item.domain,
                        'similarweb_url': item.similarweb_url,
                        'etv': item.etv
                    }, max_attempts)
                    result.queue_processed = queue_name
                
                results.append(result)
                
                # Update instance results for real-time tracking
                self.results.append(result)
                
                # Memory management - aggressive cleanup every 10 tools
                if i % 10 == 0:
                    # gc.collect()
                    await asyncio.sleep(1)
                
                # Save checkpoint every 100 items
                if i % 100 == 0:
                    await self.save_checkpoint(results, f"{queue_name}_{i}", queue_name)
                    self.print_current_stats(results)
            
            except Exception as e:
                # Create a failed result object for critical errors
                self.logger.error(f"Critical error processing tool {i}: {e}")
                
                # Create minimal failed result
                if isinstance(item, dict):
                    tool_id = str(item.get('_id', ''))
                    name = item.get('name', 'Unknown')
                    domain = item.get('domain', '')
                else:
                    tool_id = item.tool_id
                    name = item.name
                    domain = item.domain
                
                failed_result = ToolResult(
                    tool_id=tool_id,
                    name=name,
                    url=item.get('url', '') if isinstance(item, dict) else item.url,
                    domain=domain,
                    similarweb_url=item.get('similarweb_url', '') if isinstance(item, dict) else item.similarweb_url,
                    etv=item.get('etv', 0.0) if isinstance(item, dict) else item.etv
                )
                failed_result.final_error = f"Critical error: {str(e)}"
                failed_result.queue_processed = queue_name
                
                results.append(failed_result)
                self.results.append(failed_result)
                self.stats['failed_scrapes'] += 1
        
        return results
    
    async def run_1000_tool_scraping(self) -> Dict:
        """Main execution function for 1000 tool scraping"""
        self.stats['start_time'] = time.time()
        self.logger.info("Starting 1000-tool SimilarWeb scraping operation")
        
        try:
            # Fetch tools
            tools = await self.fetch_top_tools(1000)
            
            # Filter valid domains
            valid_tools = self.filter_and_prepare_tools(tools)
            self.primary_queue = valid_tools
            
            self.logger.info(f"Primary queue: {len(self.primary_queue)} tools")
            
            # Process primary queue (5 attempts each)
            primary_results = await self.process_queue(self.primary_queue, "primary", 5)
            
            # Separate results
            successful = [r for r in primary_results if r.final_success]
            failed = [r for r in primary_results if not r.final_success]
            
            self.logger.info(f"Primary complete: {len(successful)} success, {len(failed)} failed")
            
            # Retry queue 1 (2 attempts each)
            retry_1_results = []
            retry_2_results = []
            if failed:
                self.logger.info(f"Starting retry queue 1: {len(failed)} tools")
                retry_1_results = await self.process_queue(failed, "retry_1", 2)
                
                retry_1_success = [r for r in retry_1_results if r.final_success]
                retry_1_failed = [r for r in retry_1_results if not r.final_success]
                successful.extend(retry_1_success)
                
                self.logger.info(f"Retry 1 complete: {len(retry_1_success)} additional success")
                
                # Final retry queue (2 attempts each)
                if retry_1_failed:
                    self.logger.info(f"Starting final retry: {len(retry_1_failed)} tools")
                    retry_2_results = await self.process_queue(retry_1_failed, "retry_2", 2)
                    
                    final_success = [r for r in retry_2_results if r.final_success]
                    successful.extend(final_success)
                    
                    self.logger.info(f"Final retry complete: {len(final_success)} additional success")
            
            
            self.stats['end_time'] = time.time()
            
            # Generate final reports
            await self.save_final_results()
            report = self.generate_comprehensive_report()
            
            return report
            
        except Exception as e:
            self.logger.error(f"Critical error in 1000-tool scraping: {e}")
            self.logger.error(traceback.format_exc())
            raise
    def safe_percentage(self, numerator, denominator):
        """Safe division to avoid division by zero errors"""
        return (numerator / denominator * 100) if denominator > 0 else 0.0
    
    async def save_checkpoint(self, results: List[ToolResult], checkpoint_name: str, queue_name: str = "unknown"):
        """Save intermediate results with enhanced metadata"""
        checkpoint_file = self.results_dir / f"checkpoint_{checkpoint_name}.json"
        
        successful_results = [r for r in results if r.final_success]
        
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'checkpoint_name': checkpoint_name,
            'queue_name': queue_name,
            'total_results': len(results),
            'successful': len(successful_results),
            'failed': len(results) - len(successful_results),
            'success_rate': self.safe_percentage(len(successful_results), len(results)),
            'execution_stats': {
                'html_files_saved': self.stats['html_files_saved'],
                'total_attempts': self.stats['total_attempts'],
                'validation_passes': self.stats['validation_passes'],
                'validation_failures': self.stats['validation_failures']
            },
            'results': [
                {
                    'tool_id': r.tool_id,
                    'name': r.name,
                    'domain': r.domain,
                    'etv': r.etv,
                    'success': r.final_success,
                    'attempts': len(r.attempts),
                    'html_files': len(r.html_files),
                    'total_time': r.total_time,
                    'final_error': r.final_error,
                    'queue_processed': getattr(r, 'queue_processed', queue_name)
                }
                for r in results
            ]
        }
        
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            self.logger.info(f"Checkpoint saved: {checkpoint_file}")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")

    def analyze_results(self, results: List[ToolResult], total_time: float) -> Dict:
        """Comprehensive results analysis with safe division"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.final_success)
        successful_extractions = sum(1 for r in results if r.final_success)
        
        # Calculate all possible metrics coverage
        all_metrics = set()
        for result in results:
            if result.extracted_data and result.extracted_data.get('data'):
                all_metrics.update(result.extracted_data['data'].keys())
        
        metric_coverage = {}
        for metric in all_metrics:
            coverage_count = sum(1 for r in results 
                            if r.extracted_data and r.extracted_data.get('data') and 
                                metric in r.extracted_data.get('data', {}))
            metric_coverage[metric] = {
                'found_count': coverage_count,
                'coverage_rate': self.safe_percentage(coverage_count, total_tests)
            }
        
        # Proxy performance analysis
        proxy_performance = {}
        for result in results:
            proxy = 'Unknown'
            if result.attempts:
                proxy = result.attempts[-1].proxy_used
            if proxy not in proxy_performance:
                proxy_performance[proxy] = {'total': 0, 'success': 0, 'avg_time': 0}
            
            proxy_performance[proxy]['total'] += 1
            if result.final_success:
                proxy_performance[proxy]['success'] += 1
            proxy_performance[proxy]['avg_time'] += result.total_time
        
        # Calculate success rates and average times with safe division
        for proxy, stats in proxy_performance.items():
            stats['success_rate'] = self.safe_percentage(stats['success'], stats['total'])
            stats['avg_time'] = stats['avg_time'] / stats['total'] if stats['total'] > 0 else 0
        
        return {
            'total_tests': total_tests,
            'successful_navigations': successful_tests,
            'successful_extractions': successful_extractions,
            'navigation_success_rate': self.safe_percentage(successful_tests, total_tests),
            'extraction_success_rate': self.safe_percentage(successful_extractions, total_tests),
            'overall_success_rate': self.safe_percentage(successful_extractions, total_tests),
            'metric_coverage': metric_coverage,
            'proxy_performance': proxy_performance,
            'average_time_per_test': total_time / total_tests if total_tests > 0 else 0,
            'total_test_time': total_time,
            'test_stats': self.stats
        }
    
    async def save_final_results(self):
        """Save comprehensive final results"""
        # JSON results
        json_file = self.results_dir / f"final_results_{self.timestamp}.json"
        csv_file = self.results_dir / f"final_results_{self.timestamp}.csv"
        
        # Prepare data
        results_data = []
        for result in self.results:
            results_data.append({
                'tool_id': result.tool_id,
                'name': result.name,
                'url': result.url,
                'domain': result.domain,
                'etv': result.etv,
                'similarweb_url': result.similarweb_url,
                'final_success': result.final_success,
                'final_error': result.final_error,
                'total_attempts': len(result.attempts),
                'html_files_saved': len(result.html_files),
                'total_time': result.total_time,
                'queue_processed': result.queue_processed,
                'attempt_details': [
                    {
                        'attempt': a.attempt_number,
                        'success': a.success,
                        'validation_passed': a.validation_passed,
                        'html_saved': a.html_saved,
                        'data_extracted': a.data_extracted,
                        'proxy_used': a.proxy_used,
                        'error': a.error
                    }
                    for a in result.attempts
                ]
            })
        
        # Save JSON
        final_data = {
            'metadata': {
                'total_tools_processed': len(self.results),
                'timestamp': self.timestamp,
                'duration_minutes': (self.stats['end_time'] - self.stats['start_time']) / 60,
                'mongodb_uri': self.mongodb_uri
            },
            'statistics': self.stats,
            'results': results_data
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2)
        
        # Save CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Tool ID', 'Name', 'Domain', 'ETV', 'Final Success',
                'Total Attempts', 'HTML Files', 'Total Time (s)',
                'Queue Processed', 'Final Error'
            ])
            
            for result in self.results:
                writer.writerow([
                    result.tool_id, result.name, result.domain, result.etv,
                    result.final_success, len(result.attempts), len(result.html_files),
                    f"{result.total_time:.2f}",
                    result.queue_processed, result.final_error or 'N/A'
                ])
        
        self.logger.info(f"Final results saved: {json_file}, {csv_file}")
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate final comprehensive report with safe calculations"""
        successful_results = [r for r in self.results if r.final_success]
        failed_results = [r for r in self.results if not r.final_success]
        
        # Calculate detailed statistics with safe division
        total_time = self.stats['end_time'] - self.stats['start_time'] if self.stats.get('end_time') and self.stats.get('start_time') else 0
        avg_time_per_tool = total_time / len(self.results) if self.results else 0
        
        # Success by queue
        primary_success = len([r for r in self.results if r.final_success and getattr(r, 'queue_processed', '') == "primary"])
        retry_1_success = len([r for r in self.results if r.final_success and getattr(r, 'queue_processed', '') == "retry_1"])
        retry_2_success = len([r for r in self.results if r.final_success and getattr(r, 'queue_processed', '') == "retry_2"])
        
        # Proxy statistics
        proxy_stats = self.proxy_manager.get_proxy_stats() if hasattr(self, 'proxy_manager') else {}
        
        report = {
            'execution_summary': {
                'total_tools_processed': len(self.results),
                'total_successful': len(successful_results),
                'total_failed': len(failed_results),
                'overall_success_rate': self.safe_percentage(len(successful_results), len(self.results)),
                'total_execution_time_hours': total_time / 3600,
                'average_time_per_tool_minutes': avg_time_per_tool / 60
            },
            'queue_performance': {
                'primary_queue_success': primary_success,
                'retry_1_additional_success': retry_1_success,
                'retry_2_additional_success': retry_2_success
            },
            'technical_statistics': {
                'total_attempts': self.stats['total_attempts'],
                'html_files_saved': self.stats['html_files_saved'],
                'validation_passes': self.stats['validation_passes'],
                'validation_failures': self.stats['validation_failures'],
                'proxy_statistics': proxy_stats
            },
            'domain_filtering': {
                'total_tools_fetched': self.stats['total_tools_fetched'],
                'valid_domains': self.stats['valid_domains'],
                'invalid_domains': self.stats['invalid_domains'],
                'filtering_success_rate': self.safe_percentage(self.stats['valid_domains'], self.stats['total_tools_fetched'])
            }
        }
        
        return report
    
    def print_current_stats(self, current_results=None):
        """Print current statistics to console with safe division"""
        results_to_use = current_results if current_results is not None else self.results
        successful = len([r for r in results_to_use if r.final_success])
        total_processed = len(results_to_use)
        
        # Safety check for division by zero
        if total_processed == 0:
            print(f"\n{'='*60}")
            print(f"CURRENT PROGRESS STATISTICS")
            print(f"{'='*60}")
            print(f"No results processed yet")
            print(f"HTML Files Saved: {self.stats['html_files_saved']}")
            print(f"Total Attempts: {self.stats['total_attempts']}")
            print(f"Validation Passes: {self.stats['validation_passes']}")
            print(f"Validation Failures: {self.stats['validation_failures']}")
            
            if self.stats['start_time']:
                elapsed = time.time() - self.stats['start_time']
                print(f"Elapsed Time: {elapsed/3600:.1f} hours")
            print(f"{'='*60}\n")
            return

        print(f"\n{'='*60}")
        print(f"CURRENT PROGRESS STATISTICS")
        print(f"{'='*60}")
        print(f"Processed: {total_processed}")
        print(f"Successful: {successful} ({self.safe_percentage(successful, total_processed):.1f}%)")
        print(f"HTML Files Saved: {self.stats['html_files_saved']}")
        print(f"Total Attempts: {self.stats['total_attempts']}")
        print(f"Validation Passes: {self.stats['validation_passes']}")
        print(f"Validation Failures: {self.stats['validation_failures']}")
        
        if self.stats['start_time']:
            elapsed = time.time() - self.stats['start_time']
            print(f"Elapsed Time: {elapsed/3600:.1f} hours")
            if total_processed > 0 and hasattr(self, 'primary_queue'):
                estimated_total_time = (elapsed / total_processed) * len(self.primary_queue)
                print(f"Estimated Total Time: {estimated_total_time/3600:.1f} hours")
        print(f"{'='*60}\n")

async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SimilarWeb 1000 Tools Scraper")
    parser.add_argument("--mongodb-uri", help="MongoDB connection URI")
    parser.add_argument("--headless", action="store_true", default=False, help="Run in headless mode")
    parser.add_argument("--limit", type=int, default=1000, help="Number of tools to process")
    
    args = parser.parse_args()
    
    # Environment checks
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set!")
        print("Set it with: export GOOGLE_API_KEY='your_api_key'")
        return 1
    
    try:
        scraper = SimilarWeb1000Scraper(
            mongodb_uri=args.mongodb_uri,
            headless=args.headless
        )
        
        print(f"Starting SimilarWeb scraping for {args.limit} tools...")
        print(f"MongoDB URI: {args.mongodb_uri}")
        print(f"Headless mode: {args.headless}")
        print(f"Output directory: {scraper.output_dir}")
        
        # Run the comprehensive scraping
        final_report = await scraper.run_1000_tool_scraping()
        
        # Print final report
        print(f"\n{'='*80}")
        print("FINAL EXECUTION REPORT")
        print(f"{'='*80}")
        
        exec_summary = final_report['execution_summary']
        print(f"Total Tools: {exec_summary['total_tools_processed']}")
        print(f"Successful: {exec_summary['total_successful']}")
        print(f"Success Rate: {exec_summary['overall_success_rate']:.1f}%")
        print(f"Total Time: {exec_summary['total_execution_time_hours']:.2f} hours")
        print(f"Avg Time/Tool: {exec_summary['average_time_per_tool_minutes']:.1f} minutes")
        
        queue_perf = final_report['queue_performance']
        print(f"\nQueue Performance:")
        print(f"  Primary Queue Success: {queue_perf['primary_queue_success']}")
        print(f"  Retry 1 Additional: {queue_perf['retry_1_additional_success']}")
        print(f"  Retry 2 Additional: {queue_perf['retry_2_additional_success']}")
        
        tech_stats = final_report['technical_statistics']
        print(f"\nTechnical Statistics:")
        print(f"  Total Attempts: {tech_stats['total_attempts']}")
        print(f"  HTML Files Saved: {tech_stats['html_files_saved']}")
        print(f"  Validation Passes: {tech_stats['validation_passes']}")
        print(f"  Validation Failures: {tech_stats['validation_failures']}")
        
        print(f"\nOutput saved to: {scraper.output_dir}")
        print("Scraping completed successfully!")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        return 1
    except Exception as e:
        print(f"Critical error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
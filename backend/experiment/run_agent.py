# INTEGRATION GUIDE: Ultra-Dynamic Unbeatable Scraper
# =====================================================

"""
HOW TO USE THE ENHANCED SCRAPER SYSTEM

This guide shows how to integrate all the enhanced components to create
an unbeatable scraper that can bypass any anti-bot system.

COMPONENTS:
1. AdvancedFingerprintEvasion - Dynamic browser fingerprinting
2. EnhancedSmartBrowserController - Smart navigation with bypass techniques  
3. AdvancedProxyManager - Intelligent proxy rotation
4. Bypass403Engine - Advanced 403/block bypass techniques
5. AntiBotVisionModel - Vision-based anti-bot detection
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
import base64
# Import all enhanced components
from backend.experiment.testing.fingerprint_evasion import AdvancedFingerprintEvasion
from smart_browser_controller import EnhancedSmartBrowserController
from backend.experiment.testing.proxy_manager import AdvancedProxyManager, ProxyType
from anti_bot_detection import AntiBotVisionModel
from vision_model import decide
from universal_extractor import UniversalExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UnbeatableScraper:
    """
    Main scraper class that integrates all components
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the unbeatable scraper
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or self._load_default_config()
        
        # Initialize components
        self.fingerprint_evasion = AdvancedFingerprintEvasion(
            browser_data_path=self.config.get("browser_data_path", "browsers.json")
        )
        
        self.vision_model = AntiBotVisionModel()
        self.proxy_manager = AdvancedProxyManager(self.vision_model)
        self.extractor = UniversalExtractor()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "bypasses_used": 0,
            "proxies_rotated": 0,
            "fingerprints_rotated": 0,
            "captchas_encountered": 0,
            "captchas_solved": 0
        }
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            "browser_data_path": "browsers.json",
            "headless": False,  # Start with visible browser for debugging
            "use_proxies": True,
            "proxy_rotation_strategy": "smart",
            "fingerprint_rotation_interval": 600,  # 10 minutes
            "max_retries": 10,
            "enable_streaming": False,
            "save_screenshots": True,
            "bypass_403": True,
            "solve_captchas": True,
            "export_stats": True
        }
    
    async def scrape(self, url: str, goal: str = None, output_format: str = "json") -> Dict:
        """
        Main scraping method with all protections
        
        Args:
            url: Target URL to scrape
            goal: Optional goal/instruction for AI agent
            output_format: Output format (json, html, csv, txt, pdf)
        
        Returns:
            Scraped data and metadata
        """
        logger.info(f"🎯 Starting unbeatable scrape: {url}")
        self.stats["total_requests"] += 1
        
        result = {
            "success": False,
            "url": url,
            "data": None,
            "metadata": {},
            "errors": []
        }
        
        # Get best proxy
        proxy = None
        if self.config.get("use_proxies"):
            proxy_info = self.proxy_manager.get_best_proxy(
                prefer_type=ProxyType.RESIDENTIAL,
                # strategy=self.config.get("proxy_rotation_strategy", "smart")
            )
            if proxy_info:
                proxy = proxy_info.to_playwright_dict()
                logger.info(f"🔄 Using proxy: {proxy_info.session_id} ({proxy_info.proxy_type.value})")
        
        try:
            # Initialize browser with dynamic fingerprint
            async with EnhancedSmartBrowserController(
                headless=self.config.get("headless", False),
                proxy=proxy,
                enable_streaming=self.config.get("enable_streaming", False)
            ) as browser:
                
                # Log fingerprint info
                logger.info(f"🎭 Fingerprint: {browser.current_fingerprint_profile['name']}")
                logger.info(f"📱 User Agent: {browser.current_fingerprint_profile['user_agent'][:80]}...")
                
                # Navigate with smart anti-detection
                navigation_success = await browser.smart_navigate(url)
                
                if not navigation_success:
                    logger.error(f"❌ Failed to navigate to {url}")
                    result["errors"].append("Navigation failed")
                    
                    # Try with different proxy/fingerprint
                    if self.config.get("use_proxies"):
                        logger.info("🔄 Retrying with different proxy...")
                        self.stats["proxies_rotated"] += 1
                        
                        # Get new proxy
                        new_proxy_info = self.proxy_manager.get_best_proxy(
                            prefer_type=ProxyType.MOBILE,  # Try mobile proxy
                            exclude_blocked_for=url
                        )
                        if new_proxy_info:
                            proxy = new_proxy_info.to_playwright_dict()
                            
                            # Retry with new configuration
                            async with EnhancedSmartBrowserController(
                                headless=self.config.get("headless", False),
                                proxy=proxy,
                                enable_streaming=False
                            ) as retry_browser:
                                navigation_success = await retry_browser.smart_navigate(url)
                                if navigation_success:
                                    browser = retry_browser
                
                if navigation_success:
                    logger.info(f"✅ Successfully navigated to {url}")
                    self.stats["successful_requests"] += 1
                    
                    # Save screenshot if enabled
                    if self.config.get("save_screenshots"):
                        screenshot_path = f"screenshots/{url.replace('/', '_')[:50]}.png"
                        await browser.page.screenshot(path=screenshot_path)
                        logger.info(f"📸 Screenshot saved: {screenshot_path}")
                    
                    # Extract content based on goal
                    if goal:
                        # Use AI agent for goal-based extraction
                        extracted_data = await self._ai_guided_extraction(browser, goal, output_format)
                    else:
                        # Direct extraction
                        extracted_data = await self._direct_extraction(browser, output_format)
                    
                    result["success"] = True
                    result["data"] = extracted_data
                    
                    # Collect metadata
                    result["metadata"] = {
                        "final_url": browser.page.url,
                        "title": await browser.page.title(),
                        "proxy_used": proxy.get("server") if proxy else None,
                        "fingerprint_used": browser.current_fingerprint_profile["name"],
                        "bypasses_used": browser.bypass_engine.bypass_attempts,
                        "extraction_format": output_format
                    }
                    
                    # Update proxy success
                    if proxy and proxy_info:
                        self.proxy_manager.mark_proxy_success(proxy_info)
                
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            result["errors"].append(str(e))
        
        # Export statistics if enabled
        if self.config.get("export_stats"):
            self._export_statistics()
        
        return result
    
    async def _ai_guided_extraction(self, browser, goal: str, output_format: str) -> any:
        """Extract content using AI guidance"""
        logger.info(f"🤖 Starting AI-guided extraction with goal: {goal}")
        
        max_steps = 30
        for step in range(max_steps):
            # Get current page state
            page_state = await browser.get_page_state(include_screenshot=True)
            
            if not page_state.screenshot:
                continue
            
            # AI decision
            screenshot_bytes = base64.b64decode(page_state.screenshot)
            decision = await decide(screenshot_bytes, page_state, goal)
            
            logger.info(f"Step {step + 1}: {decision.get('action')} - {decision.get('reason', '')}")
            
            # Execute action
            action = decision.get("action")
            
            if action == "extract":
                # Extract content
                content = await self.extractor.extract_intelligent_content(
                    browser, goal, output_format, "extraction_job"
                )
                return content
            
            elif action == "done":
                # Task complete
                break
            
            elif action == "click":
                index = decision.get("index")
                if index in page_state.selector_map:
                    await browser.click_element_by_index(index, page_state)
            
            elif action == "type":
                index = decision.get("index")
                text = decision.get("text", "")
                if index in page_state.selector_map and text:
                    await browser.input_text_by_index(index, text, page_state)
            
            elif action == "scroll":
                direction = decision.get("direction", "down")
                amount = decision.get("amount", 400)
                await browser.scroll_page(direction, amount)
            
            elif action == "navigate":
                url = decision.get("url")
                if url:
                    await browser.smart_navigate(url)
            
            await asyncio.sleep(1)
        
        # Final extraction if not done
        return await self.extractor.extract_intelligent_content(
            browser, goal, output_format, "extraction_job"
        )
    
    async def _direct_extraction(self, browser, output_format: str) -> any:
        """Direct content extraction without AI guidance"""
        logger.info(f"📋 Starting direct extraction in {output_format} format")
        
        # Wait for page to fully load
        await asyncio.sleep(3)
        
        if output_format == "html":
            return await browser.page.content()
        
        elif output_format == "json":
            # Extract structured data
            data = await browser.page.evaluate("""
                () => {
                    const data = {};
                    
                    // Extract meta tags
                    data.meta = {};
                    document.querySelectorAll('meta').forEach(meta => {
                        const name = meta.getAttribute('name') || meta.getAttribute('property');
                        const content = meta.getAttribute('content');
                        if (name && content) {
                            data.meta[name] = content;
                        }
                    });
                    
                    // Extract headings
                    data.headings = [];
                    document.querySelectorAll('h1, h2, h3').forEach(h => {
                        data.headings.push({
                            level: h.tagName,
                            text: h.textContent.trim()
                        });
                    });
                    
                    // Extract links
                    data.links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        data.links.push({
                            text: a.textContent.trim(),
                            href: a.href
                        });
                    });
                    
                    // Extract images
                    data.images = [];
                    document.querySelectorAll('img[src]').forEach(img => {
                        data.images.push({
                            src: img.src,
                            alt: img.alt || ''
                        });
                    });
                    
                    return data;
                }
            """)
            return json.dumps(data, indent=2)
        
        elif output_format == "txt":
            # Extract text content
            return await browser.page.evaluate("() => document.body.innerText")
        
        else:
            # Default to HTML
            return await browser.page.content()
    
    def _export_statistics(self):
        """Export scraping statistics"""
        stats_file = "scraping_stats.json"
        
        # Add proxy stats
        self.stats["proxy_stats"] = self.proxy_manager.get_proxy_stats()
        
        # Add timestamp
        self.stats["timestamp"] = time.time()
        
        try:
            # Load existing stats
            existing_stats = []
            if Path(stats_file).exists():
                with open(stats_file, 'r') as f:
                    existing_stats = json.load(f)
            
            # Append new stats
            existing_stats.append(self.stats)
            
            # Save
            with open(stats_file, 'w') as f:
                json.dump(existing_stats, f, indent=2)
            
            logger.info(f"📊 Statistics exported to {stats_file}")
        except Exception as e:
            logger.error(f"Failed to export statistics: {e}")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_basic_scraping():
    """Example: Basic scraping with all protections"""
    
    scraper = UnbeatableScraper({
        "headless": False,
        "use_proxies": True,
        "bypass_403": True
    })
    
    # Scrape a simple page
    result = await scraper.scrape(
        url="https://example.com",
        output_format="json"
    )
    
    if result["success"]:
        print(f"✅ Successfully scraped: {result['url']}")
        print(f"📊 Data: {result['data'][:500]}...")
        print(f"🔧 Metadata: {result['metadata']}")
    else:
        print(f"❌ Scraping failed: {result['errors']}")


# async def example_ai_guided_scraping():
    # """Example: AI-guided scraping with specific goal"""
    
    # scraper = UnbeatableScraper({
    #     "headless": True,
    #     "use_proxies": True,
    #     "solve_captchas": True
    # })
    
    # # Scrape with AI guidance
    # # result = await scraper.scrape(
    # #     url="https://www.similarweb.com/website/example.com/",
    # #     goal="Extract website traffic statistics and ranking data",
    # #     output_format="json"
    # # )
    
    # if result["success"]:
    #     print(f"✅ AI extraction successful")
    #     print(f"📊 Extracted data: {result['data']}")


async def example_batch_scraping():
    """Example: Batch scraping multiple URLs"""
    
    scraper = UnbeatableScraper({
        "headless": True,
        "use_proxies": True,
        "proxy_rotation_strategy": "smart",
        "fingerprint_rotation_interval": 300  # Rotate every 5 minutes
    })
    
    urls = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]
    
    results = []
    for url in urls:
        # Rotate between requests
        await asyncio.sleep(random.uniform(5, 15))
        
        result = await scraper.scrape(url, output_format="json")
        results.append(result)
        
        # Log progress
        success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
        print(f"📊 Progress: {len(results)}/{len(urls)} - Success rate: {success_rate:.1f}%")
    
    # Save results
    with open("batch_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Batch scraping complete. Results saved to batch_results.json")


async def example_with_custom_browser_data():
    """Example: Using custom browsers.json file"""
    
    # Ensure browser.json exists with thousands of user agents
    browser_data_path = "browsers.json"
    
    if not Path(browser_data_path).exists():
        print("⚠️ browsers.json not found. Creating sample...")
        sample_data = {
            "headers": {
                "chrome": {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9"
                }
            },
            "user_agents": {
                "desktop": {
                    "windows": {
                        "chrome": [
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
                            # Add thousands more...
                        ]
                    }
                }
            }
        }
        with open(browser_data_path, "w") as f:
            json.dump(sample_data, f, indent=2)
    
    scraper = UnbeatableScraper({
        "browser_data_path": browser_data_path,
        "headless": False,
        "use_proxies": True
    })
    
    result = await scraper.scrape("https://example.com")
    print(f"Result: {result}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point for testing"""
    
    print("🚀 Unbeatable Scraper Test Suite")
    print("=" * 50)
    
    # Test 1: Basic scraping
    print("\n📌 Test 1: Basic Scraping")
    await example_basic_scraping()
    
    # Test 2: AI-guided scraping
    print("\n📌 Test 2: AI-Guided Scraping")
    await example_ai_guided_scraping()
    
    # Test 3: Batch scraping
    print("\n📌 Test 3: Batch Scraping")
    await example_batch_scraping()
    
    print("\n✅ All tests complete!")


if __name__ == "__main__":
    import time
    import random
    
    # Run the test suite
    asyncio.run(main())


# ============================================================================
# CONFIGURATION TEMPLATES
# ============================================================================

# Configuration for maximum stealth
STEALTH_CONFIG = {
    "headless": False,  # Headless can be detected
    "use_proxies": True,
    "proxy_rotation_strategy": "smart",
    "fingerprint_rotation_interval": 300,
    "bypass_403": True,
    "solve_captchas": True,
    "save_screenshots": False,
    "enable_streaming": False
}

# Configuration for maximum speed
SPEED_CONFIG = {
    "headless": True,
    "use_proxies": False,
    "proxy_rotation_strategy": "none",
    "fingerprint_rotation_interval": 3600,
    "bypass_403": False,
    "solve_captchas": False,
    "save_screenshots": False,
    "enable_streaming": False
}

# Configuration for maximum reliability
RELIABILITY_CONFIG = {
    "headless": False,
    "use_proxies": True,
    "proxy_rotation_strategy": "weighted",
    "fingerprint_rotation_interval": 600,
    "bypass_403": True,
    "solve_captchas": True,
    "save_screenshots": True,
    "enable_streaming": True,
    "max_retries": 20
}


# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================

"""
SETUP INSTRUCTIONS:

1. Install required packages:
   pip install playwright asyncio aiohttp requests pillow fake-useragent

2. Install Playwright browsers:
   playwright install chromium

3. Set up environment variables:
   export GOOGLE_API_KEY="your_gemini_api_key"
   export WEBSHARE_USERNAME="your_username"
   export WEBSHARE_PASSWORD="your_password"
   export OXYLABS_USERNAME="your_username"
   export OXYLABS_PASSWORD="your_password"

4. Create browsers.json file with thousands of user agents:
   - Download from user agent databases
   - Or use the scraper to collect them

5. Create proxy list files (optional):
   - proxies.txt
   - residential_proxies.txt
   - mobile_proxies.txt

6. Run the scraper:
   python integration_guide.py

TIPS FOR MAXIMUM EFFECTIVENESS:

1. Rotate Everything:
   - Proxies every 5-10 requests
   - Fingerprints every 5-15 minutes
   - User agents on every context
   - Headers randomly

2. Add Delays:
   - Random delays between actions (1-5 seconds)
   - Longer delays after errors (10-30 seconds)
   - Human-like typing speeds
   - Natural mouse movements

3. Monitor and Adapt:
   - Track success rates per proxy
   - Log anti-bot detections
   - Save successful bypass techniques
   - Export statistics for analysis

4. Use Multiple Proxy Providers:
   - Combine residential, mobile, and datacenter
   - Use different providers for different sites
   - Keep backup proxy sources

5. Handle Failures Gracefully:
   - Retry with different configurations
   - Save partial data
   - Log detailed errors
   - Alert on critical failures
"""
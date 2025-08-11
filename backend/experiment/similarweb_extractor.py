import json
import asyncio
import re
import base64
import functools
from typing import Dict, List, Optional
import logging
from vision_model import MODEL

logger = logging.getLogger(__name__)

class SimilarWebExtractor:
    def __init__(self):
        self.vision_model = MODEL
        
    async def extract_similarweb_data_with_vision(self, browser, url: str) -> Dict:
        """Extract SimilarWeb data using pure AI vision - no HTML dependency"""
        try:
            logger.info(f"🔍 Starting vision-based SimilarWeb extraction from: {url}")
            
            # Wait for page to fully load and render
            await asyncio.sleep(5)
            
            # Get multiple screenshots with scrolling for comprehensive analysis
            screenshots = await self._capture_comprehensive_screenshots(browser)
            
            extracted_data = {
                'url': url,
                'domain': self._extract_domain_from_url(url),
                'extraction_timestamp': asyncio.get_event_loop().time(),
                'extraction_method': 'pure_vision_based',
                'data': {},
                'validation_results': {},
                'confidence_scores': {}
            }
            
            # Primary extraction using AI vision on full page
            primary_data = await self._vision_extract_metrics(screenshots['full_page'], url)
            extracted_data['data'].update(primary_data.get('metrics', {}))
            extracted_data['confidence_scores']['primary'] = primary_data.get('confidence', 0.0)
            
            # Secondary extraction on scrolled content for missed metrics
            if screenshots.get('scrolled'):
                secondary_data = await self._vision_extract_metrics(screenshots['scrolled'], url)
                # Merge non-duplicate data
                for key, value in secondary_data.get('metrics', {}).items():
                    if key not in extracted_data['data'] or extracted_data['data'][key] == 'Not found':
                        extracted_data['data'][key] = value
                extracted_data['confidence_scores']['secondary'] = secondary_data.get('confidence', 0.0)
            
            # Validate the page contains SimilarWeb analytics content
            validation_result = await self._validate_similarweb_page(screenshots['full_page'], url)
            extracted_data['validation_results'] = validation_result
            
            # Final extraction success assessment
            extracted_data['extraction_success'] = self._assess_extraction_success(
                extracted_data['data'], 
                validation_result
            )
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"❌ Vision-based SimilarWeb extraction failed: {e}")
            return {
                'url': url,
                'extraction_success': False,
                'extraction_method': 'pure_vision_based',
                'error': str(e),
                'data': {}
            }

    async def _capture_comprehensive_screenshots(self, browser) -> Dict[str, str]:
        """Capture multiple screenshots for comprehensive analysis"""
        screenshots = {}
        
        try:
            # Full page screenshot
            screenshot_bytes = await browser.page.screenshot(type='png', full_page=False)
            screenshots['full_page'] = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Scroll down to capture more content
            await browser.scroll_page("down", 800)
            await asyncio.sleep(3)
            
            # Second screenshot after scrolling
            screenshot_bytes = await browser.page.screenshot(type='png', full_page=False)
            screenshots['scrolled'] = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Scroll back up
            await browser.scroll_page("up", 800)
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.warning(f"⚠️ Error capturing comprehensive screenshots: {e}")
            
        return screenshots

    async def _vision_extract_metrics(self, screenshot_b64: str, url: str) -> Dict:
        """Use AI vision to extract SimilarWeb metrics"""
        try:
            # Convert screenshot for vision model
            screenshot_bytes = base64.b64decode(screenshot_b64)
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Comprehensive SimilarWeb extraction prompt
            extraction_prompt = f"""
            SIMILARWEB DATA EXTRACTION TASK:
            
            You are analyzing a SimilarWeb analytics page for website: {self._extract_domain_from_url(url)}
            URL: {url}
            
            **EXTRACT THESE SPECIFIC METRICS IF VISIBLE:**
            
            1. **Global Rank** - Look for "Global Rank" with a number (e.g., "#1,234" or "1,234")
            2. **Category Rank** - Look for "Category Rank" with a number
            3. **Country Rank** - Look for country-specific ranking (e.g., "United States #123")
            4. **Total Visits** - Monthly visits (e.g., "1.2M", "5.6B", "123K visits")
            5. **Bounce Rate** - Percentage (e.g., "45.67%")
            6. **Pages per Visit** - Average number (e.g., "2.34")
            7. **Visit Duration** - Time format (e.g., "2:34", "1m 23s")
            8. **Traffic Sources** - Organic search, direct, referrals percentages
            9. **Top Countries** - Geographic traffic distribution
            10. **Engagement Metrics** - Any other engagement data visible
            
            **VISUAL CUES TO LOOK FOR:**
            - Numbers with "#" prefix (rankings)
            - Large numbers with "K", "M", "B" suffixes (visits)
            - Percentages with "%" symbol
            - Time formats like "mm:ss"
            - Charts and graphs with data points
            - Metric labels and corresponding values
            
            **IMPORTANT INSTRUCTIONS:**
            - Only extract data that is CLEARLY VISIBLE and READABLE
            - If a metric is not visible, mark it as null
            - Pay attention to metric labels and their associated values
            - Look for both numerical and text-based data representations
            - Consider charts and visual data representations
            
            Return JSON format:
            {{
                "metrics": {{
                    "global_rank": "value or null",
                    "category_rank": "value or null", 
                    "country_rank": "value or null",
                    "total_visits": "value or null",
                    "bounce_rate": "value or null",
                    "pages_per_visit": "value or null",
                    "visit_duration": "value or null",
                    "direct_traffic": "value or null",
                    "search_traffic": "value or null",
                    "referral_traffic": "value or null",
                    "top_country": "value or null"
                }},
                "confidence": 0.0-1.0,
                "page_type": "similarweb_analytics|login_required|blocked|loading|error",
                "extraction_notes": "any important observations"
            }}
            """
            
            content = [extraction_prompt, image]
            response = await asyncio.to_thread(
                functools.partial(self.vision_model.generate_content, content)
            )
            
            # Parse response
            raw_text = response.text
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                return json.loads(raw_text[start:end])
            else:
                logger.warning("⚠️ Could not parse vision extraction response")
                return {"metrics": {}, "confidence": 0.0}
                
        except Exception as e:
            logger.error(f"❌ Vision metric extraction failed: {e}")
            return {"metrics": {}, "confidence": 0.0, "error": str(e)}

    async def _validate_similarweb_page(self, screenshot_b64: str, url: str) -> Dict:
        """Validate if we're on a proper SimilarWeb analytics page using AI vision"""
        try:
            screenshot_bytes = base64.b64decode(screenshot_b64)
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            validation_prompt = f"""
            SIMILARWEB PAGE VALIDATION TASK:
            
            You are validating if this webpage is a proper SimilarWeb analytics page.
            Expected URL pattern: {url}
            
            **CHECK FOR THESE SIMILARWEB PAGE INDICATORS:**
            
            ✅ **POSITIVE INDICATORS (page is valid):**
            - SimilarWeb logo or branding
            - "Global Rank" text or rankings with "#" symbols
            - "Total Visits" or traffic metrics
            - Analytics charts and graphs
            - Category rankings
            - Country-specific data
            - Traffic source breakdowns (Organic, Direct, Referral)
            - Engagement metrics (bounce rate, pages/visit, duration)
            - Professional analytics dashboard layout
            
            ❌ **NEGATIVE INDICATORS (page has issues):**
            - Login required messages ("Sign in to continue")
            - Account creation prompts ("Create account to see data")
            - Access denied or blocked messages
            - "Premium feature" or upgrade prompts
            - Blank or loading pages
            - Error messages (403, 404, 500)
            - Cloudflare protection pages
            - CAPTCHA challenges
            - Geographic restriction messages
            
            **ASSESSMENT CRITERIA:**
            - Are we on the actual analytics page with data?
            - Is the data freely accessible without login?
            - Are the core metrics visible?
            - Is this the expected SimilarWeb format?
            
            Return JSON:
            {{
                "is_valid_similarweb_page": true/false,
                "page_status": "valid_analytics|login_required|blocked|error|loading|premium_required",
                "found_indicators": ["list of positive indicators seen"],
                "blocking_issues": ["list of negative indicators seen"],
                "data_accessibility": "full|partial|none",
                "confidence": 0.0-1.0,
                "recommended_action": "continue|login|rotate_proxy|retry|abort"
            }}
            """
            
            content = [validation_prompt, image]
            response = await asyncio.to_thread(
                functools.partial(self.vision_model.generate_content, content)
            )
            
            raw_text = response.text
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                return json.loads(raw_text[start:end])
            else:
                return {
                    "is_valid_similarweb_page": False,
                    "page_status": "validation_error",
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"❌ Page validation failed: {e}")
            return {
                "is_valid_similarweb_page": False,
                "page_status": "validation_error",
                "error": str(e),
                "confidence": 0.0
            }

    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from SimilarWeb URL"""
        match = re.search(r'similarweb\.com/website/([^/]+)', url)
        return match.group(1) if match else 'unknown'

    def _assess_extraction_success(self, data: Dict, validation: Dict) -> bool:
        """Assess overall extraction success"""
        # Check if page is valid
        if not validation.get("is_valid_similarweb_page", False):
            logger.warning("⚠️ Page validation failed - not a valid SimilarWeb page")
            return False
        
        # Check for core metrics
        core_metrics = ['global_rank', 'total_visits']
        found_core_metrics = 0
        
        for metric in core_metrics:
            if metric in data and data[metric] and data[metric] != 'null':
                found_core_metrics += 1
        
        success = found_core_metrics > 0
        logger.info(f"📊 Extraction assessment: {found_core_metrics}/{len(core_metrics)} core metrics found")
        
        return success

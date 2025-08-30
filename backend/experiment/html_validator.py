import base64
from anti_bot_detection import AntiBotVisionModel

class SimilarWebValidator:
    def __init__(self):
        self.vision_model = AntiBotVisionModel()
    
    async def validate_page_before_saving(self, browser, domain: str) -> dict:
        """Validate page using vision before saving HTML"""
        try:
            screenshot_bytes = await browser.page.screenshot(type='png')
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            validation_prompt = f"""
            SIMILARWEB PAGE VALIDATION for domain: {domain}
            
            Analyze this SimilarWeb page and determine if it contains actual analytics data:
            
            LOOK FOR THESE POSITIVE INDICATORS:
            - Global Rank number (e.g., "#1,234" or "Rank: 1,234")
            - Total Visits metrics with numbers
            - Bounce Rate percentage
            - Pages per Visit number
            - Average Visit Duration
            - Traffic charts/graphs visible
            - Country/demographic data
            - Competitor analysis sections
            
            LOOK FOR THESE BLOCKING INDICATORS:
            - "Create account to continue" messages
            - "Sign up to see data" prompts
            - Login forms or barriers
            - "Upgrade to Pro" blocks
            - "No data available" messages
            - Blank/empty data sections
            - Error messages or 404 pages
            
            Return JSON:
            {{
                "is_valid_similarweb_page": true/false,
                "has_analytics_data": true/false,
                "blocking_type": "none|login_required|no_data|upgrade_needed|error",
                "found_metrics": ["list of metrics visible"],
                "confidence": 0.0-1.0,
                "should_save_html": true/false,
                "reason": "explanation of decision"
            }}
            """
            
            result = await self.vision_model.analyze_anti_bot_page(
                screenshot_b64, validation_prompt, browser.page.url
            )
            
            return result
            
        except Exception as e:
            return {
                "is_valid_similarweb_page": False,
                "has_analytics_data": False,
                "should_save_html": False,
                "error": str(e)
            }
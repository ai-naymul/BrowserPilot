import os
import base64
import google.generativeai as genai
import json
import asyncio
import functools
from PIL import Image
import io
import logging
class AntiBotVisionModel:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyBcCHKwA2PXZSuz_wuXc7lxaNJrBhJ9lMk"))
        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")
    
    async def analyze_anti_bot_page(self, screenshot_b64: str, detection_prompt: str, page_url: str) -> dict:
        """Analyze page screenshot to detect anti-bot systems"""
        try:
            # Convert base64 to PIL Image
            image_data = base64.b64decode(screenshot_b64)
            image = Image.open(io.BytesIO(image_data))
            
            # Compress image for token efficiency
            max_size = (1024, 768)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Create content for analysis
            content = [detection_prompt, image]
            
            # Send to vision model
            response = await asyncio.to_thread(
                functools.partial(self.model.generate_content, content)
            )
            
            raw_text = response.text
            print(f"🔍 Anti-bot detection response: {raw_text[:200]}...")
            
            # Parse JSON response
            try:
                start = raw_text.find('{')
                end = raw_text.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = raw_text[start:end]
                    result = json.loads(json_str)
                    return result
                else:
                    # Fallback parsing
                    return self._parse_fallback_response(raw_text, page_url)
                    
            except json.JSONDecodeError:
                return self._parse_fallback_response(raw_text, page_url)
                
        except Exception as e:
            print(f"❌ Error in anti-bot vision analysis: {e}")
            return {
                "is_anti_bot": False,
                "detection_type": "none",
                "confidence": 0.0,
                "description": f"Analysis failed: {str(e)}",
                "can_solve": False,
                "suggested_action": "retry"
            }
    
    def _parse_fallback_response(self, raw_text: str, page_url: str) -> dict:
        """Fallback parsing when JSON extraction fails"""
        text_lower = raw_text.lower()
        
        # Simple keyword detection as fallback
        anti_bot_keywords = [
            "cloudflare", "captcha", "verification", "access denied", 
            "blocked", "rate limit", "checking your browser", "security check",
            "automated traffic", "unusual activity"
        ]
        
        detected_keywords = [kw for kw in anti_bot_keywords if kw in text_lower]
        
        if detected_keywords:
            return {
                "is_anti_bot": True,
                "detection_type": detected_keywords[0],
                "confidence": 0.7,
                "description": f"Detected keywords: {', '.join(detected_keywords)}",
                "can_solve": "captcha" in detected_keywords,
                "suggested_action": "solve_captcha" if "captcha" in detected_keywords else "rotate_proxy"
            }
        
        return {
            "is_anti_bot": False,
            "detection_type": "none",
            "confidence": 0.5,
            "description": "No clear anti-bot indicators found",
            "can_solve": False,
            "suggested_action": "continue"
        }
    
    async def solve_captcha(self, screenshot_b64: str, page_url: str, captcha_type: str) -> dict:
        """Attempt to solve CAPTCHA using vision model"""
        try:
            # Convert base64 to PIL Image
            image_data = base64.b64decode(screenshot_b64)
            image = Image.open(io.BytesIO(image_data))
            
            captcha_prompt = f"""
            CAPTCHA SOLVING TASK:
            
            You are looking at a CAPTCHA challenge on: {page_url}
            CAPTCHA Type: {captcha_type}
            
            Analyze the image and provide the solution:
            
            For text CAPTCHAs:
            - Read and transcribe the text/numbers exactly as shown
            
            For image selection CAPTCHAs:
            - Identify which images match the requested criteria
            - Provide grid positions or image descriptions
            
            For math CAPTCHAs:
            - Solve the mathematical expression
            
            Respond with JSON:
            {{
                "can_solve": true/false,
                "solution_type": "text|selection|math|unknown",
                "solution": "the answer or list of selections",
                "confidence": 0.0-1.0,
                "instructions": "step by step what to do"
            }}
            """
            
            content = [captcha_prompt, image]
            
            response = await asyncio.to_thread(
                functools.partial(self.model.generate_content, content)
            )
            
            raw_text = response.text
            
            # Parse response
            try:
                start = raw_text.find('{')
                end = raw_text.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = raw_text[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            return {
                "can_solve": False,
                "solution_type": "unknown",
                "solution": "",
                "confidence": 0.0,
                "instructions": "Could not parse CAPTCHA solution"
            }
            
        except Exception as e:
            print(f"❌ Error solving CAPTCHA: {e}")
            return {
                "can_solve": False,
                "solution_type": "error",
                "solution": "",
                "confidence": 0.0,
                "instructions": f"CAPTCHA solving failed: {str(e)}"
            }
    
    async def analyze_similarweb_specific(self, screenshot_b64: str, page_url: str) -> dict:
        """SimilarWeb-specific anti-bot and accessibility detection"""
        try:
            image_data = base64.b64decode(screenshot_b64)
            image = Image.open(io.BytesIO(image_data))
            
            similarweb_prompt = f"""
            SIMILARWEB ANTI-BOT & ACCESSIBILITY DETECTION:
            
            You are analyzing a SimilarWeb page for anti-bot systems and access restrictions.
            URL: {page_url}
            
            **DETECT THESE SIMILARWEB-SPECIFIC ISSUES:**
            
            🚫 **ACCESS RESTRICTIONS:**
            - Login walls ("Sign in to continue", "Create account to see data")
            - Premium blocks ("Upgrade to Pro", "This feature requires subscription")
            - Geographic restrictions ("Not available in your region")
            - Rate limiting ("Too many requests", "Please wait")
            
            🛡️ **ANTI-BOT SYSTEMS:**
            - Cloudflare protection ("Checking your browser before accessing")
            - CAPTCHA challenges (reCAPTCHA, hCaptcha, image puzzles)
            - Bot detection warnings ("Automated traffic detected")
            - Browser verification pages ("Please verify you are human")
            
            📊 **DATA ACCESSIBILITY:**
            - Are analytics metrics visible? (Global Rank, Total Visits, etc.)
            - Is the page fully loaded with data?
            - Are there loading spinners or placeholder content?
            - Can we see charts, graphs, and traffic data?
            
            ✅ **POSITIVE INDICATORS:**
            - SimilarWeb analytics dashboard visible
            - Global rank, visits, and engagement metrics shown
            - Charts and data visualizations present
            - No blocking messages or restrictions
            
            Return JSON:
            {{
                "is_blocked": true/false,
                "block_type": "login_required|premium_block|cloudflare|captcha|rate_limit|geo_block|bot_detection|none",
                "data_accessible": "full|partial|none", 
                "confidence": 0.0-1.0,
                "description": "what you see on the page",
                "found_metrics": ["list of visible analytics metrics"],
                "blocking_elements": ["list of blocking UI elements"],
                "recommended_action": "continue|login|upgrade|rotate_proxy|solve_captcha|retry|abort"
            }}
            """
            
            content = [similarweb_prompt, image]
            response = await asyncio.to_thread(
                functools.partial(self.model.generate_content, content)
            )
            
            raw_text = response.text
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                return json.loads(raw_text[start:end])
            else:
                return {"is_blocked": False, "block_type": "none", "data_accessible": "full"}
                
        except Exception as e:
            logging.error(f"❌ SimilarWeb anti-bot detection error: {e}")
            return {"is_blocked": False, "block_type": "error", "error": str(e)}
        
    async def detect_fingerprintjs_challenge(self, screenshot_b64: str, page_url: str) -> dict:
            """Specifically detect fingerprintjs and advanced fingerprinting attempts"""
            try:
                image_data = base64.b64decode(screenshot_b64)
                image = Image.open(io.BytesIO(image_data))
                
                fingerprintjs_prompt = f"""
                FINGERPRINTJS DETECTION TASK:
                
                You are analyzing a webpage for advanced browser fingerprinting systems, specifically fingerprintjs or similar.
                URL: {page_url}
                
                Look for these indicators:
                1. **Page loading indefinitely** - fingerprintjs collecting data
                2. **Blank/white pages** - fingerprinting in progress
                3. **"Please wait" messages** - browser verification
                4. **Invisible content loading** - background fingerprinting
                5. **Delayed page rendering** - waiting for fingerprint completion
                6. **Browser compatibility messages** - fingerprint failed
                7. **"Verifying browser" text** - explicit fingerprinting
                
                CRITICAL: SimilarWeb uses sophisticated fingerprinting that may not show visible signs.
                If the page seems to be loading indefinitely or content is not appearing normally,
                this could indicate fingerprinting in progress.
                
                Respond with JSON:
                {{
                    "fingerprinting_detected": true/false,
                    "fingerprint_type": "fingerprintjs|advanced|basic|none",
                    "indicators": ["list of what you see"],
                    "confidence": 0.0-1.0,
                    "page_loading_normally": true/false,
                    "recommended_action": "wait|regenerate_fingerprint|rotate_proxy|continue"
                }}
                """
                
                content = [fingerprintjs_prompt, image]
                response = await asyncio.to_thread(
                    functools.partial(self.model.generate_content, content)
                )
                
                raw_text = response.text
                start = raw_text.find('{')
                end = raw_text.rfind('}') + 1
                
                if start != -1 and end > start:
                    return json.loads(raw_text[start:end])
                else:
                    return {
                        "fingerprinting_detected": False,
                        "fingerprint_type": "none",
                        "page_loading_normally": True,
                        "recommended_action": "continue"
                    }
                    
            except Exception as e:
                logging.error(f"❌ Fingerprintjs detection error: {e}")
                return {
                    "fingerprinting_detected": False,
                    "fingerprint_type": "error",
                    "recommended_action": "continue"
                }

import os
import base64
import google.generativeai as genai
import json
import asyncio
import functools
from PIL import Image
import io

class AntiBotVisionModel:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
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

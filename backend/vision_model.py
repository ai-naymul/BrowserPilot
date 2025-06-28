# backend/vision_model.py
import os
import base64
import google.generativeai as genai
from dotenv import load_dotenv
import json
import asyncio
import functools
from PIL import Image
import io

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Use the newer model that supports vision
MODEL = genai.GenerativeModel("gemini-2.0-flash-exp-image-generation")  # or "gemini-pro-vision"


# catch the cloudlfare or antibot system to rotate the proxy

SYSTEM_PROMPT = """
You control a web browser for data extraction.
Given the current page screenshot + URL + the user's high-level goal,
reply ONLY with a JSON dict containing:
action: "click" | "type" | "scroll" | "extract" | "done" | "navigate"
selector: an XPath/CSS selector (omit for done/scroll)
text: text to type (only for action=="type")
url: URL to navigate to (only for action=="navigate")

Examples:
{"action": "click", "selector": "button[type='submit']"}
{"action": "type", "selector": "#search-box", "text": "example query"}
{"action": "scroll"}
{"action": "extract"}
{"action": "done"}
"""

async def decide(img_bytes: bytes, url: str, goal: str) -> dict:
    """
    Send screenshot and context to Gemini, get back action decision
    """
    print(f"🤖 Starting Gemini API call for URL: {url}")
    print(f"📊 Image size: {len(img_bytes)} bytes")
    
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(img_bytes))
        print(f"🖼️ Image dimensions: {image.size}")
        
        # Create the prompt
        prompt = f"""URL: {url}
GOAL: {goal}

Based on the screenshot provided, determine the next action to take. Respond with a JSON object only."""
        
        # Method 1: Using PIL Image directly (recommended)
        content = [SYSTEM_PROMPT, prompt, image]
        
        print("📡 Sending request to Gemini API...")
        
        # Run the blocking call in a thread
        response = await asyncio.to_thread(
            functools.partial(MODEL.generate_content, content, stream=False)
        )
        
        print("✅ Received response from Gemini API")
        
        raw_text = response.text
        print(f"📝 Raw Gemini response: {raw_text}")
        
        # Initialize result dictionary
        result = {"action": "done"}
        
        # Extract JSON from response
        try:
            # Try to find JSON in the response
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = raw_text[start:end]
                result = json.loads(json_str)
                print(f"✅ Successfully parsed JSON: {result}")
            else:
                print("❌ No JSON found in response")
                result = {"action": "done"}
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"🔍 Attempted to parse: {raw_text[start:end] if 'start' in locals() else raw_text}")
            result = {"action": "done"}
        print(response)
        # Extract and add token usage information
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            print(f"📊 Token usage available:")
            print(f"   - Prompt tokens: {response.usage_metadata.prompt_token_count}")
            print(f"   - Response tokens: {response.usage_metadata.candidates_token_count}")
            print(f"   - Total tokens: {response.usage_metadata.total_token_count}")
            
            result['token_usage'] = {
                'prompt_tokens': response.usage_metadata.prompt_token_count,
                'response_tokens': response.usage_metadata.candidates_token_count,
                'total_tokens': response.usage_metadata.total_token_count
            }
        else:
            print("❌ No token usage metadata available")
            # Add fallback token usage for testing
            result['token_usage'] = {
                'prompt_tokens': 1000,  # Estimated values for testing
                'response_tokens': 50,
                'total_tokens': 1050
            }
        
        print(f"🎯 Final result with token usage: {result}")
        return result
            
    except Exception as e:
        print(f"❌ Error in decide function: {str(e)}")
        print(f"🔍 Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error result with fallback token usage
        return {
            "action": "done", 
            "error": str(e),
            "token_usage": {
                "prompt_tokens": 0,
                "response_tokens": 0,
                "total_tokens": 0
            }
        }

# Alternative implementation using base64 (if PIL method doesn't work)
async def decide_base64(img_bytes: bytes, url: str, goal: str) -> dict:
    """
    Alternative implementation using base64 encoding
    """
    try:
        # Encode image as base64
        b64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        # Create the prompt
        prompt = f"""URL: {url}
GOAL: {goal}

Based on the screenshot provided, determine the next action to take. Respond with a JSON object only."""
        
        # Create image part
        image_part = {
            "mime_type": "image/png",
            "data": b64_image
        }
        
        # Combine content
        content = [SYSTEM_PROMPT, prompt, image_part]
        
        # Generate response
        response = await asyncio.to_thread(
            functools.partial(MODEL.generate_content, content, stream=False)
        )
        
        raw_text = response.text
        print(f"Raw Gemini response (base64 method): {raw_text}")
        
        # Parse JSON response
        try:
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = raw_text[start:end]
                result = json.loads(json_str)
                
                token_usage = extract_token_usage(response)
        
                if token_usage:
                    print(f"📊 Token usage found: {token_usage}")
                    result['token_usage'] = token_usage
                else:
                    print("❌ No token usage metadata available")
                    result['token_usage'] = {
                        'prompt_tokens': 0,
                        'response_tokens': 0,
                        'total_tokens': 0
                    }
            else:
                return {"action": "done", "token_usage": {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}}
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error (base64 method): {e}")
            return {"action": "done", "token_usage": {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}}
            
    except Exception as e:
        print(f"Error in decide_base64 function: {str(e)}")
        return {"action": "done", "token_usage": {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}}

# extract token usage
def extract_token_usage(response):
    """
    Extract token usage from various possible locations in the response
    """
    try:
        # Method 1: Check usage_metadata attribute
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            print(f"📊 Found usage_metadata:")
            print(f"   - Response object: {response.usage_metadata}")
            return {
                'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                'response_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0)
            }
        
        # Method 2: Check if it's in the result
        if hasattr(response, 'result') and response.result:
            result_dict = response.result.to_dict() if hasattr(response.result, 'to_dict') else {}
            print(f"📊 Checking result dict: {result_dict.keys() if isinstance(result_dict, dict) else 'Not a dict'}")
            
            if 'usage_metadata' in result_dict:
                usage = result_dict['usage_metadata']
                return {
                    'prompt_tokens': usage.get('prompt_token_count', 0),
                    'response_tokens': usage.get('candidates_token_count', 0),
                    'total_tokens': usage.get('total_token_count', 0)
                }
        
        # Method 3: Check candidates for token_count
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'token_count'):
                print(f"📊 Found token_count in candidate: {candidate.token_count}")
                # This might not give us the breakdown, but it's something
                return {
                    'prompt_tokens': 0,  # Not available separately
                    'response_tokens': candidate.token_count,
                    'total_tokens': candidate.token_count
                }
        
        # Method 4: Try to access through the internal result
        if hasattr(response, 'result') and hasattr(response.result, 'candidates'):
            candidates = response.result.candidates
            if candidates and len(candidates) > 0:
                candidate = candidates[0]
                if hasattr(candidate, 'token_count'):
                    return {
                        'prompt_tokens': 0,
                        'response_tokens': candidate.token_count,
                        'total_tokens': candidate.token_count
                    }
        
        print("❌ No token usage found in any expected location")
        return None
        
    except Exception as e:
        print(f"❌ Error extracting token usage: {e}")
        return None
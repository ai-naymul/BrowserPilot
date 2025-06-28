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
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(img_bytes))
        
        # Create the prompt
        prompt = f"""URL: {url}
GOAL: {goal}

Based on the screenshot provided, determine the next action to take. Respond with a JSON object only."""
        
        # Method 1: Using PIL Image directly (recommended)
        content = [SYSTEM_PROMPT, prompt, image]
        
        # Run the blocking call in a thread
        response = await asyncio.to_thread(
            functools.partial(MODEL.generate_content, content, stream=False)
        )
        
        raw_text = response.text
        print(f"Raw Gemini response: {raw_text}")
        
        # Extract JSON from response
        try:
            # Try to find JSON in the response
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = raw_text[start:end]
                result = json.loads(json_str)
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    result['token_usage'] = {
                        'prompt_tokens': response.usage_metadata.prompt_token_count,
                        'response_tokens': response.usage_metadata.candidates_token_count,
                        'total_tokens': response.usage_metadata.total_token_count
                    }
                print(f"Parsed JSON: {result}")
                return result
            else:
                print("No JSON found in response")
                return {"action": "done"}
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Attempted to parse: {raw_text[start:end] if 'start' in locals() else raw_text}")
            return {"action": "done"}
            
    except Exception as e:
        print(f"Error in decide function: {str(e)}")
        print(f"Error type: {type(e)}")
        return {"action": "done"}

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
                return result
            else:
                return {"action": "done"}
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error (base64 method): {e}")
            return {"action": "done"}
            
    except Exception as e:
        print(f"Error in decide_base64 function: {str(e)}")
        return {"action": "done"}

# Test function to verify API connectivity
async def test_gemini_connection():
    """
    Test function to verify Gemini API is working
    """
    try:
        # Create a simple test image (white square)
        test_image = Image.new('RGB', (100, 100), color='white')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        # Test the API
        result = await decide(img_bytes, "https://example.com", "test connection")
        print(f"Test result: {result}")
        return result
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return None

# Debugging version with more verbose output
async def decide_debug(img_bytes: bytes, url: str, goal: str) -> dict:
    """
    Debug version with extensive logging
    """
    print(f"=== DEBUG decide function ===")
    print(f"Image bytes length: {len(img_bytes)}")
    print(f"URL: {url}")
    print(f"Goal: {goal}")
    print(f"API Key configured: {'Yes' if os.getenv('GOOGLE_API_KEY') else 'No'}")
    
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(img_bytes))
        print(f"Image size: {image.size}")
        print(f"Image mode: {image.mode}")
        
        # Create the prompt
        prompt = f"""URL: {url}
GOAL: {goal}

Based on the screenshot provided, determine the next action to take. Respond with a JSON object only."""
        
        print(f"Sending request to Gemini...")
        
        # Create content
        content = [SYSTEM_PROMPT, prompt, image]
        
        # Generate response with error handling
        try:
            response = await asyncio.to_thread(
                functools.partial(MODEL.generate_content, content, stream=False)
            )
            
            print(f"Response received successfully")
            print(f"Response type: {type(response)}")
            
            if hasattr(response, 'text'):
                raw_text = response.text
                print(f"Raw response text: {raw_text}")
            else:
                print(f"Response object: {response}")
                return {"action": "done"}
                
        except Exception as api_error:
            print(f"API call failed: {str(api_error)}")
            print(f"API error type: {type(api_error)}")
            return {"action": "done"}
        
        # Parse response
        try:
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = raw_text[start:end]
                print(f"Extracted JSON string: {json_str}")
                result = json.loads(json_str)
                print(f"Successfully parsed JSON: {result}")
                return result
            else:
                print("No valid JSON brackets found in response")
                return {"action": "done"}
                
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing failed: {str(json_error)}")
            return {"action": "done"}
            
    except Exception as e:
        print(f"General error in decide_debug: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return {"action": "done"}

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
MODEL = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")
# Much more concise system prompt
SYSTEM_PROMPT = """
You are a web automation agent that controls a browser using element indices (like browser-use).

You will receive:
1. A screenshot of the current webpage
2. Information about interactive elements with their indices
3. The user's goal/task

Each interactive element has:
- index: Numeric index to use for interactions (0, 1, 2, etc.)
- tag_name: HTML tag (button, input, a, etc.)
- text: Visible text content
- is_clickable: Whether element can be clicked
- is_input: Whether element accepts text input
- coordinates: x,y position for reference
- attributes: HTML attributes (class, id, href, etc.)

Reply ONLY with a JSON object containing:

CLICK ACTION:
{"action": "click", "index": 5, "reason": "clicking search button to submit query"}

TYPE ACTION:
{"action": "type", "index": 2, "text": "search query", "reason": "typing search query into search box"}

SCROLL ACTION:
{"action": "scroll", "direction": "down", "amount": 500, "reason": "scrolling to see more content"}

KEY PRESS ACTION:
{"action": "press_key", "key": "Enter", "reason": "pressing Enter to submit form"}

NAVIGATE ACTION:
{"action": "navigate", "url": "https://example.com", "reason": "navigating to specific URL"}

EXTRACT ACTION (when task is complete):
{"action": "extract", "reason": "task completed, extracting page content"}

DONE ACTION (when task is complete):
{"action": "done", "reason": "task completed successfully"}

IMPORTANT:
- Use the exact index number from the interactive element list
- Interactive elements are highlighted with red outlines and numbered labels
- Choose the most relevant element based on text content and purpose
- Explain your reasoning for each action
"""

async def decide(img_bytes: bytes, page_state, goal: str) -> dict:
    """Optimized AI decision with minimal token usage"""
    print(f"🤖 Optimized AI decision")
    print(f"📊 Image size: {len(img_bytes)} bytes")
    print(f"🎯 Goal: {goal}")
    print(f"🖱️ Interactive elements: {len(page_state.selector_map)}")

    try:
        # Compress image to reduce tokens
        image = Image.open(io.BytesIO(img_bytes))
        
        # Resize image to reduce tokens (critical optimization!)
        max_size = (1280, 800)  # Much smaller than 1280x800
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert back to bytes with compression
        compressed_buffer = io.BytesIO()
        image.save(compressed_buffer, format='JPEG', quality=70, optimize=True)
        compressed_image = Image.open(compressed_buffer)
        
        print(f"🖼️ Compressed image: {image.size} -> {compressed_image.size}")

        # Create minimal element information (HUGE token reduction!)
        interactive_elements = []
        for index in sorted(page_state.selector_map.keys())[:15]:  # Limit to 15 elements max
            elem = page_state.selector_map[index]
            
            # Only essential information
            element_data = {
                "i": index,  # Shortened key names
                "t": elem.tag_name,
                "txt": elem.text[:30] if elem.text else "",  # Truncate text
                "input": elem.is_input,
            }
            
            # Add minimal attributes only if relevant
            if elem.is_input and elem.placeholder:
                element_data["ph"] = elem.placeholder[:20]
            if elem.attributes.get("type"):
                element_data["type"] = elem.attributes["type"]
                
            interactive_elements.append(element_data)

        # Much shorter prompt
        prompt = f"""
Goal: {goal[:100]}  
URL: {page_state.url}

Elements: {json.dumps(interactive_elements)}

Next action?
"""

        content = [SYSTEM_PROMPT, prompt, compressed_image]

        # COUNT TOKENS BEFORE SENDING REQUEST
        print("📊 Counting tokens...")
        token_count_response = await asyncio.to_thread(
            functools.partial(MODEL.count_tokens, content)
        )


        input_tokens = token_count_response.total_tokens
        print(f"📊 Input tokens: {input_tokens}")

        print("📡 Sending optimized request to Gemini...")

        response = await asyncio.to_thread(
            functools.partial(MODEL.generate_content, content)
        )

        print("✅ Received response")
        raw_text = response.text
        print(f"📝 Response: {raw_text[:100]}...")
        
        #COUNT TOKENS FOR THE RESPONSE
        response_tokens = await count_response_tokens(raw_text)
        # Calculate total tokens
        total_tokens = input_tokens + response_tokens
        # Parse response
        result = {"action": "done"}
        try:
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = raw_text[start:end]
                result = json.loads(json_str)
                
                # Validate index
                if "index" in result and result["index"] not in page_state.selector_map:
                    print(f"❌ Invalid index {result['index']}")
                    result = {"action": "scroll", "direction": "down"}
                        
        except json.JSONDecodeError as e:
            print(f"❌ JSON error: {e}")
            result = {"action": "done"}

        # Add token usage
        # token_usage = extract_token_usage(response)
        token_usage = {
            'prompt_tokens': input_tokens,
            'response_tokens': response_tokens,
            'total_tokens': total_tokens
        }
        print(f"📊 Token usage: {token_usage}")
        print("Here is the response:", response)
        # import time
        # time.sleep(70)  # Short delay to avoid rate limits
        if token_usage:
            print(f"📊 Token usage: {token_usage}")
            result['token_usage'] = token_usage
        else:
            print("❌ No token usage found")
            result['token_usage'] = {'prompt_tokens': 0, 'response_tokens': 0, 'total_tokens': 0}

        print(f"🎯 Result: {result}")
        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "action": "done",
            "error": str(e),
            "token_usage": {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}
        }


async def count_response_tokens(response_text: str) -> int:
    """Count tokens in the response text"""
    try:
        # Count tokens for just the response text
        token_count_response = await asyncio.to_thread(
            functools.partial(MODEL.count_tokens, response_text)
        )
        return token_count_response.total_tokens
    except Exception as e:
        print(f"❌ Error counting response tokens: {e}")
        # Fallback: rough estimation (1 token ≈ 4 characters for English)
        return len(response_text) // 4



## This doesn't work with current response structure or generative model
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
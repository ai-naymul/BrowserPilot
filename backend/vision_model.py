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

MODEL = genai.GenerativeModel("gemini-2.0-flash-exp")

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
    """AI decision function compatible with browser-use"""
    print(f"🤖 Starting AI decision with browser-use compatible approach")
    print(f"📊 Image size: {len(img_bytes)} bytes")
    print(f"🎯 Goal: {goal}")
    print(f"📋 Available elements: {len(page_state.elements)}")
    print(f"🖱️ Interactive elements: {len(page_state.selector_map)}")

    try:
        image = Image.open(io.BytesIO(img_bytes))
        print(f"🖼️ Image dimensions: {image.size}")

        # Create element information for AI (only interactive elements)
        interactive_elements = []
        for index, elem in page_state.selector_map.items():
            interactive_elements.append({
                "index": index,
                "tag_name": elem.tag_name,
                "text": elem.text[:80] if elem.text else "",
                "is_clickable": elem.is_clickable,
                "is_input": elem.is_input,
                "input_type": elem.input_type,
                "placeholder": elem.placeholder,
                "coordinates": elem.center_coordinates,
                "key_attributes": {
                    "class": elem.attributes.get("class", ""),
                    "id": elem.attributes.get("id", ""),
                    "href": elem.attributes.get("href", ""),
                    "type": elem.attributes.get("type", ""),
                    "name": elem.attributes.get("name", "")
                }
            })

        # Sort by index for consistent ordering
        interactive_elements.sort(key=lambda x: x["index"])

        element_summary = f"""
INTERACTIVE ELEMENTS (Total: {len(interactive_elements)}):
{json.dumps(interactive_elements, indent=2)}
"""

        prompt = f"""
CURRENT PAGE:
URL: {page_state.url}
Title: {page_state.title}

USER GOAL: {goal}

{element_summary}

Analyze the screenshot and interactive elements to determine the next action.
Look for elements highlighted with red outlines and numbered labels.
Use the exact index number from the list above.

Respond with a JSON object only.
"""

        content = [SYSTEM_PROMPT, prompt, image]

        print("📡 Sending request to Gemini API...")

        response = await asyncio.to_thread(
            functools.partial(MODEL.generate_content, content)
        )

        print("✅ Received response from Gemini API")
        raw_text = response.text
        print(f"📝 Raw Gemini response: {raw_text}")

        result = {"action": "done"}

        try:
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = raw_text[start:end]
                result = json.loads(json_str)
                print(f"✅ Successfully parsed JSON: {result}")
                
                # Validate index if provided
                if "index" in result:
                    index = result["index"]
                    if index in page_state.selector_map:
                        element = page_state.selector_map[index]
                        print(f"✅ Element index {index} found: {element.text[:50]}...")
                    else:
                        print(f"❌ Element index {index} not found in selector map")
                        available_indices = list(page_state.selector_map.keys())
                        print(f"Available indices: {available_indices}")
                        result = {"action": "scroll", "direction": "down", "reason": "Looking for more interactive elements"}
                        
            else:
                print("❌ No JSON found in response")
                result = {"action": "done", "reason": "No valid JSON in AI response"}

        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            result = {"action": "done", "reason": "JSON parsing failed"}

        # Add token usage
        token_usage = extract_token_usage(response)
        if token_usage:
            print(f"📊 Token usage extracted: {token_usage}")
            result['token_usage'] = token_usage
        else:
            print("❌ No token usage found in response")
            result['token_usage'] = {
                'prompt_tokens': 0,
                'response_tokens': 0,
                'total_tokens': 0
            }

        print(f"🎯 Final result: {result}")
        return result

    except Exception as e:
        print(f"❌ Error in decide function: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "action": "done",
            "error": str(e),
            "reason": "AI processing failed",
            "token_usage": {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}
        }


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
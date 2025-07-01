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

# Universal system prompt - works for ANY website
SYSTEM_PROMPT = """
You are a universal web automation agent that can navigate and interact with ANY website to accomplish user goals.

You will receive:
1. A screenshot of the current webpage
2. Interactive elements with indices
3. The user's specific goal/task
4. Current URL and page context

Your job is to analyze the current page and determine the BEST next action to accomplish the user's goal, regardless of what type of website this is.

AVAILABLE ACTIONS:

CLICK - Click on any interactive element:
{"action": "click", "index": N, "reason": "specific reason for clicking this element"}

TYPE - Input text into any input field:
{"action": "type", "index": N, "text": "text to enter", "reason": "reason for entering this text"}

SCROLL - Navigate the page vertically:
{"action": "scroll", "direction": "down|up", "amount": 300-800, "reason": "reason for scrolling"}

PRESS_KEY - Press any keyboard key:
{"action": "press_key", "key": "Enter|Tab|Escape|Space|etc", "reason": "reason for key press"}

NAVIGATE - Go to a specific URL (only if needed):
{"action": "navigate", "url": "https://example.com", "reason": "reason for navigation"}

EXTRACT - Save current page content (when goal is achieved):
{"action": "extract", "reason": "goal accomplished, extracting relevant information"}

DONE - Mark task as complete:
{"action": "done", "reason": "task successfully completed"}

DECISION RULES:
1. **Analyze the user's goal** - understand what information/action they want
2. **Assess current page** - what type of page is this? What can be done here?
3. **Choose best action** - what single action moves closest to the goal?
4. **Be adaptive** - different sites have different patterns, adapt accordingly

WEBSITE TYPE DETECTION:
- **Search engines**: Look for search boxes, enter queries, click results
- **E-commerce**: Find products, navigate categories, view details
- **Social media**: Look for profiles, posts, navigation menus
- **Forms/Applications**: Fill required fields, submit forms
- **Content sites**: Navigate articles, extract information
- **Databases/APIs**: Use search/filter features, extract data

INTERACTION STRATEGY:
- **First time on page**: Look for main navigation, search, or primary actions
- **Search results**: Click on most relevant results for user's goal
- **Product pages**: Look for details, specifications, reviews as needed
- **Profile/About pages**: Extract relevant information about person/entity
- **Forms**: Fill systematically, validate inputs
- **Lists/Tables**: Use pagination, sorting, filtering as needed

EXTRACTION TIMING:
- Extract when you have found the specific information the user requested
- Don't extract from search results - click through to detailed pages first
- For research tasks: navigate to authoritative sources before extracting
- For data collection: ensure you're on pages with comprehensive information

REMEMBER: Be universal - work with ANY website structure, ANY content type, ANY user goal.
"""

async def decide(img_bytes: bytes, page_state, goal: str) -> dict:
    """Universal AI decision making for any website"""
    print(f"🤖 Universal AI decision")
    print(f"📊 Image size: {len(img_bytes)} bytes")
    print(f"🎯 Goal: {goal}")
    print(f"🖱️ Interactive elements: {len(page_state.selector_map)}")
    print(f"📍 Current URL: {page_state.url}")

    try:
        # Compress image efficiently
        image = Image.open(io.BytesIO(img_bytes))
        max_size = (1280, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        compressed_buffer = io.BytesIO()
        image.save(compressed_buffer, format='JPEG', quality=75, optimize=True)
        compressed_image = Image.open(compressed_buffer)

        # Create comprehensive element information (dynamic based on content)
        interactive_elements = []
        max_elements = min(20, len(page_state.selector_map))  # Adaptive limit
        
        for index in sorted(page_state.selector_map.keys())[:max_elements]:
            elem = page_state.selector_map[index]
            
            # Dynamic element description based on context
            element_data = {
                "index": index,
                "tag": elem.tag_name,
                "text": elem.text[:60] if elem.text else "",
                "clickable": elem.is_clickable,
                "input": elem.is_input,
            }
            
            # Add contextual attributes dynamically
            if elem.attributes.get("href"):
                element_data["link"] = elem.attributes["href"][:100]
            if elem.attributes.get("placeholder"):
                element_data["placeholder"] = elem.attributes["placeholder"][:30]
            if elem.attributes.get("type"):
                element_data["type"] = elem.attributes["type"]
            if elem.attributes.get("class"):
                # Extract meaningful class hints
                classes = elem.attributes["class"].lower()
                if any(hint in classes for hint in ["search", "login", "submit", "button", "nav", "menu"]):
                    element_data["class_hint"] = classes[:50]
            if elem.attributes.get("id"):
                element_data["id"] = elem.attributes["id"][:30]
                
            interactive_elements.append(element_data)

        # Detect website type dynamically
        website_type = detect_website_type(page_state.url, page_state.title, interactive_elements)
        
        # Create dynamic context-aware prompt
        prompt = f"""
USER GOAL: {goal}

CURRENT CONTEXT:
- URL: {page_state.url}
- Page Title: {page_state.title}
- Website Type: {website_type}
- Available Elements: {len(interactive_elements)}

INTERACTIVE ELEMENTS:
{json.dumps(interactive_elements, indent=1)}

Based on the user's goal and current page context, what is the BEST next action?
Consider the website type and adapt your strategy accordingly.
"""

        content = [SYSTEM_PROMPT, prompt, compressed_image]

        # Count tokens and send request
        token_count_response = await asyncio.to_thread(
            functools.partial(MODEL.count_tokens, content)
        )
        input_tokens = token_count_response.total_tokens

        response = await asyncio.to_thread(
            functools.partial(MODEL.generate_content, content)
        )

        raw_text = response.text
        response_tokens = await count_response_tokens(raw_text)
        total_tokens = input_tokens + response_tokens

        # Parse response with validation
        result = parse_ai_response(raw_text, page_state, goal, website_type)

        # Add token usage
        result['token_usage'] = {
            'prompt_tokens': input_tokens,
            'response_tokens': response_tokens,
            'total_tokens': total_tokens
        }
        
        print(f"🎯 Universal Result: {result}")
        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "action": "done",
            "error": str(e),
            "token_usage": {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}
        }

def detect_website_type(url: str, title: str, elements: list) -> str:
    """Dynamically detect website type based on URL and content"""
    url_lower = url.lower()
    title_lower = title.lower()
    
    # Search engines
    if any(domain in url_lower for domain in ["google.com", "bing.com", "duckduckgo.com", "yahoo.com"]):
        if "/search" in url_lower or any("search" in elem.get("text", "").lower() for elem in elements):
            return "search_results"
        return "search_engine"
    
    # E-commerce
    if any(domain in url_lower for domain in ["amazon", "ebay", "shopify", "etsy", "alibaba"]):
        return "ecommerce"
    if any(word in title_lower for word in ["shop", "store", "buy", "cart", "product"]):
        return "ecommerce"
    
    # Social media
    if any(domain in url_lower for domain in ["linkedin", "twitter", "facebook", "instagram", "github"]):
        return "social_profile"
    
    # Forms/Applications
    if any(elem.get("input") for elem in elements if len([e for e in elements if e.get("input")]) > 3):
        return "form_application"
    
    # Content/News sites
    if any(word in title_lower for word in ["news", "article", "blog", "post"]):
        return "content_site"
    
    # Company/Organization
    if any(word in title_lower for word in ["company", "corp", "inc", "ltd", "about", "contact"]):
        return "company_site"
    
    # Database/Directory
    if any(word in url_lower for word in ["directory", "database", "catalog", "listing"]):
        return "database_site"
    
    return "general_website"

def parse_ai_response(raw_text: str, page_state, goal: str, website_type: str) -> dict:
    """Parse AI response with intelligent fallbacks"""
    try:
        # Extract JSON from response
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = raw_text[start:end]
            result = json.loads(json_str)
            
            # Validate action
            valid_actions = ["click", "type", "scroll", "press_key", "navigate", "extract", "done"]
            if result.get("action") not in valid_actions:
                return get_fallback_action(page_state, goal, website_type)
            
            # Validate index if present
            if "index" in result and result["index"] not in page_state.selector_map:
                print(f"❌ Invalid index {result['index']}")
                return get_fallback_action(page_state, goal, website_type)
            
            return result
        else:
            return get_fallback_action(page_state, goal, website_type)
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON error: {e}")
        return get_fallback_action(page_state, goal, website_type)

def get_fallback_action(page_state, goal: str, website_type: str) -> dict:
    """Intelligent fallback based on context"""
    goal_lower = goal.lower()
    
    # Look for obvious search boxes
    for index, elem in page_state.selector_map.items():
        if elem.is_input and any(word in elem.text.lower() + str(elem.attributes).lower() 
                                for word in ["search", "query", "find"]):
            if "search" in goal_lower:
                return {"action": "type", "index": index, "text": extract_search_query(goal), 
                       "reason": "Found search box for user query"}
    
    # Look for relevant links based on goal
    for index, elem in page_state.selector_map.items():
        if elem.is_clickable and elem.text:
            if any(word in elem.text.lower() for word in goal_lower.split()[:3]):
                return {"action": "click", "index": index, 
                       "reason": f"Found relevant link: {elem.text[:30]}"}
    
    # Default behaviors by website type
    if website_type == "search_results":
        # Click first meaningful result
        for index, elem in page_state.selector_map.items():
            if elem.is_clickable and len(elem.text) > 10:
                return {"action": "click", "index": index, 
                       "reason": "Clicking search result for more details"}
    
    # Generic fallback
    return {"action": "scroll", "direction": "down", "amount": 400, 
           "reason": "Exploring page to find relevant content"}

def extract_search_query(goal: str) -> str:
    """Extract search query from user goal"""
    # Remove common command words
    stop_words = ["go", "to", "search", "for", "find", "get", "save", "extract", "info", "about"]
    words = goal.split()
    query_words = [word for word in words if word.lower() not in stop_words]
    return " ".join(query_words[:6])  # Limit query length

async def count_response_tokens(response_text: str) -> int:
    """Count tokens in the response text"""
    try:
        token_count_response = await asyncio.to_thread(
            functools.partial(MODEL.count_tokens, response_text)
        )
        return token_count_response.total_tokens
    except Exception as e:
        print(f"❌ Error counting response tokens: {e}")
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
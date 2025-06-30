import asyncio, json, base64, re
from pathlib import Path
from typing import Literal
from backend.browser_controller import BrowserController
from backend.vision_model import decide
from backend.universal_extractor import UniversalExtractor

async def run_agent(job_id: str, prompt: str, fmt: Literal["txt","md","json","html","csv","pdf"],
                   headless: bool, proxy: dict | None, enable_streaming: bool = False):
    """Universal agent that works with any website"""
    from backend.main import broadcast, OUTPUT_DIR, register_streaming_session
    
    print(f"🚀 Starting universal agent for job {job_id}")
    print(f"📋 Goal: {prompt}")
    print(f"🌐 Format: {fmt}")
    
    # Initialize universal extractor
    extractor = UniversalExtractor()
    
    async with BrowserController(headless, proxy, enable_streaming) as browser:
        # Register streaming session
        if enable_streaming:
            await register_streaming_session(job_id, browser)
        
        # Smart navigation - detect if URL is in prompt
        url_match = re.search(r"https?://[\w\-\.]+[^\s]*", prompt)
        if url_match:
            start_url = url_match.group(0).rstrip('".,;')
            print(f"🔗 Found URL in prompt: {start_url}")
            await browser.goto(start_url)
        else:
            # Determine best starting point based on goal
            start_url = determine_starting_url(prompt)
            print(f"🔗 Starting at: {start_url}")
            await browser.goto(start_url)
        
        await broadcast(job_id, {"status": "started", "initial_url": browser.page.url})
        
        # Dynamic limits based on task complexity
        max_steps = determine_max_steps(prompt)
        consecutive_scrolls = 0
        max_consecutive_scrolls = 3
        extraction_attempts = 0
        max_extraction_attempts = 2
        
        print(f"🎯 Running for max {max_steps} steps")
        
        # Main universal loop
        for step in range(max_steps):
            print(f"\n🔄 Step {step + 1}/{max_steps}")
            
            try:
                page_state = await browser.get_page_state(include_screenshot=True)
                print(f"📊 Found {len(page_state.selector_map)} interactive elements")
                print(f"📍 Current: {page_state.url}")
                
                # Send info to frontend
                await broadcast(job_id, {
                    "type": "page_info",
                    "step": step + 1,
                    "url": page_state.url,
                    "title": page_state.title,
                    "interactive_elements": len(page_state.selector_map)
                })
                
                if page_state.screenshot:
                    await broadcast(job_id, {
                        "type": "screenshot",
                        "screenshot": page_state.screenshot
                    })
                
            except Exception as e:
                print(f"❌ Page state failed: {e}")
                continue
            
            # Handle empty pages
            if len(page_state.selector_map) == 0:
                if consecutive_scrolls < max_consecutive_scrolls:
                    print("⚠️ No interactive elements, trying to scroll...")
                    await browser.scroll_page("down", 400)
                    consecutive_scrolls += 1
                    continue
                else:
                    print("⚠️ No elements found after scrolling, may need to navigate elsewhere")
                    break
            
            # AI decision making
            try:
                screenshot_bytes = base64.b64decode(page_state.screenshot)
                decision = await decide(screenshot_bytes, page_state, prompt)
                
                print(f"🤖 AI Decision: {decision.get('action')} - {decision.get('reason', 'No reason')}")
                
                await broadcast(job_id, {
                    "type": "decision", 
                    "step": step + 1,
                    "decision": decision
                })
                
            except Exception as e:
                print(f"❌ AI decision failed: {e}")
                continue
            
            # Execute action
            action = decision.get("action")
            print(f"⚡ Executing: {action}")
            
            try:
                if action == "click":
                    index = decision.get("index")
                    if index is not None and index in page_state.selector_map:
                        elem = page_state.selector_map[index]
                        print(f"🖱️ Clicking: {elem.text[:50]}...")
                        await browser.click_element_by_index(index, page_state)
                        consecutive_scrolls = 0
                        extraction_attempts = 0  # Reset on navigation
                        await asyncio.sleep(2)  # Wait for page changes
                    else:
                        print(f"❌ Invalid click index: {index}")
                        
                elif action == "type":
                    index = decision.get("index")
                    text = decision.get("text", "")
                    if index is not None and index in page_state.selector_map and text:
                        elem = page_state.selector_map[index]
                        print(f"⌨️ Typing '{text}' into: {elem.text[:30]}...")
                        await browser.input_text_by_index(index, text, page_state)
                        consecutive_scrolls = 0
                        await asyncio.sleep(1)
                    else:
                        print(f"❌ Invalid type parameters: index={index}, text='{text}'")
                        
                elif action == "scroll":
                    direction = decision.get("direction", "down")
                    amount = decision.get("amount", 400)
                    print(f"📜 Scrolling {direction} by {amount}px")
                    await browser.scroll_page(direction, amount)
                    consecutive_scrolls += 1
                    
                    if consecutive_scrolls >= max_consecutive_scrolls:
                        print("⚠️ Too many scrolls, trying page end")
                        await browser.press_key("End")
                        consecutive_scrolls = 0
                        
                elif action == "press_key":
                    key = decision.get("key", "Enter")
                    print(f"🔑 Pressing key: {key}")
                    await browser.press_key(key)
                    consecutive_scrolls = 0
                    await asyncio.sleep(2)
                    
                elif action == "navigate":
                    url = decision.get("url", "")
                    if url and url.startswith("http"):
                        print(f"🔗 Navigating to: {url}")
                        await browser.goto(url)
                        consecutive_scrolls = 0
                        extraction_attempts = 0
                        await asyncio.sleep(2)
                    else:
                        print(f"❌ Invalid navigation URL: {url}")
                        
                elif action == "extract":
                    extraction_attempts += 1
                    if extraction_attempts <= max_extraction_attempts:
                        print("🔍 Starting intelligent extraction...")
                        await broadcast(job_id, {
                            "type": "extraction", 
                            "status": "starting",
                            "attempt": extraction_attempts
                        })
                        
                        # Use universal extraction
                        content = await extractor.extract_intelligent_content(browser, prompt, fmt)
                        
                        # Save content
                        output_file = OUTPUT_DIR / f"{job_id}.output"
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(content)
                        
                        print(f"💾 Universal content saved to {output_file}")
                        await broadcast(job_id, {
                            "type": "extraction", 
                            "status": "completed",
                            "file_size": len(content)
                        })
                        break
                    else:
                        print("⚠️ Maximum extraction attempts reached")
                        break
                    
                elif action == "done":
                    print("✅ Task marked as complete by AI")
                    break
                    
                else:
                    print(f"⚠️ Unknown action: {action}")
                    
            except Exception as e:
                print(f"❌ Action execution failed: {e}")
                await asyncio.sleep(1)
            
            # Small delay between actions
            await asyncio.sleep(0.5)
        
        # Final extraction if not done yet
        if extraction_attempts == 0:
            print("🔍 Performing final extraction...")
            try:
                content = await extractor.extract_intelligent_content(browser, prompt, fmt)
                output_file = OUTPUT_DIR / f"{job_id}.output"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"💾 Final content saved to {output_file}")
            except Exception as e:
                print(f"❌ Final extraction failed: {e}")
        
        await broadcast(job_id, {"status": "finished"})

def determine_starting_url(prompt: str) -> str:
    """Determine the best starting URL based on the user's goal"""
    prompt_lower = prompt.lower()
    
    # Search-related tasks
    if any(word in prompt_lower for word in ["search", "find", "look for", "google"]):
        return "https://www.google.com"
    
    # LinkedIn profiles
    if "linkedin" in prompt_lower or "professional profile" in prompt_lower:
        return "https://www.linkedin.com"
    
    # GitHub profiles
    if "github" in prompt_lower or "code repository" in prompt_lower:
        return "https://www.github.com"
    
    # Shopping/e-commerce
    if any(word in prompt_lower for word in ["buy", "purchase", "product", "price", "amazon"]):
        return "https://www.amazon.com"
    
    # News
    if any(word in prompt_lower for word in ["news", "article", "breaking"]):
        return "https://news.google.com"
    
    # Default to Google for most tasks
    return "https://www.google.com"

def determine_max_steps(prompt: str) -> int:
    """Determine max steps based on task complexity"""
    prompt_lower = prompt.lower()
    
    # Simple extraction tasks
    if any(word in prompt_lower for word in ["extract", "get info", "save", "download"]):
        return 15
    
    # Complex research tasks
    if any(word in prompt_lower for word in ["research", "analyze", "compare", "comprehensive"]):
        return 25
    
    # Form filling or multi-step processes
    if any(word in prompt_lower for word in ["fill", "submit", "register", "apply", "multiple"]):
        return 20
    
    # Default
    return 20

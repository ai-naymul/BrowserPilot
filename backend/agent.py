import asyncio, json, base64, re
from pathlib import Path
from typing import Literal
from backend.browser_controller import BrowserController
from backend.vision_model import decide

async def run_agent(job_id: str, prompt: str, fmt: Literal["txt","md","json","html"],
                   headless: bool, proxy: dict | None, enable_streaming: bool = False):
    """Agent with CDP streaming support"""
    from backend.main import broadcast, OUTPUT_DIR, register_streaming_session
    
    print(f"🚀 Starting agent for job {job_id} with streaming={enable_streaming}")
    
    async with BrowserController(headless, proxy, enable_streaming) as browser:
        # Register streaming session
        if enable_streaming:
            await register_streaming_session(job_id, browser)
        
        # Navigate
        url_match = re.search(r"https?://\S+", prompt)
        if url_match:
            await browser.goto(url_match.group(0).rstrip('"'))
        else:
            await browser.goto("https://www.google.com")
        
        await broadcast(job_id, {"status": "started"})
        
        consecutive_scrolls = 0
        max_consecutive_scrolls = 3
        
        # Main loop
        for step in range(30):
            print(f"\n🔄 Step {step + 1}/30")
            
            try:
                page_state = await browser.get_page_state(include_screenshot=True)
                print(f"📊 Using {len(page_state.selector_map)} interactive elements")
                
                # Send info to frontend
                await broadcast(job_id, {
                    "type": "page_info",
                    "url": page_state.url,
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
            
            # Skip AI call if no interactive elements
            if len(page_state.selector_map) == 0 and consecutive_scrolls > 0:
                print("⚠️ No elements found, scrolling...")
                await browser.scroll_page("down", 300)
                consecutive_scrolls += 1
                continue
            
            # AI decision
            try:
                screenshot_bytes = base64.b64decode(page_state.screenshot)
                decision = await decide(screenshot_bytes, page_state, prompt)
                await broadcast(job_id, {"type": "decision", "decision": decision})
            except Exception as e:
                print(f"❌ AI decision failed: {e}")
                continue
            
            # Execute action
            action = decision.get("action")
            print(f"⚡ Action: {action}")
            
            try:
                if action == "click":
                    index = decision.get("index")
                    if index is not None:
                        await browser.click_element_by_index(index, page_state)
                        consecutive_scrolls = 0
                        
                elif action == "type":
                    index = decision.get("index")
                    text = decision.get("text", "")
                    if index is not None and text:
                        await browser.input_text_by_index(index, text, page_state)
                        consecutive_scrolls = 0
                        
                elif action == "scroll":
                    await browser.scroll_page(decision.get("direction", "down"), 300)
                    consecutive_scrolls += 1
                    
                    if consecutive_scrolls >= max_consecutive_scrolls:
                        print("⚠️ Too many scrolls, switching strategy")
                        await browser.press_key("End")
                        consecutive_scrolls = 0
                        
                elif action == "press_key":
                    await browser.press_key(decision.get("key", "Enter"))
                    consecutive_scrolls = 0
                    
                elif action == "done":
                    print("✅ Task completed")
                    break
                    
            except Exception as e:
                print(f"❌ Action failed: {e}")
            
            await asyncio.sleep(1)
        
        # Extract final content
        try:
            content = await extract_page_content(browser, fmt)
            output_file = OUTPUT_DIR / f"{job_id}.output"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"💾 Content saved to {output_file}")
        except Exception as e:
            print(f"❌ Failed to extract content: {e}")
        
        await broadcast(job_id, {"status": "finished"})

async def extract_page_content(browser: BrowserController, fmt: str) -> str:
    """Extract page content in the specified format"""
    try:
        html = await browser.page.content()
        if fmt == "html":
            return html
        
        if fmt == "txt":
            text_content = await browser.page.inner_text("body")
            return text_content.strip()
        
        if fmt == "md":
            import bs4, markdownify
            soup = bs4.BeautifulSoup(html, "lxml")
            for tag in soup.find_all(True):
                if tag.name not in ["h1","h2","h3","h4","h5","h6","p","li","ul","ol","a","strong","em","div","span"]:
                    tag.decompose()
            return markdownify.markdownify(str(soup))
        
        if fmt == "json":
            page_state = await browser.get_page_state(include_screenshot=False, highlight_elements=False)
            return json.dumps({
                "url": page_state.url,
                "title": page_state.title,
                "elements": [{
                    "index": elem.index,
                    "tag": elem.tag_name,
                    "text": elem.text[:100],
                    "type": "interactive" if elem.index is not None else "text",
                    "coordinates": elem.center_coordinates,
                    "attributes": elem.attributes
                } for elem in page_state.elements[:50]]
            }, indent=2)
        
        return html
        
    except Exception as e:
        print(f"❌ Failed to extract content: {e}")
        return f"Error extracting content: {str(e)}"

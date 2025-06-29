import asyncio, json, base64, re
from pathlib import Path
from typing import Literal
from backend.browser_controller import BrowserController
from backend.vision_model import decide

async def run_agent(job_id: str, prompt: str, fmt: Literal["txt","md","json","html"],
                   headless: bool, proxy: dict | None, enable_vnc: bool = False):
    """
    Browser-use compatible agent with index-based element interaction
    """
    from backend.main import broadcast, OUTPUT_DIR, register_vnc_session

    print(f"🚀 Starting agent for job {job_id}")
    print(f"📝 Prompt: {prompt}")
    print(f"📄 Format: {fmt}")
    print(f"👁️ Headless: {headless}")
    print(f"📺 VNC Enabled: {enable_vnc}")

    async with BrowserController(headless, proxy, enable_vnc) as browser:
        # Register VNC session if enabled
        if enable_vnc:
            vnc_info = browser.get_vnc_info()
            await register_vnc_session(job_id, vnc_info)
            print(f"🖥️ VNC Info: {vnc_info}")

        # Try to navigate to a URL explicitly mentioned in the user's prompt
        url_match = re.search(r"https?://\S+", prompt)
        if url_match:
            initial_url = url_match.group(0).rstrip('"')
            print(f"🌐 Navigating to: {initial_url}")
            await browser.goto(initial_url)
        else:
            # Start with Google if no URL specified in prompt
            print("🌐 No URL found in prompt, starting with Google")
            await browser.goto("https://www.google.com")

        await broadcast(job_id, {"status": "started"})
        print(f"📡 Broadcast: started")

        # Main agent loop with max 30 steps
        for step in range(30):
            print(f"\n🔄 Step {step + 1}/30 for job {job_id}")

            # Get page state with element extraction
            try:
                page_state = await browser.get_page_state(include_screenshot=True, highlight_elements=True)
                print(f"📊 Found {len(page_state.elements)} total elements")
                print(f"🖱️ Interactive elements: {len(page_state.selector_map)}")
                print(f"🔗 Current URL: {page_state.url}")
                print(f"📄 Page title: {page_state.title}")
                
                # Send page info to frontend
                await broadcast(job_id, {
                    "type": "page_info",
                    "url": page_state.url,
                    "title": page_state.title,
                    "total_elements": len(page_state.elements),
                    "interactive_elements": len(page_state.selector_map)
                })

                # Send screenshot to frontend
                if page_state.screenshot:
                    await broadcast(job_id, {
                        "type": "screenshot", 
                        "screenshot": page_state.screenshot
                    })
                    print(f"📡 Broadcast: screenshot and page info sent")

            except Exception as e:
                print(f"❌ Failed to get page state: {e}")
                await broadcast(job_id, {
                    "type": "error",
                    "error": f"Failed to get page state: {str(e)}"
                })
                continue

            # Get decision from AI
            print(f"🤖 Requesting decision from AI...")
            try:
                # Convert screenshot to bytes for vision model
                screenshot_bytes = base64.b64decode(page_state.screenshot)
                
                # Send page state to AI
                decision = await decide(screenshot_bytes, page_state, prompt)
                print(f"🎯 Decision received: {decision}")

                # Broadcast the decision to frontend
                await broadcast(job_id, {
                    "type": "decision",
                    "decision": decision
                })
                print(f"📡 Broadcast: decision sent")

            except Exception as e:
                print(f"❌ Failed to get AI decision: {e}")
                await broadcast(job_id, {
                    "type": "error", 
                    "error": f"AI decision failed: {str(e)}"
                })
                continue

            # Execute the decision
            action = decision.get("action")
            print(f"⚡ Executing action: {action}")

            try:
                if action == "click":
                    index = decision.get("index")
                    if index is not None:
                        print(f"🖱️ Clicking element at index {index}")
                        success = await browser.click_element_by_index(index, page_state)
                        if success:
                            print(f"✅ Successfully clicked element {index}")
                        else:
                            print(f"❌ Failed to click element {index}")
                    else:
                        print(f"❌ No index provided for click action")
                        
                elif action == "type":
                    index = decision.get("index")
                    text = decision.get("text", "")
                    if index is not None and text:
                        print(f"⌨️ Typing '{text}' into element {index}")
                        success = await browser.input_text_by_index(index, text, page_state)
                        if success:
                            print(f"✅ Successfully typed into element {index}")
                        else:
                            print(f"❌ Failed to type into element {index}")
                    else:
                        print(f"❌ Invalid type parameters: index={index}, text='{text}'")
                        
                elif action == "scroll":
                    direction = decision.get("direction", "down")
                    amount = decision.get("amount", 500)
                    print(f"📜 Scrolling {direction} by {amount}px")
                    await browser.scroll_page(direction, amount)
                    
                elif action == "press_key":
                    key = decision.get("key", "Enter")
                    print(f"⌨️ Pressing key: {key}")
                    await browser.press_key(key)
                    
                elif action == "navigate":
                    url = decision.get("url")
                    print(f"🌐 Navigating to: {url}")
                    await browser.goto(url)
                    
                elif action == "extract":
                    print(f"📄 Extracting content as {fmt}")
                    content = await extract_page_content(browser, fmt)
                    file_path = OUTPUT_DIR / f"{job_id}.output"
                    file_path.write_text(content, encoding="utf-8")
                    print(f"💾 Content saved to: {file_path}")
                    
                    await broadcast(job_id, {
                        "type": "status",
                        "status": "saved"
                    })
                    print(f"📡 Broadcast: saved")
                    break
                    
                elif action == "done":
                    print(f"✅ Agent completed task")
                    break

            except Exception as e:
                print(f"❌ Action execution failed: {e}")
                await broadcast(job_id, {
                    "type": "error",
                    "error": f"Action execution failed: {str(e)}"
                })

            # Wait before next iteration
            await asyncio.sleep(2)

        await broadcast(job_id, {
            "type": "status",
            "status": "finished"
        })
        print(f"📡 Broadcast: finished")
        print(f"🏁 Agent finished for job {job_id}")


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
                "elements": [
                    {
                        "index": elem.index,
                        "tag": elem.tag_name,
                        "text": elem.text[:100],
                        "type": "interactive" if elem.index is not None else "text",
                        "coordinates": elem.center_coordinates,
                        "attributes": elem.attributes
                    }
                    for elem in page_state.elements[:50]
                ]
            }, indent=2)
        
        return html
        
    except Exception as e:
        print(f"❌ Failed to extract content: {e}")
        return f"Error extracting content: {str(e)}"

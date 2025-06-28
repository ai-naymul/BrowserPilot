import asyncio, json
from pathlib import Path
from typing import Literal

from backend.browser_controller import BrowserController
from backend.vision_model import decide

async def run_agent(job_id: str, prompt: str, fmt: Literal["txt","md","json","html"],
                    headless: bool, proxy: dict | None, enable_vnc: bool = False):
    """
    High-level orchestration loop with VNC support:
    1. Setup browser with optional VNC
    2. Ask Gemini until it says "done" or "extract"
    3. If action=="extract" → grab page content, format, save
    """
    from backend.main import broadcast, OUTPUT_DIR, register_vnc_session
    import base64, re
    
    print(f"🚀 Starting agent for job {job_id}")
    print(f"📝 Prompt: {prompt}")
    print(f"📄 Format: {fmt}")
    print(f"👁️ Headless: {headless}")
    print(f"📺 VNC Enabled: {enable_vnc}")
    
    async with BrowserController(headless, proxy, enable_vnc) as b:
        # Register VNC session if enabled
        if enable_vnc:
            vnc_info = b.get_vnc_info()
            await register_vnc_session(job_id, vnc_info)
            print(f"🖥️ VNC Info: {vnc_info}")
        
        # Try to navigate to a URL explicitly mentioned in the user's prompt
        url_match = re.search(r"https?://\S+", prompt)
        if url_match:
            initial_url = url_match.group(0).rstrip('"')
            print(f"🌐 Navigating to: {initial_url}")
            await b.page.goto(initial_url)
        else:
            print("🌐 No URL found in prompt, starting with blank page")
            await b.page.goto("about:blank")
        
        await broadcast(job_id, {"status":"started"})
        print(f"📡 Broadcast: started")

        # Main agent loop with max 30 steps
        for step in range(30):
            print(f"\n🔄 Step {step + 1}/30 for job {job_id}")
            
            # Take screenshot (always send for fallback/debugging)
            png = await b.screenshot()
            print(f"📸 Screenshot taken: {len(png)} bytes")
            
            # Send screenshot to frontend
            await broadcast(job_id, {
                "type": "screenshot",
                "screenshot": base64.b64encode(png).decode()
            })
            print(f"📡 Broadcast: screenshot sent")
            
            # Get decision from Gemini
            print(f"🤖 Requesting decision from Gemini...")
            decision = await decide(png, b.page.url, prompt)
            print(f"🎯 Decision received: {decision}")
            
            # Broadcast the decision to frontend (including token usage)
            await broadcast(job_id, {
                "type": "decision",
                "decision": decision
            })
            print(f"📡 Broadcast: decision sent with token usage: {decision.get('token_usage', 'None')}")
            
            action = decision.get("action")
            print(f"⚡ Executing action: {action}")
            
            if action == "click":
                selector = decision.get("selector")
                print(f"🖱️ Clicking: {selector}")
                try:
                    await b.click(selector)
                except Exception as e:
                    print(f"❌ Click failed: {e}")
                    await broadcast(job_id, {
                        "type": "error",
                        "error": f"Click failed: {str(e)}"
                    })
                    
            elif action == "type":
                selector = decision.get("selector")
                text = decision.get("text", "")
                print(f"⌨️ Typing '{text}' into: {selector}")
                try:
                    await b.type(selector, text)
                except Exception as e:
                    print(f"❌ Type failed: {e}")
                    await broadcast(job_id, {
                        "type": "error", 
                        "error": f"Type failed: {str(e)}"
                    })
                    
            elif action == "scroll":
                print(f"📜 Scrolling")
                try:
                    await b.scroll()
                except Exception as e:
                    print(f"❌ Scroll failed: {e}")
                    
            elif action == "navigate":
                url = decision.get("url")
                print(f"🌐 Navigating to: {url}")
                try:
                    await b.page.goto(url, timeout=15000)
                except Exception as e:
                    print(f"❌ Navigation failed: {e}")
                    await broadcast(job_id, {
                        "type": "error",
                        "error": f"Navigation failed: {str(e)}"
                    })
                    
            elif action == "extract":
                print(f"📄 Extracting content as {fmt}")
                try:
                    content = await extract(b.page, fmt)
                    file_path = OUTPUT_DIR / f"{job_id}.output"
                    file_path.write_text(content, encoding="utf-8")
                    print(f"💾 Content saved to: {file_path}")
                    await broadcast(job_id, {
                        "type": "status",
                        "status": "saved"
                    })
                    print(f"📡 Broadcast: saved")
                    break
                except Exception as e:
                    print(f"❌ Extract failed: {e}")
                    await broadcast(job_id, {
                        "type": "error",
                        "error": f"Extract failed: {str(e)}"
                    })
                    
            elif action == "done":
                print(f"✅ Agent completed task")
                break

            await asyncio.sleep(1)   # polite delay

        await broadcast(job_id, {
            "type": "status",
            "status": "finished"
        })
        print(f"📡 Broadcast: finished")
        print(f"🏁 Agent finished for job {job_id}")

async def extract(page, fmt: str) -> str:
    """Extract page content in the specified format"""
    html = await page.content()
    if fmt == "html":
        print(f"Extracting HTML content for {page.url}")
        return html
    if fmt == "txt":
        return (await page.inner_text("body")).strip()
    if fmt == "md":
        # Quick heuristic – keep <h1-h6>, <p>, <li>
        import bs4, markdownify
        soup = bs4.BeautifulSoup(html, "lxml")
        for tag in soup.find_all(True):
            if tag.name not in ["h1","h2","h3","h4","h5","h6","p","li","ul","ol","a","strong","em"]:
                tag.decompose()
        return markdownify.markdownify(str(soup))
    if fmt == "json":
        return json.dumps({"url": page.url, "html": html})
    return html
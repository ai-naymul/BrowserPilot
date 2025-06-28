import asyncio, json
from pathlib import Path
from typing import Literal

from backend.browser_controller import BrowserController
from backend.vision_model import decide
# from backend.main import broadcast, OUTPUT_DIR 


# TODO: rotate proxy if its being detected by cloudflare or other antibot system
# TODO: using xvbf to run the browser in headless mode wherre it the window won't be visible, its crucial for those anti bot systems which detects the browser is running in headless mode or not

async def run_agent(job_id: str, prompt: str, fmt: Literal["txt","md","json","html"],
                    headless: bool, proxy: dict | None):
    """
    High-level orchestration loop:
    1. Ask Gemini until it says "done" or "extract"
    2. If action=="extract" → grab page content, format, save
    """
    from backend.main import broadcast, OUTPUT_DIR
    import base64, re
    
    print(f"🚀 Starting agent for job {job_id}")
    print(f"📝 Prompt: {prompt}")
    print(f"📄 Format: {fmt}")
    print(f"👁️ Headless: {headless}")
    
    async with BrowserController(headless, proxy) as b:
        # Try to navigate to a URL explicitly mentioned in the user's prompt (first http/https found)
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

        # naive loop with max 30 steps
        for step in range(30):
            print(f"\n🔄 Step {step + 1}/30 for job {job_id}")
            
            # Take screenshot
            png = await b.screenshot()
            print(f"📸 Screenshot taken: {len(png)} bytes")
            
            # Send screenshot to frontend
            await broadcast(job_id, {"screenshot": base64.b64encode(png).decode()})
            print(f"📡 Broadcast: screenshot sent")
            
            # Get decision from Gemini
            print(f"🤖 Requesting decision from Gemini...")
            decision = await decide(png, b.page.url, prompt)
            print(f"🎯 Decision received: {decision}")
            
            # Broadcast the decision to frontend (including token usage)
            await broadcast(job_id, {"decision": decision})
            print(f"📡 Broadcast: decision sent with token usage: {decision.get('token_usage', 'None')}")
            
            action = decision.get("action")
            print(f"⚡ Executing action: {action}")
            
            if action == "click":
                selector = decision.get("selector")
                print(f"🖱️ Clicking: {selector}")
                await b.click(selector)
            elif action == "type":
                selector = decision.get("selector")
                text = decision.get("text", "")
                print(f"⌨️ Typing '{text}' into: {selector}")
                await b.type(selector, text)
            elif action == "scroll":
                print(f"📜 Scrolling")
                await b.scroll()
            elif action == "navigate":
                url = decision.get("url")
                print(f"🌐 Navigating to: {url}")
                await b.page.goto(url, timeout=15000)
            elif action == "extract":
                print(f"📄 Extracting content as {fmt}")
                content = await extract(b.page, fmt)
                file_path = OUTPUT_DIR / f"{job_id}.output"
                file_path.write_text(content, encoding="utf-8")
                print(f"💾 Content saved to: {file_path}")
                await broadcast(job_id, {"status":"saved"})
                print(f"📡 Broadcast: saved")
                break
            elif action == "done":
                print(f"✅ Agent completed task")
                break

            await asyncio.sleep(1)   # polite delay

        await broadcast(job_id, {"status":"finished"})
        print(f"📡 Broadcast: finished")
        print(f"🏁 Agent finished for job {job_id}")

async def extract(page, fmt: str) -> str:
    html = await page.content()
    if fmt == "html":
        print(f"Extracting HTML content for {page.url}")
        return html
    if fmt == "txt":
        return (await page.inner_text("body")).strip()
    if fmt == "md":
        # quick heuristic – keep <h1-h6>, <p>, <li>
        import bs4, markdownify
        soup = bs4.BeautifulSoup(html, "lxml")
        for tag in soup.find_all(True):
            if tag.name not in ["h1","h2","h3","h4","h5","h6","p","li","ul","ol","a","strong","em"]:
                tag.decompose()
        return markdownify.markdownify(str(soup))
    if fmt == "json":
        return json.dumps({"url": page.url, "html": html})
    return html
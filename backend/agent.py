# backend/agent.py
import asyncio, json
from pathlib import Path
from typing import Literal

from backend.browser_controller import BrowserController
from backend.vision_model import decide
# from backend.main import broadcast, OUTPUT_DIR   # avoid circular import

async def run_agent(job_id: str, prompt: str, fmt: Literal["txt","md","json","html"],
                    headless: bool, proxy: dict | None):
    """
    High-level orchestration loop:
    1. Ask Gemini until it says "done" or "extract"
    2. If action=="extract" → grab page content, format, save
    """
    from backend.main import broadcast, OUTPUT_DIR
    import base64, re
    async with BrowserController(headless, proxy) as b:
        # Try to navigate to a URL explicitly mentioned in the user's prompt (first http/https found)
        url_match = re.search(r"https?://\S+", prompt)
        if url_match:
            await b.page.goto(url_match.group(0).rstrip('"'))
        else:
            await b.page.goto("about:blank")
        await broadcast(job_id, {"status":"started"})

        # naive loop with max 30 steps
        for _ in range(30):
            print(f"Job here 30 line")
            png = await b.screenshot()
            await broadcast(job_id, {"screenshot": base64.b64encode(png).decode()})
            decision = await decide(png, b.page.url, prompt)
            print(f"Decision for {job_id}: {decision}")
            # try:
            #     decision = json.loads(decision_json)
            # except Exception:
            #     decision = {"action":"done"}
            print(f"Parsed decision: {decision}")
            action = decision.get("action")
            print(f"Action: {action}")
            if action == "click":
                await b.click(decision["selector"])
            elif action == "type":
                await b.type(decision["selector"], decision.get("text",""))
            elif action == "scroll":
                await b.scroll()
            elif action == "navigate":
                await b.page.goto(decision["url"], timeout=15000)
            elif action == "extract":
                content = await extract(b.page, fmt)
                file_path = OUTPUT_DIR / f"{job_id}.output"
                file_path.write_text(content, encoding="utf-8")
                await broadcast(job_id, {"status":"saved"})
                break
            elif action == "done":
                break

            await asyncio.sleep(1)   # polite delay

        await broadcast(job_id, {"status":"finished"})

async def extract(page, fmt: str) -> str:
    html = await page.content()
    if fmt == "html":
        print(f"Extracting HTML content for {page.url}")
        print(f"HTML : {html}")
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
# backend/browser_controller.py
import asyncio, base64
from pathlib import Path
from playwright.async_api import async_playwright

class BrowserController:
    def __init__(self, headless: bool, proxy: dict | None):
        self.headless = headless
        self.proxy   = proxy
        self.play    = None
        self.browser = None
        self.page    = None

    async def __aenter__(self):
        self.play = await async_playwright().start()
        self.browser = await self.play.chromium.launch(headless=self.headless, proxy=self.proxy)
        self.page = await self.browser.new_page(viewport={"width": 1280, "height": 800})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.browser.close()
        await self.play.stop()

    async def screenshot(self) -> bytes:
        return await self.page.screenshot(full_page=False)

    async def click(self, selector: str):
        await self.page.locator(selector).first.click(timeout=5000)

    async def type(self, selector: str, text: str):
        await self.page.fill(selector, text)

    async def scroll(self, amount: int = 1000):
        await self.page.mouse.wheel(0, amount)

    async def goto(self, url: str, **kwargs):
        await self.page.goto(url, **kwargs)
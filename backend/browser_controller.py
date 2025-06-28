import asyncio
import subprocess
import os
from playwright.async_api import async_playwright

class BrowserController:
    def __init__(self, headless: bool, proxy: dict | None, enable_vnc: bool = False):
        self.headless = headless
        self.proxy = proxy
        self.enable_vnc = enable_vnc
        self.play = None
        self.browser = None
        self.page = None
        self.vnc_process = None
        self.xvfb_process = None
        self.display_num = None
        self.vnc_port = None

    async def __aenter__(self):
        if self.enable_vnc and not self.headless:
            await self._setup_vnc()
        
        self.play = await async_playwright().start()
        
        # Browser launch options
        launch_options = {
            "headless": self.headless,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        }
        
        if self.proxy:
            launch_options["proxy"] = self.proxy
            
        # If VNC is enabled and we're using Xvfb, set the display
        if self.enable_vnc and self.display_num:
            os.environ['DISPLAY'] = f":{self.display_num}"
            
        self.browser = await self.play.chromium.launch(**launch_options)
        self.page = await self.browser.new_page(viewport={"width": 1280, "height": 800})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.browser.close()
        await self.play.stop()
        await self._cleanup_vnc()

    async def _setup_vnc(self):
        """Setup Xvfb and VNC server for real-time browser streaming"""
        try:
            # Find available display number
            self.display_num = self._find_free_display()
            self.vnc_port = 5900 + self.display_num
            
            print(f"🖥️ Setting up VNC on display :{self.display_num}, port {self.vnc_port}")
            
            # Start Xvfb (X Virtual Framebuffer)
            xvfb_cmd = [
                "Xvfb", f":{self.display_num}",
                "-screen", "0", "1280x800x24",
                "-ac", "+extension", "GLX",
                "+render", "-noreset"
            ]
            
            self.xvfb_process = subprocess.Popen(
                xvfb_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for Xvfb to start
            await asyncio.sleep(2)
            
            # Start VNC server
            vnc_cmd = [
                "x11vnc",
                "-display", f":{self.display_num}",
                "-rfbport", str(self.vnc_port),
                "-forever",
                "-nopw",
                "-quiet",
                "-bg"
            ]
            
            self.vnc_process = subprocess.Popen(
                vnc_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for VNC server to start
            await asyncio.sleep(2)
            
            print(f"✅ VNC server started on port {self.vnc_port}")
            
        except Exception as e:
            print(f"❌ Failed to setup VNC: {e}")
            await self._cleanup_vnc()
            raise

    def _find_free_display(self):
        """Find a free X display number"""
        for i in range(1, 100):
            if not os.path.exists(f"/tmp/.X{i}-lock"):
                return i
        raise RuntimeError("No free X display found")

    async def _cleanup_vnc(self):
        """Clean up VNC and Xvfb processes"""
        if self.vnc_process:
            try:
                self.vnc_process.terminate()
                self.vnc_process.wait(timeout=5)
            except:
                self.vnc_process.kill()
            self.vnc_process = None
            
        if self.xvfb_process:
            try:
                self.xvfb_process.terminate()
                self.xvfb_process.wait(timeout=5)
            except:
                self.xvfb_process.kill()
            self.xvfb_process = None
            
        # Clean up X11 lock file
        if self.display_num:
            lock_file = f"/tmp/.X{self.display_num}-lock"
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except:
                    pass

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
        
    def get_vnc_info(self):
        """Get VNC connection information"""
        if self.enable_vnc and self.vnc_port:
            return {
                "enabled": True,
                "port": self.vnc_port,
                "display": self.display_num,
                "url": f"ws://localhost:{self.vnc_port + 1000}"  # WebSocket proxy port
            }
        return {"enabled": False}
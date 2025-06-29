import asyncio
import subprocess
import os
import logging
import json
import base64
from playwright.async_api import async_playwright, Page
from typing import Optional, Dict, List, Any, Tuple
import hashlib
from dataclasses import dataclass, asdict
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ElementInfo:
    """Comprehensive information about a DOM element"""
    id: str  # Unique identifier for the element
    tag_name: str
    xpath: str
    css_selector: str
    text: str
    attributes: Dict[str, str]
    is_clickable: bool
    is_input: bool
    input_type: Optional[str] = None
    placeholder: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    center_coordinates: Optional[Dict[str, float]] = None
    is_visible: bool = True
    element_hash: Optional[str] = None
    parent_text: Optional[str] = None
    nearby_text: Optional[str] = None

class PageState:
    """Represents the current state of a web page"""
    def __init__(self, url: str, title: str, elements: List[ElementInfo], screenshot: Optional[str] = None):
        self.url = url
        self.title = title
        self.elements = elements
        self.screenshot = screenshot
        self.clickable_elements = [e for e in elements if e.is_clickable]
        self.input_elements = [e for e in elements if e.is_input]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "elements": [asdict(e) for e in self.elements],
            "screenshot": self.screenshot,
            "clickable_count": len(self.clickable_elements),
            "input_count": len(self.input_elements)
        }

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
        self.wm_process = None
        self.display_num = None
        self.vnc_port = 5901
        self.element_counter = 0

    async def __aenter__(self):
        if self.enable_vnc:
            await self._setup_vnc()
            if self.display_num:
                os.environ['DISPLAY'] = f":{self.display_num}"

        self.play = await async_playwright().start()

        launch_options = {
            "headless": False if self.enable_vnc else self.headless,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu" if not self.enable_vnc else "--use-gl=swiftshader",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--window-size=1280,800",
                "--window-position=0,0",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-first-run",
                "--disable-default-apps"
            ]
        }

        if self.proxy:
            launch_options["proxy"] = self.proxy

        self.browser = await self.play.chromium.launch(**launch_options)
        self.page = await self.browser.new_page(viewport={"width": 1280, "height": 800})
        
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.browser:
            await self.browser.close()
        if self.play:
            await self.play.stop()
        await self._cleanup_vnc()

    async def _setup_vnc(self):
        """Setup Xvfb and VNC server for real-time browser streaming"""
        try:
            self.display_num = self._find_free_display()
            self.vnc_port = 5901 + self.display_num

            print(f"🖥️ Setting up VNC on display :{self.display_num}, port {self.vnc_port}")

            xvfb_cmd = [
                "Xvfb", f":{self.display_num}",
                "-screen", "0", "1280x800x24",
                "-ac", "+extension", "GLX",
                "+render", "-noreset",
                "-dpi", "96"
            ]

            self.xvfb_process = subprocess.Popen(
                xvfb_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            await asyncio.sleep(3)
            os.environ['DISPLAY'] = f":{self.display_num}"
            
            wm_cmd = ["fluxbox", "-display", f":{self.display_num}"]
            self.wm_process = subprocess.Popen(
                wm_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            await asyncio.sleep(2)

            vnc_cmd = [
                "x11vnc",
                "-display", f":{self.display_num}",
                "-rfbport", str(self.vnc_port),
                "-forever",
                "-nopw",
                "-quiet",
                "-bg",
                "-shared",
                "-cursor", "arrow"
            ]

            self.vnc_process = subprocess.Popen(
                vnc_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            await asyncio.sleep(3)
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
        processes = [self.vnc_process, self.wm_process, self.xvfb_process]
        
        for process in processes:
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass
        
        if self.display_num:
            lock_file = f"/tmp/.X{self.display_num}-lock"
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except:
                    pass

    async def goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000):
        """Navigate to a URL with proper waiting"""
        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            await asyncio.sleep(2)  # Wait for dynamic content
            logger.info(f"Successfully navigated to: {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise

    async def get_comprehensive_page_state(self, include_screenshot: bool = True) -> PageState:
        """Get comprehensive information about the current page state"""
        try:
            # Wait for page to be ready
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            
            # Get page info
            url = self.page.url
            title = await self.page.title()
            
            # Get screenshot if requested
            screenshot = None
            if include_screenshot:
                screenshot_bytes = await self.page.screenshot(full_page=False)
                screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Get all interactive elements
            elements = await self._extract_all_elements()
            
            return PageState(url, title, elements, screenshot)
            
        except Exception as e:
            logger.error(f"Failed to get page state: {e}")
            return PageState("", "", [], None)

    async def _extract_all_elements(self) -> List[ElementInfo]:
        """Extract all interactive elements from the page"""
        try:
            js_code = """
            () => {
                const elements = [];
                let elementId = 0;
                
                // Define what makes an element interactive
                const interactiveSelectors = [
                    'a[href]', 'button', 'input', 'select', 'textarea',
                    '[onclick]', '[role="button"]', '[role="link"]', '[role="tab"]',
                    '[tabindex]', 'label', '[contenteditable="true"]', 'summary'
                ];
                
                // Get all potentially interactive elements
                const allElements = document.querySelectorAll('*');
                
                allElements.forEach((el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    
                    // Check if element is visible and has reasonable size
                    const isVisible = rect.width > 0 && rect.height > 0 && 
                                    style.visibility !== 'hidden' && 
                                    style.display !== 'none' &&
                                    rect.top < window.innerHeight && 
                                    rect.bottom > 0;
                    
                    if (!isVisible) return;
                    
                    const tagName = el.tagName.toLowerCase();
                    const isClickable = el.matches(interactiveSelectors.join(',')) || 
                                      el.onclick || 
                                      style.cursor === 'pointer' ||
                                      el.hasAttribute('data-testid') ||
                                      el.className.includes('btn') ||
                                      el.className.includes('button') ||
                                      el.className.includes('link');
                    
                    const isInput = ['input', 'textarea', 'select'].includes(tagName) ||
                                   el.contentEditable === 'true';
                    
                    // Include all clickable elements and visible text elements
                    const hasText = el.textContent && el.textContent.trim().length > 0;
                    const isImportant = isClickable || isInput || 
                                      (hasText && el.textContent.trim().length < 200);
                    
                    if (isImportant) {
                        const xpath = getXPath(el);
                        const cssSelector = getCSSSelector(el);
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        
                        // Get nearby text for context
                        const nearbyText = getNearbyText(el);
                        const parentText = el.parentElement ? 
                            el.parentElement.textContent?.trim().substring(0, 100) : '';
                        
                        elements.push({
                            id: `element_${elementId++}`,
                            tag_name: tagName,
                            xpath: xpath,
                            css_selector: cssSelector,
                            text: el.textContent?.trim() || el.value || el.alt || '',
                            attributes: Array.from(el.attributes).reduce((acc, attr) => {
                                acc[attr.name] = attr.value;
                                return acc;
                            }, {}),
                            is_clickable: isClickable,
                            is_input: isInput,
                            input_type: el.type || null,
                            placeholder: el.placeholder || null,
                            bounding_box: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                top: rect.top,
                                bottom: rect.bottom,
                                left: rect.left,
                                right: rect.right
                            },
                            center_coordinates: {
                                x: centerX,
                                y: centerY
                            },
                            is_visible: isVisible,
                            parent_text: parentText,
                            nearby_text: nearbyText
                        });
                    }
                });
                
                function getXPath(element) {
                    if (element.id !== '') {
                        return `//*[@id="${element.id}"]`;
                    }
                    if (element === document.body) {
                        return '/html/body';
                    }
                    
                    let ix = 0;
                    const siblings = element.parentNode ? element.parentNode.childNodes : [];
                    for (let i = 0; i < siblings.length; i++) {
                        const sibling = siblings[i];
                        if (sibling === element) {
                            const tagName = element.tagName ? element.tagName.toLowerCase() : '';
                            return getXPath(element.parentNode) + '/' + tagName + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                    return '';
                }
                
                function getCSSSelector(element) {
                    if (element.id) {
                        return '#' + element.id;
                    }
                    if (element.className) {
                        const classes = element.className.split(' ').filter(c => c.length > 0);
                        if (classes.length > 0) {
                            return element.tagName.toLowerCase() + '.' + classes.join('.');
                        }
                    }
                    return element.tagName.toLowerCase();
                }
                
                function getNearbyText(element) {
                    let text = '';
                    // Check siblings
                    if (element.parentNode) {
                        const siblings = Array.from(element.parentNode.children);
                        siblings.forEach(sibling => {
                            if (sibling !== element) {
                                const siblingText = sibling.textContent?.trim();
                                if (siblingText && siblingText.length < 50) {
                                    text += siblingText + ' ';
                                }
                            }
                        });
                    }
                    return text.trim().substring(0, 100);
                }
                
                return elements;
            }
            """
            
            elements_data = await self.page.evaluate(js_code)
            elements = []
            
            for elem_data in elements_data:
                # Generate hash for element
                element_hash = self._generate_element_hash(elem_data)
                elem_data['element_hash'] = element_hash
                elements.append(ElementInfo(**elem_data))
            
            logger.info(f"Extracted {len(elements)} elements from page")
            return elements
            
        except Exception as e:
            logger.error(f"Failed to extract elements: {e}")
            return []

    def _generate_element_hash(self, element_data: Dict) -> str:
        """Generate a unique hash for an element"""
        hash_components = [
            element_data.get('xpath', ''),
            element_data.get('tag_name', ''),
            str(element_data.get('attributes', {})),
            element_data.get('text', '')[:50]  # First 50 chars of text
        ]
        hash_string = '|'.join(hash_components)
        return hashlib.sha256(hash_string.encode()).hexdigest()[:16]

    async def click_by_coordinates(self, x: float, y: float) -> bool:
        """Click at specific coordinates"""
        try:
            await self.page.mouse.click(x, y)
            logger.info(f"Clicked at coordinates ({x}, {y})")
            await asyncio.sleep(1)  # Wait for any potential page changes
            return True
        except Exception as e:
            logger.error(f"Failed to click at coordinates ({x}, {y}): {e}")
            return False

    async def click_element_by_id(self, element_id: str, page_state: PageState) -> bool:
        """Click an element by its ID from the page state"""
        try:
            element = next((e for e in page_state.elements if e.id == element_id), None)
            if not element or not element.center_coordinates:
                logger.error(f"Element with ID {element_id} not found or has no coordinates")
                return False
            
            x = element.center_coordinates['x']
            y = element.center_coordinates['y']
            
            # Scroll element into view if needed
            await self._scroll_to_element(element)
            await asyncio.sleep(0.5)
            
            return await self.click_by_coordinates(x, y)
        except Exception as e:
            logger.error(f"Failed to click element {element_id}: {e}")
            return False

    async def type_text(self, text: str, element_id: str = None, coordinates: Tuple[float, float] = None) -> bool:
        """Type text into an input field"""
        try:
            if coordinates:
                # Click at coordinates first to focus
                await self.click_by_coordinates(coordinates[0], coordinates[1])
                await asyncio.sleep(0.5)
            elif element_id:
                # Find element and click it first
                page_state = await self.get_comprehensive_page_state(include_screenshot=False)
                element = next((e for e in page_state.elements if e.id == element_id), None)
                if element and element.center_coordinates:
                    await self.click_by_coordinates(
                        element.center_coordinates['x'], 
                        element.center_coordinates['y']
                    )
                    await asyncio.sleep(0.5)
            
            # Clear existing text and type new text
            await self.page.keyboard.press('Control+a')
            await self.page.keyboard.type(text)
            logger.info(f"Typed text: {text}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            return False

    async def _scroll_to_element(self, element: ElementInfo):
        """Scroll to make element visible"""
        if element.center_coordinates:
            await self.page.evaluate(f"""
                window.scrollTo({{
                    left: {element.center_coordinates['x'] - 640},
                    top: {element.center_coordinates['y'] - 400},
                    behavior: 'smooth'
                }});
            """)

    async def scroll_page(self, direction: str = "down", amount: int = 500):
        """Scroll the page"""
        if direction == "down":
            await self.page.mouse.wheel(0, amount)
        elif direction == "up":
            await self.page.mouse.wheel(0, -amount)
        await asyncio.sleep(1)

    async def press_key(self, key: str) -> bool:
        """Press a keyboard key"""
        try:
            await self.page.keyboard.press(key)
            logger.info(f"Pressed key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to press key {key}: {e}")
            return False

    async def wait_for_navigation(self, timeout: int = 10000) -> bool:
        """Wait for page navigation to complete"""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except:
            return False

    async def get_page_screenshot(self) -> str:
        """Get base64 encoded screenshot of current page"""
        try:
            screenshot_bytes = await self.page.screenshot(full_page=False)
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return ""

    def get_vnc_info(self):
        """Get VNC connection information"""
        if self.enable_vnc and self.vnc_port:
            return {
                "enabled": True,
                "port": self.vnc_port,
                "display": self.display_num,
                "url": f"ws://localhost:{self.vnc_port + 1000}"
            }
        return {"enabled": False}

# AI Integration Helper Class
class AIBrowserAgent:
    """Helper class to integrate with AI for decision making"""
    
    def __init__(self, browser_controller: BrowserController):
        self.browser = browser_controller
    
    async def execute_task(self, task_description: str) -> Dict[str, Any]:
        """Execute a task described in natural language"""
        try:
            # Get current page state
            page_state = await self.browser.get_comprehensive_page_state()
            
            # This is where you would integrate with your AI model
            # The AI would receive:
            # 1. task_description - what the user wants to do
            # 2. page_state - current state of the page with all elements
            # 3. screenshot - visual context
            
            return {
                "status": "ready_for_ai",
                "task": task_description,
                "page_state": page_state.to_dict(),
                "available_actions": [
                    "click_element_by_id",
                    "type_text", 
                    "scroll_page",
                    "press_key",
                    "goto"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to execute task: {e}")
            return {"status": "error", "error": str(e)}
    
    async def perform_ai_action(self, action: Dict[str, Any]) -> bool:
        """Perform an action decided by AI"""
        try:
            action_type = action.get("type")
            
            if action_type == "click":
                if "element_id" in action:
                    page_state = await self.browser.get_comprehensive_page_state(include_screenshot=False)
                    return await self.browser.click_element_by_id(action["element_id"], page_state)
                elif "coordinates" in action:
                    return await self.browser.click_by_coordinates(
                        action["coordinates"]["x"], 
                        action["coordinates"]["y"]
                    )
            
            elif action_type == "type":
                return await self.browser.type_text(
                    action["text"],
                    action.get("element_id"),
                    action.get("coordinates")
                )
            
            elif action_type == "scroll":
                await self.browser.scroll_page(
                    action.get("direction", "down"),
                    action.get("amount", 500)
                )
                return True
            
            elif action_type == "key":
                return await self.browser.press_key(action["key"])
            
            elif action_type == "navigate":
                await self.browser.goto(action["url"])
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to perform AI action: {e}")
            return False
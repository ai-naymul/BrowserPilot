import asyncio
import subprocess
import os
import logging
import json
import base64
from playwright.async_api import async_playwright, Page, CDPSession
from typing import Optional, Dict, List, Any, Tuple
import hashlib
from dataclasses import dataclass, asdict
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ElementInfo:
    """DOM element information compatible with browser-use"""
    index: int
    id: str
    tag_name: str
    xpath: str
    css_selector: str
    text: str
    attributes: Dict[str, str]
    is_clickable: bool
    is_input: bool
    is_visible: bool = True
    is_in_viewport: bool = True
    input_type: Optional[str] = None
    placeholder: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    center_coordinates: Optional[Dict[str, float]] = None
    viewport_coordinates: Optional[Dict[str, float]] = None

class PageState:
    """Page state compatible with browser-use"""
    def __init__(self, url: str, title: str, elements: List[ElementInfo], selector_map: Dict[int, ElementInfo], screenshot: Optional[str] = None):
        self.url = url
        self.title = title
        self.elements = elements
        self.selector_map = selector_map
        self.screenshot = screenshot
        self.clickable_elements = [e for e in elements if e.is_clickable]
        self.input_elements = [e for e in elements if e.is_input]

class BrowserController:
    def __init__(self, headless: bool, proxy: dict | None, enable_streaming: bool = False):
        self.headless = headless
        self.proxy = proxy
        self.enable_streaming = enable_streaming
        self.play = None
        self.browser = None
        self.page = None
        self.cdp_session = None
        self.streaming_active = False
        self.stream_clients = set()
        self._cached_page_state = None
        self._cached_url = None
        self._last_action_timestamp = None
        self.input_enabled = False  # Track if Input domain is available
        
        # Load the robust DOM extraction JavaScript
        self.dom_js = self._get_dom_extraction_js()

    async def __aenter__(self):
        """Initialize browser with CDP streaming support"""
        self.play = await async_playwright().start()
        
        launch_options = {
            "headless": self.headless,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--window-size=1280,800",
                "--window-position=0,0",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-first-run",
                "--disable-default-apps",
                # Enable remote debugging for CDP
                "--remote-debugging-port=0"  # Use random port
            ]
        }
        
        if self.proxy:
            launch_options["proxy"] = self.proxy
            
        self.browser = await self.play.chromium.launch(**launch_options)
        self.page = await self.browser.new_page(viewport={"width": 1280, "height": 800})
        
        # Set up CDP session for streaming
        if self.enable_streaming:
            await self._setup_cdp_streaming()
            
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Cleanup browser and CDP session"""
        if self.streaming_active:
            await self._stop_cdp_streaming()
        if self.browser:
            await self.browser.close()
        if self.play:
            await self.play.stop()

    async def _setup_cdp_streaming(self):
        """Setup CDP session for real-time streaming with proper error handling"""
        try:
            # Get CDP session - ensure it's for the page target
            self.cdp_session = await self.page.context.new_cdp_session(self.page)
            
            # Enable required domains with error handling
            await self._enable_cdp_domain('Runtime')
            await self._enable_cdp_domain('Page')
            
            # Try to enable Input domain (optional)
            self.input_enabled = await self._enable_cdp_domain('Input', optional=True)
            
            if self.input_enabled:
                logger.info("✅ Input domain enabled - full interaction support available")
            else:
                logger.warning("⚠️ Input domain not available - using Playwright for interactions")
            
            logger.info("✅ CDP session established for streaming")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup CDP streaming: {e}")
            raise

    async def _enable_cdp_domain(self, domain: str, optional: bool = False) -> bool:
        """Enable a CDP domain with proper error handling"""
        try:
            await self.cdp_session.send(f'{domain}.enable')
            logger.info(f"✅ {domain} domain enabled")
            return True
        except Exception as e:
            if optional:
                logger.warning(f"⚠️ {domain} domain not available: {e}")
                return False
            else:
                logger.error(f"❌ Required {domain} domain failed: {e}")
                raise

    async def start_streaming(self, quality: int = 80):
        """Start CDP screencast streaming with enhanced error handling"""
        if not self.cdp_session:
            raise RuntimeError("CDP session not initialized")
            
        try:
            # Check if Page.startScreencast is available
            await self.cdp_session.send('Page.startScreencast', {
                'format': 'jpeg',
                'quality': quality,
                'maxWidth': 1280,
                'maxHeight': 800,
                'everyNthFrame': 1  # Stream every frame for real-time
            })
            
            # Set up frame listener
            self.cdp_session.on('Page.screencastFrame', self._handle_screencast_frame)
            
            self.streaming_active = True
            logger.info("🎥 CDP streaming started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start CDP streaming: {e}")
            # Try alternative approach with screenshots
            await self._start_screenshot_polling()

    async def _start_screenshot_polling(self):
        """Fallback: Use screenshot polling if screencast not available"""
        logger.info("🔄 Starting screenshot polling as fallback")
        self.streaming_active = True
        
        async def screenshot_loop():
            while self.streaming_active:
                try:
                    screenshot_bytes = await self.page.screenshot(type='jpeg', quality=80)
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    frame_data = {
                        'type': 'frame',
                        'data': screenshot_b64,
                        'timestamp': asyncio.get_event_loop().time(),
                        'method': 'polling'
                    }
                    
                    await self._broadcast_to_clients(frame_data)
                    await asyncio.sleep(0.1)  # 10 FPS
                    
                except Exception as e:
                    logger.error(f"Screenshot polling error: {e}")
                    await asyncio.sleep(1)
        
        # Start screenshot polling in background
        asyncio.create_task(screenshot_loop())

    async def stop_streaming(self):
        """Stop CDP screencast streaming"""
        if self.cdp_session and self.streaming_active:
            try:
                await self.cdp_session.send('Page.stopScreencast')
                logger.info("🛑 CDP streaming stopped")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping screencast (may not have been active): {e}")
            finally:
                self.streaming_active = False

    async def _stop_cdp_streaming(self):
        """Internal cleanup for CDP streaming"""
        await self.stop_streaming()
        if self.cdp_session:
            try:
                await self.cdp_session.detach()
            except Exception as e:
                logger.warning(f"⚠️ Error detaching CDP session: {e}")

    async def _handle_screencast_frame(self, params):
        """Handle incoming screencast frames"""
        try:
            # Acknowledge frame immediately
            await self.cdp_session.send('Page.screencastFrameAck', {
                'sessionId': params['sessionId']
            })
            
            # Broadcast frame to all connected clients
            frame_data = {
                'type': 'frame',
                'data': params['data'],  # Base64 encoded JPEG
                'timestamp': params.get('timestamp'),
                'method': 'screencast',
                'metadata': {
                    'sessionId': params['sessionId']
                }
            }
            
            # Send to all connected streaming clients
            await self._broadcast_to_clients(frame_data)
            
        except Exception as e:
            logger.error(f"❌ Error handling screencast frame: {e}")

    async def _broadcast_to_clients(self, data):
        """Broadcast data to all connected streaming clients"""
        if not self.stream_clients:
            return
            
        disconnected_clients = []
        for client in self.stream_clients:
            try:
                await client.send_text(json.dumps(data))
            except Exception:
                disconnected_clients.append(client)
                
        # Remove disconnected clients
        for client in disconnected_clients:
            self.stream_clients.discard(client)

    def add_stream_client(self, websocket):
        """Add a new streaming client"""
        self.stream_clients.add(websocket)
        logger.info(f"🔗 Stream client connected. Total clients: {len(self.stream_clients)}")

    def remove_stream_client(self, websocket):
        """Remove a streaming client"""
        self.stream_clients.discard(websocket)
        logger.info(f"🔌 Stream client disconnected. Total clients: {len(self.stream_clients)}")

    async def handle_mouse_event(self, event_data):
        """Handle mouse events with fallback support"""
        try:
            if self.input_enabled and self.cdp_session:
                # Use CDP Input domain if available
                await self.cdp_session.send('Input.dispatchMouseEvent', {
                    'type': event_data['eventType'],
                    'x': event_data['x'],
                    'y': event_data['y'],
                    'button': event_data.get('button', 'left'),
                    'clickCount': event_data.get('clickCount', 1)
                })
            else:
                # Fallback to Playwright mouse actions
                if event_data['eventType'] == 'mousePressed':
                    await self.page.mouse.click(event_data['x'], event_data['y'])
                elif event_data['eventType'] == 'mouseMoved':
                    await self.page.mouse.move(event_data['x'], event_data['y'])
                    
        except Exception as e:
            logger.error(f"❌ Error handling mouse event: {e}")

    async def handle_keyboard_event(self, event_data):
        """Handle keyboard events with fallback support"""
        try:
            if self.input_enabled and self.cdp_session:
                # Use CDP Input domain if available
                await self.cdp_session.send('Input.dispatchKeyEvent', {
                    'type': event_data['eventType'],
                    'text': event_data.get('text', ''),
                    'key': event_data.get('key', ''),
                    'code': event_data.get('code', ''),
                    'keyCode': event_data.get('keyCode', 0)
                })
            else:
                # Fallback to Playwright keyboard actions
                if event_data['eventType'] == 'keyDown' and event_data.get('key'):
                    await self.page.keyboard.press(event_data['key'])
                elif event_data.get('text'):
                    await self.page.keyboard.type(event_data['text'])
                    
        except Exception as e:
            logger.error(f"❌ Error handling keyboard event: {e}")

    def get_streaming_info(self):
        """Get streaming connection information"""
        if self.enable_streaming:
            return {
                "enabled": True,
                "active": self.streaming_active,
                "clients": len(self.stream_clients),
                "websocket_url": "ws://localhost:8000/stream",
                "input_enabled": self.input_enabled,
                "method": "screencast" if self.input_enabled else "polling"
            }
        return {"enabled": False}

    # Keep all your existing methods from the original code
    def _get_dom_extraction_js(self) -> str:
        """Get the robust DOM extraction JavaScript similar to browser-use"""
        return """
        (args) => {
            const { doHighlightElements = true, debugMode = false } = args || {};
            
            // Performance tracking
            const startTime = performance.now();
            let nodeCount = 0;
            let processedCount = 0;
            
            // Results
            const elementMap = new Map();
            const selectorMap = {};
            let highlightIndex = 0;
            
            // Helper functions
            function getClassName(element) {
                if (!element.className) return '';
                if (typeof element.className === 'string') return element.className;
                if (element.className.toString) return element.className.toString();
                if (element.classList && element.classList.length > 0) {
                    return Array.from(element.classList).join(' ');
                }
                return '';
            }
            
            function isInteractive(element) {
                const tagName = element.tagName.toLowerCase();
                const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'label'];
                if (interactiveTags.includes(tagName)) return true;
                if (element.onclick || element.getAttribute('onclick')) return true;
                if (element.getAttribute('role') === 'button') return true;
                if (element.getAttribute('role') === 'link') return true;
                if (element.hasAttribute('tabindex')) return true;
                if (element.contentEditable === 'true') return true;
                const style = window.getComputedStyle(element);
                if (style.cursor === 'pointer') return true;
                return false;
            }
            
            function isInput(element) {
                const tagName = element.tagName.toLowerCase();
                return ['input', 'textarea', 'select'].includes(tagName) ||
                       element.contentEditable === 'true';
            }
            
            function getTextContent(element) {
                let text = '';
                if (element.textContent) {
                    text = element.textContent.trim();
                }
                if (element.value) {
                    text = element.value;
                } else if (element.placeholder) {
                    text = element.placeholder;
                }
                if (element.tagName === 'IMG' && element.alt) {
                    text = element.alt;
                }
                return text.substring(0, 200);
            }
            
            function isVisibleAndInViewport(element) {
                const rect = element.getBoundingClientRect();
                const style = window.getComputedStyle(element);
                const hasDimensions = rect.width > 0 && rect.height > 0;
                const isVisible = style.visibility !== 'hidden' &&
                                style.display !== 'none' &&
                                style.opacity !== '0';
                const isInViewport = rect.top < window.innerHeight &&
                                   rect.bottom > 0 &&
                                   rect.left < window.innerWidth &&
                                   rect.right > 0;
                return hasDimensions && isVisible && isInViewport;
            }
            
            // Process elements
            const allElements = document.querySelectorAll('*');
            const elements = [];
            
            allElements.forEach(element => {
                nodeCount++;
                if (!element || element.nodeType !== 1) return;
                
                const isElementVisible = isVisibleAndInViewport(element);
                const isElementInteractive = isInteractive(element);
                const isElementInput = isInput(element);
                
                if (!isElementVisible && !isElementInteractive) return;
                
                processedCount++;
                const rect = element.getBoundingClientRect();
                const elementId = `element_${processedCount}`;
                let currentHighlightIndex = null;
                
                if (isElementInteractive || isElementInput) {
                    currentHighlightIndex = highlightIndex++;
                    
                    if (doHighlightElements) {
                        element.style.outline = '2px solid red';
                        element.style.outlineOffset = '1px';
                        
                        const label = document.createElement('div');
                        label.textContent = currentHighlightIndex.toString();
                        label.style.cssText = `
                            position: absolute;
                            top: ${rect.top + window.scrollY - 20}px;
                            left: ${rect.left + window.scrollX}px;
                            background: red;
                            color: white;
                            padding: 2px 6px;
                            font-size: 12px;
                            font-weight: bold;
                            z-index: 10000;
                            border-radius: 3px;
                            pointer-events: none;
                        `;
                        document.body.appendChild(label);
                    }
                }
                
                const elementData = {
                    index: currentHighlightIndex,
                    id: elementId,
                    tagName: element.tagName.toLowerCase(),
                    xpath: '',
                    cssSelector: '',
                    text: getTextContent(element),
                    attributes: {},
                    isClickable: isElementInteractive,
                    isInput: isElementInput,
                    isVisible: isElementVisible,
                    isInViewport: isElementVisible,
                    inputType: element.type || null,
                    placeholder: element.placeholder || null,
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        bottom: rect.bottom,
                        left: rect.left,
                        right: rect.right
                    },
                    centerCoordinates: {
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2
                    }
                };
                
                if (element.attributes) {
                    for (let attr of element.attributes) {
                        elementData.attributes[attr.name] = attr.value;
                    }
                }
                
                elements.push(elementData);
                
                if (currentHighlightIndex !== null) {
                    selectorMap[currentHighlightIndex] = elementData;
                }
            });
            
            const endTime = performance.now();
            return {
                elements: elements,
                selectorMap: selectorMap,
                stats: {
                    totalNodes: nodeCount,
                    processedNodes: processedCount,
                    interactiveElements: Object.keys(selectorMap).length,
                    executionTime: endTime - startTime
                }
            };
        }
        """

    # Add all your existing methods here (goto, get_page_state, click_element_by_index, etc.)
    async def goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000):
        """Navigate to a URL with proper waiting"""
        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            await asyncio.sleep(2)
            logger.info(f"Successfully navigated to: {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise

    async def get_page_state(self, include_screenshot: bool = True, highlight_elements: bool = True) -> PageState:
        """Get current page state with elements"""
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            await asyncio.sleep(1)
            
            url = self.page.url
            title = await self.page.title()
            
            screenshot = None
            if include_screenshot:
                screenshot_bytes = await self.page.screenshot(
                    full_page=False,
                    clip={'x': 0, 'y': 0, 'width': 1250, 'height': 800}
                )
                screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Extract DOM elements
            try:
                dom_result = await self.page.evaluate(self.dom_js, {"doHighlightElements": highlight_elements})
                logger.info(f"Extracted {len(dom_result.get('elements', []))} interactive elements")
            except Exception as e:
                logger.error(f"DOM extraction failed: {e}")
                return PageState(url, title, [], {}, screenshot)
            
            elements = []
            selector_map = {}
            
            for elem_data in dom_result.get('elements', []):
                element_info = ElementInfo(
                    index=elem_data.get('index'),
                    id=elem_data.get('id', ''),
                    tag_name=elem_data.get('tagName', ''),
                    xpath=elem_data.get('xpath', ''),
                    css_selector=elem_data.get('cssSelector', ''),
                    text=elem_data.get('text', ''),
                    attributes=elem_data.get('attributes', {}),
                    is_clickable=elem_data.get('isClickable', False),
                    is_input=elem_data.get('isInput', False),
                    center_coordinates=elem_data.get('centerCoordinates')
                )
                
                elements.append(element_info)
                if element_info.index is not None:
                    selector_map[element_info.index] = element_info
            
            return PageState(url, title, elements, selector_map, screenshot)
            
        except Exception as e:
            logger.error(f"Failed to get page state: {e}")
            return PageState("", "", [], {}, None)

    async def click_element_by_index(self, index: int, page_state: PageState = None) -> bool:
        """Click element by index"""
        try:
            if page_state is None:
                page_state = await self.get_page_state(include_screenshot=False, highlight_elements=False)
            
            if index not in page_state.selector_map:
                logger.error(f"Element with index {index} not found")
                return False
            
            element = page_state.selector_map[index]
            if not element.center_coordinates:
                logger.error(f"Element at index {index} has no coordinates")
                return False
            
            x = element.center_coordinates['x']
            y = element.center_coordinates['y']
            
            logger.info(f"Clicking element {index}: {element.text[:50]}... at ({x}, {y})")
            
            await self.page.mouse.click(x, y)
            await asyncio.sleep(1)
            
            logger.info(f"Successfully clicked element {index}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click element at index {index}: {e}")
            return False

    async def input_text_by_index(self, index: int, text: str, page_state: PageState = None) -> bool:
        """Input text into element by index"""
        try:
            if page_state is None:
                page_state = await self.get_page_state(include_screenshot=False, highlight_elements=False)
            
            if index not in page_state.selector_map:
                logger.error(f"Element with index {index} not found")
                return False
            
            element = page_state.selector_map[index]
            if not element.center_coordinates:
                logger.error(f"Element at index {index} has no coordinates")
                return False
            
            x = element.center_coordinates['x']
            y = element.center_coordinates['y']
            
            logger.info(f"Typing '{text}' into element {index}")
            
            await self.page.mouse.click(x, y)
            await asyncio.sleep(0.5)
            await self.page.keyboard.press('Control+a')
            await self.page.keyboard.type(text)
            
            logger.info(f"Successfully typed text into element {index}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to input text into element at index {index}: {e}")
            return False

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

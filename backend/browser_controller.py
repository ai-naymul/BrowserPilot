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
    """DOM element information compatible with browser-use"""
    index: int  # Highlight index for clicking
    id: str # Unique identifier
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
        self.selector_map = selector_map  # index -> ElementInfo mapping
        self.screenshot = screenshot
        self.clickable_elements = [e for e in elements if e.is_clickable]
        self.input_elements = [e for e in elements if e.is_input]

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
        
        # Load the robust DOM extraction JavaScript
        self.dom_js = self._get_dom_extraction_js()

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
            
            // Helper function to safely get className
            function getClassName(element) {
                if (!element.className) return '';
                if (typeof element.className === 'string') return element.className;
                if (element.className.toString) return element.className.toString();
                if (element.classList && element.classList.length > 0) {
                    return Array.from(element.classList).join(' ');
                }
                return '';
            }
            
            // Helper function to generate CSS selector
            function getCSSSelector(element) {
                if (element.id) {
                    return '#' + element.id;
                }
                
                const className = getClassName(element);
                if (className) {
                    const classes = className.split(' ').filter(c => c.length > 0);
                    if (classes.length > 0) {
                        return element.tagName.toLowerCase() + '.' + classes.join('.');
                    }
                }
                
                return element.tagName.toLowerCase();
            }
            
            // Helper function to generate XPath
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
            
            // Check if element is interactive
            function isInteractive(element) {
                const tagName = element.tagName.toLowerCase();
                const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'label'];
                
                // Check tag name
                if (interactiveTags.includes(tagName)) return true;
                
                // Check attributes
                if (element.onclick || element.getAttribute('onclick')) return true;
                if (element.getAttribute('role') === 'button') return true;
                if (element.getAttribute('role') === 'link') return true;
                if (element.hasAttribute('tabindex')) return true;
                if (element.contentEditable === 'true') return true;
                
                // Check computed style
                const style = window.getComputedStyle(element);
                if (style.cursor === 'pointer') return true;
                
                // Check class names for common interactive patterns
                const className = getClassName(element);
                const interactivePatterns = ['btn', 'button', 'link', 'clickable'];
                if (interactivePatterns.some(pattern => className.includes(pattern))) return true;
                
                return false;
            }
            
            // Check if element is input
            function isInput(element) {
                const tagName = element.tagName.toLowerCase();
                return ['input', 'textarea', 'select'].includes(tagName) || 
                       element.contentEditable === 'true';
            }
            
            // Get text content safely
            function getTextContent(element) {
                let text = '';
                
                // Get direct text content
                if (element.textContent) {
                    text = element.textContent.trim();
                }
                
                // For inputs, get value or placeholder
                if (element.value) {
                    text = element.value;
                } else if (element.placeholder) {
                    text = element.placeholder;
                }
                
                // For images, get alt text
                if (element.tagName === 'IMG' && element.alt) {
                    text = element.alt;
                }
                
                return text.substring(0, 200); // Limit text length
            }
            
            // Check if element is visible and in viewport
            function isVisibleAndInViewport(element) {
                const rect = element.getBoundingClientRect();
                const style = window.getComputedStyle(element);
                
                // Check if element has dimensions
                const hasDimensions = rect.width > 0 && rect.height > 0;
                
                // Check if element is visible
                const isVisible = style.visibility !== 'hidden' && 
                                style.display !== 'none' && 
                                style.opacity !== '0';
                
                // Check if element is in viewport
                const isInViewport = rect.top < window.innerHeight && 
                                   rect.bottom > 0 && 
                                   rect.left < window.innerWidth && 
                                   rect.right > 0;
                
                return hasDimensions && isVisible && isInViewport;
            }
            
            // Process all elements
            function processElement(element) {
                nodeCount++;
                
                if (!element || element.nodeType !== 1) return null;
                
                const isElementVisible = isVisibleAndInViewport(element);
                const isElementInteractive = isInteractive(element);
                const isElementInput = isInput(element);
                
                // Only process visible elements or interactive elements
                if (!isElementVisible && !isElementInteractive) return null;
                
                processedCount++;
                
                const rect = element.getBoundingClientRect();
                const elementId = `element_${processedCount}`;
                let currentHighlightIndex = null;
                
                // Assign highlight index to interactive elements
                if (isElementInteractive || isElementInput) {
                    currentHighlightIndex = highlightIndex++;
                    
                    // Add visual highlight if enabled
                    if (doHighlightElements) {
                        element.style.outline = '2px solid red';
                        element.style.outlineOffset = '1px';
                        
                        // Add index label
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
                
                // Create element data
                const elementData = {
                    index: currentHighlightIndex,
                    id: elementId,
                    tagName: element.tagName.toLowerCase(),
                    xpath: getXPath(element),
                    cssSelector: getCSSSelector(element),
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
                    },
                    viewportCoordinates: {
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2
                    }
                };
                
                // Get attributes
                if (element.attributes) {
                    for (let attr of element.attributes) {
                        elementData.attributes[attr.name] = attr.value;
                    }
                }
                
                elementMap.set(elementId, elementData);
                
                // Add to selector map if has highlight index
                if (currentHighlightIndex !== null) {
                    selectorMap[currentHighlightIndex] = elementData;
                }
                
                return elementData;
            }
            
            // Process all elements in the document
            const allElements = document.querySelectorAll('*');
            const elements = [];
            
            allElements.forEach(element => {
                const elementData = processElement(element);
                if (elementData) {
                    elements.push(elementData);
                }
            });
            
            const endTime = performance.now();
            
            const result = {
                elements: elements,
                selectorMap: selectorMap,
                stats: {
                    totalNodes: nodeCount,
                    processedNodes: processedCount,
                    interactiveElements: Object.keys(selectorMap).length,
                    executionTime: endTime - startTime
                }
            };
            
            if (debugMode) {
                console.log('DOM extraction completed:', result.stats);
            }
            
            return result;
        }
        """

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

    async def get_page_state(self, include_screenshot: bool = True, highlight_elements: bool = True) -> PageState:
        """Get comprehensive page state using robust DOM extraction"""
        try:
            # Wait for page to be ready
            await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            await asyncio.sleep(1)  # Additional wait for dynamic content

            # Get page info
            url = self.page.url
            title = await self.page.title()

            # Get screenshot if requested
            screenshot = None
            if include_screenshot:
                screenshot_bytes = await self.page.screenshot(full_page=False)
                screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')

            # Extract DOM elements using robust JavaScript
            try:
                dom_result = await self.page.evaluate(self.dom_js, {
                    'doHighlightElements': highlight_elements,
                    'debugMode': logger.isEnabledFor(logging.DEBUG)
                })
                
                logger.info(f"DOM extraction stats: {dom_result.get('stats', {})}")
                
            except Exception as e:
                logger.error(f"Failed to extract DOM elements: {e}")
                return PageState(url, title, [], {}, screenshot)

            # Convert to ElementInfo objects
            elements = []
            selector_map = {}
            
            for elem_data in dom_result.get('elements', []):
                try:
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
                        is_visible=elem_data.get('isVisible', True),
                        is_in_viewport=elem_data.get('isInViewport', True),
                        input_type=elem_data.get('inputType'),
                        placeholder=elem_data.get('placeholder'),
                        bounding_box=elem_data.get('boundingBox'),
                        center_coordinates=elem_data.get('centerCoordinates'),
                        viewport_coordinates=elem_data.get('viewportCoordinates')
                    )
                    
                    elements.append(element_info)
                    
                    # Add to selector map if has index
                    if element_info.index is not None:
                        selector_map[element_info.index] = element_info
                        
                except Exception as e:
                    logger.warning(f"Failed to process element: {e}")
                    continue

            logger.info(f"Successfully extracted {len(elements)} elements, {len(selector_map)} interactive")
            return PageState(url, title, elements, selector_map, screenshot)

        except Exception as e:
            logger.error(f"Failed to get page state: {e}")
            return PageState("", "", [], {}, None)

    async def click_element_by_index(self, index: int, page_state: PageState = None) -> bool:
        """Click element by index (browser-use compatible)"""
        try:
            if page_state is None:
                page_state = await self.get_page_state(include_screenshot=False, highlight_elements=False)
            
            if index not in page_state.selector_map:
                logger.error(f"Element with index {index} not found in selector map")
                return False

            element = page_state.selector_map[index]
            
            if not element.center_coordinates:
                logger.error(f"Element at index {index} has no coordinates")
                return False

            x = element.center_coordinates['x']
            y = element.center_coordinates['y']

            logger.info(f"Clicking element {index}: {element.text[:50]}... at ({x}, {y})")
            
            # Click using coordinates
            await self.page.mouse.click(x, y)
            await asyncio.sleep(1)
            
            logger.info(f"Successfully clicked element {index}")
            return True

        except Exception as e:
            logger.error(f"Failed to click element at index {index}: {e}")
            return False

    async def input_text_by_index(self, index: int, text: str, page_state: PageState = None) -> bool:
        """Input text into element by index (browser-use compatible)"""
        try:
            if page_state is None:
                page_state = await self.get_page_state(include_screenshot=False, highlight_elements=False)
            
            if index not in page_state.selector_map:
                logger.error(f"Element with index {index} not found in selector map")
                return False

            element = page_state.selector_map[index]
            
            if not element.is_input:
                logger.warning(f"Element at index {index} may not be an input field")

            if not element.center_coordinates:
                logger.error(f"Element at index {index} has no coordinates")
                return False

            x = element.center_coordinates['x']
            y = element.center_coordinates['y']

            logger.info(f"Typing '{text}' into element {index}: {element.text[:30]}...")
            
            # Click to focus, then type
            await self.page.mouse.click(x, y)
            await asyncio.sleep(0.5)
            
            # Clear existing text and type new text
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

    def get_vnc_info(self):
        """Get VNC connection information"""
        if self.enable_vnc and self.vnc_port:
            return {
                "enabled": True,
                "port": self.vnc_port,
                "display": self.display_num,
                "url": f"ws://localhost:{self.vnc_port + 1000}",
                "websocket_port": self.vnc_port + 1000,
                "websocket_url": f"ws://localhost:{self.vnc_port + 1000}"
            }
        return {"enabled": False}

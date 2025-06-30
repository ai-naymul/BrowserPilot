import asyncio, json, base64, re
from pathlib import Path
from typing import Literal
from backend.browser_controller import BrowserController
from backend.vision_model import decide
from backend.universal_extractor import UniversalExtractor

def detect_format_from_prompt(prompt: str, default_fmt: str) -> str:
    """Detect format from prompt text and override default if found"""
    prompt_lower = prompt.lower()
    
    # Format detection patterns
    format_patterns = {
        'pdf': [r'\bpdf\b', r'pdf format', r'save.*pdf', r'as pdf', r'to pdf'],
        'csv': [r'\bcsv\b', r'csv format', r'save.*csv', r'as csv', r'to csv'],
        'json': [r'\bjson\b', r'json format', r'save.*json', r'as json', r'to json'],
        'html': [r'\bhtml\b', r'html format', r'save.*html', r'as html', r'to html'],
        'md': [r'\bmarkdown\b', r'md format', r'save.*markdown', r'as markdown', r'to md'],
        'txt': [r'\btext\b', r'txt format', r'save.*text', r'as text', r'to txt', r'plain text']
    }
    
    # Check each format pattern
    for fmt, patterns in format_patterns.items():
        for pattern in patterns:
            if re.search(pattern, prompt_lower):
                print(f"🎯 Detected format '{fmt}' from prompt")
                return fmt
    
    print(f"📋 No specific format detected, using default: {default_fmt}")
    return default_fmt

def get_file_extension(fmt: str) -> str:
    """Get appropriate file extension for format"""
    extensions = {
        'txt': 'txt',
        'md': 'md', 
        'json': 'json',
        'html': 'html',
        'csv': 'csv',
        'pdf': 'pdf'
    }
    return extensions.get(fmt, 'output')  # fallback to .output

def get_content_type(fmt: str) -> str:
    """Get MIME type for format"""
    content_types = {
        'txt': 'text/plain',
        'md': 'text/markdown',
        'json': 'application/json',
        'html': 'text/html',
        'csv': 'text/csv',
        'pdf': 'application/pdf'
    }
    return content_types.get(fmt, 'application/octet-stream')

async def run_agent(job_id: str, prompt: str, fmt: Literal["txt","md","json","html","csv","pdf"],
                   headless: bool, proxy: dict | None, enable_streaming: bool = False):
    """Universal agent with complete file format support"""
    from backend.main import broadcast, OUTPUT_DIR, register_streaming_session, store_job_info
    
    print(f"🚀 Starting universal agent for job {job_id}")
    print(f"📋 Goal: {prompt}")
    print(f"🌐 Default Format: {fmt}")
    
    # Smart format detection from prompt
    detected_fmt = detect_format_from_prompt(prompt, fmt)
    if detected_fmt != fmt:
        print(f"🔄 Format overridden: {fmt} → {detected_fmt}")
        fmt = detected_fmt
    
    # Store job info for later download
    await store_job_info(job_id, {
        "format": fmt,
        "content_type": get_content_type(fmt),
        "extension": get_file_extension(fmt),
        "prompt": prompt
    })
    
    # Initialize universal extractor
    extractor = UniversalExtractor()
    
    async with BrowserController(headless, proxy, enable_streaming) as browser:
        # Register streaming session
        if enable_streaming:
            await register_streaming_session(job_id, browser)
        
        # Smart navigation
        url_match = re.search(r"https?://[\w\-\.]+[^\s]*", prompt)
        if url_match:
            start_url = url_match.group(0).rstrip('".,;')
            print(f"🔗 Found URL in prompt: {start_url}")
            await browser.goto(start_url)
        else:
            start_url = determine_starting_url(prompt)
            print(f"🔗 Starting at: {start_url}")
            await browser.goto(start_url)
        
        await broadcast(job_id, {
            "status": "started", 
            "initial_url": browser.page.url,
            "detected_format": fmt,
            "file_extension": get_file_extension(fmt)
        })
        
        # Dynamic limits
        max_steps = determine_max_steps(prompt)
        consecutive_scrolls = 0
        max_consecutive_scrolls = 3
        extraction_attempts = 0
        max_extraction_attempts = 2
        
        print(f"🎯 Running for max {max_steps} steps, output format: {fmt}")
        
        # Main universal loop
        for step in range(max_steps):
            print(f"\n🔄 Step {step + 1}/{max_steps}")
            
            try:
                page_state = await browser.get_page_state(include_screenshot=True)
                print(f"📊 Found {len(page_state.selector_map)} interactive elements")
                print(f"📍 Current: {page_state.url}")
                
                await broadcast(job_id, {
                    "type": "page_info",
                    "step": step + 1,
                    "url": page_state.url,
                    "title": page_state.title,
                    "interactive_elements": len(page_state.selector_map),
                    "format": fmt
                })
                
                if page_state.screenshot:
                    await broadcast(job_id, {
                        "type": "screenshot",
                        "screenshot": page_state.screenshot
                    })
                
            except Exception as e:
                print(f"❌ Page state failed: {e}")
                continue
            
            # Handle empty pages
            if len(page_state.selector_map) == 0:
                if consecutive_scrolls < max_consecutive_scrolls:
                    print("⚠️ No interactive elements, trying to scroll...")
                    await browser.scroll_page("down", 400)
                    consecutive_scrolls += 1
                    continue
                else:
                    print("⚠️ No elements found after scrolling")
                    break
            
            # AI decision making
            try:
                screenshot_bytes = base64.b64decode(page_state.screenshot)
                decision = await decide(screenshot_bytes, page_state, prompt)
                
                print(f"🤖 AI Decision: {decision.get('action')} - {decision.get('reason', 'No reason')}")
                
                await broadcast(job_id, {
                    "type": "decision", 
                    "step": step + 1,
                    "decision": decision
                })
                
            except Exception as e:
                print(f"❌ AI decision failed: {e}")
                continue
            
            # Execute action
            action = decision.get("action")
            print(f"⚡ Executing: {action}")
            
            try:
                if action == "click":
                    index = decision.get("index")
                    if index is not None and index in page_state.selector_map:
                        elem = page_state.selector_map[index]
                        print(f"🖱️ Clicking: {elem.text[:50]}...")
                        await browser.click_element_by_index(index, page_state)
                        consecutive_scrolls = 0
                        extraction_attempts = 0
                        await asyncio.sleep(2)
                    else:
                        print(f"❌ Invalid click index: {index}")
                        
                elif action == "type":
                    index = decision.get("index")
                    text = decision.get("text", "")
                    if index is not None and index in page_state.selector_map and text:
                        elem = page_state.selector_map[index]
                        print(f"⌨️ Typing '{text}' into: {elem.text[:30]}...")
                        await browser.input_text_by_index(index, text, page_state)
                        consecutive_scrolls = 0
                        await asyncio.sleep(1)
                    else:
                        print(f"❌ Invalid type parameters: index={index}, text='{text}'")
                        
                elif action == "scroll":
                    direction = decision.get("direction", "down")
                    amount = decision.get("amount", 400)
                    print(f"📜 Scrolling {direction} by {amount}px")
                    await browser.scroll_page(direction, amount)
                    consecutive_scrolls += 1
                    
                    if consecutive_scrolls >= max_consecutive_scrolls:
                        print("⚠️ Too many scrolls, trying page end")
                        await browser.press_key("End")
                        consecutive_scrolls = 0
                        
                elif action == "press_key":
                    key = decision.get("key", "Enter")
                    print(f"🔑 Pressing key: {key}")
                    await browser.press_key(key)
                    consecutive_scrolls = 0
                    await asyncio.sleep(2)
                    
                elif action == "navigate":
                    url = decision.get("url", "")
                    if url and url.startswith("http"):
                        print(f"🔗 Navigating to: {url}")
                        await browser.goto(url)
                        consecutive_scrolls = 0
                        extraction_attempts = 0
                        await asyncio.sleep(2)
                    else:
                        print(f"❌ Invalid navigation URL: {url}")
                        
                elif action == "extract":
                    extraction_attempts += 1
                    if extraction_attempts <= max_extraction_attempts:
                        print(f"🔍 Starting intelligent extraction in {fmt} format...")
                        await broadcast(job_id, {
                            "type": "extraction", 
                            "status": "starting",
                            "attempt": extraction_attempts,
                            "format": fmt
                        })
                        
                        # Use universal extraction with specified format
                        content_result = await extractor.extract_intelligent_content(browser, prompt, fmt, job_id)
                        
                        # Save content with proper extension
                        file_extension = get_file_extension(fmt)
                        output_file = OUTPUT_DIR / f"{job_id}.{file_extension}"
                        
                        # Handle different content types
                        saved_successfully = await save_content(content_result, output_file, fmt, job_id)
                        
                        if saved_successfully:
                            print(f"💾 Content saved successfully: {output_file}")
                            await broadcast(job_id, {
                                "type": "extraction", 
                                "status": "completed",
                                "format": fmt,
                                "file_path": str(output_file),
                                "file_extension": file_extension
                            })
                        else:
                            print(f"❌ Failed to save content")
                            
                        break
                    else:
                        print("⚠️ Maximum extraction attempts reached")
                        break
                    
                elif action == "done":
                    print("✅ Task marked as complete by AI")
                    break
                    
                else:
                    print(f"⚠️ Unknown action: {action}")
                    
            except Exception as e:
                print(f"❌ Action execution failed: {e}")
                await asyncio.sleep(1)
            
            await asyncio.sleep(0.5)
        
        # Final extraction if not done yet
        if extraction_attempts == 0:
            print(f"🔍 Performing final extraction in {fmt} format...")
            try:
                content_result = await extractor.extract_intelligent_content(browser, prompt, fmt, job_id)
                
                file_extension = get_file_extension(fmt)
                output_file = OUTPUT_DIR / f"{job_id}.{file_extension}"
                
                await save_content(content_result, output_file, fmt, job_id)
                print(f"💾 Final content saved: {output_file}")
            except Exception as e:
                print(f"❌ Final extraction failed: {e}")
        
        await broadcast(job_id, {"status": "finished", "final_format": fmt})

async def save_content(content_result: str, output_file: Path, fmt: str, job_id: str) -> bool:
    """Save content based on format type"""
    try:
        if fmt == "pdf":
            # Handle PDF - check for direct save indicator
            if content_result.startswith("PDF_DIRECT_SAVE:"):
                # PDF was saved directly to the correct location
                pdf_path = content_result.split("PDF_DIRECT_SAVE:")[1].strip()
                print(f"📄 PDF saved directly: {pdf_path}")
                
                # Verify the file exists at expected location
                if Path(pdf_path).exists():
                    return True
                else:
                    print(f"❌ PDF file not found at expected location: {pdf_path}")
                    return False
                    
            elif content_result.startswith("PDF saved to:"):
                # Legacy format - PDF was saved elsewhere, need to copy
                pdf_path = content_result.split("PDF saved to: ")[1].strip()
                import shutil
                shutil.copy2(pdf_path, output_file)
                print(f"📄 PDF copied to standard location: {output_file}")
                return True
            else:
                # Content is text, save as fallback
                with open(output_file.with_suffix('.txt'), "w", encoding="utf-8") as f:
                    f.write("PDF GENERATION FAILED - TEXT FALLBACK\n")
                    f.write("="*50 + "\n\n")
                    f.write(content_result)
                print(f"📄 PDF fallback saved as text: {output_file.with_suffix('.txt')}")
                return True
        else:
            # Handle text-based formats
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content_result)
            print(f"📝 {fmt.upper()} content saved: {output_file}")
            return True
            
    except Exception as e:
        print(f"❌ Error saving content: {e}")
        return False

def determine_starting_url(prompt: str) -> str:
    """Determine the best starting URL based on the user's goal"""
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ["search", "find", "look for", "google"]):
        return "https://www.google.com"
    if "linkedin" in prompt_lower:
        return "https://www.linkedin.com"
    if "github" in prompt_lower:
        return "https://www.github.com"
    if any(word in prompt_lower for word in ["buy", "purchase", "product", "amazon"]):
        return "https://www.amazon.com"
    if any(word in prompt_lower for word in ["news", "article"]):
        return "https://news.google.com"
    
    return "https://www.google.com"

def determine_max_steps(prompt: str) -> int:
    """Determine max steps based on task complexity"""
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ["extract", "get info", "save"]):
        return 15
    if any(word in prompt_lower for word in ["research", "analyze", "compare"]):
        return 25
    if any(word in prompt_lower for word in ["fill", "submit", "register"]):
        return 20
    
    return 20

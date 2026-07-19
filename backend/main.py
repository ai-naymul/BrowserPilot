import asyncio, json, os, uuid, shutil, base64, time, functools
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from backend.smart_browser_controller import SmartBrowserController  # Updated import
from backend.proxy_manager import SmartProxyManager  # Updated import
from backend.agent import run_agent
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.config import WS_BASE_URL, STREAM_SESSION_TIMEOUT_S, EXTRACTION_MAX_CHARS
from backend.bulk_engine import BulkEngine, BulkJobConfig, extract_dom
from backend.browser_controller import BrowserController
from backend.universal_extractor import MODEL

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO add specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks = {} # job_id → async.Task
ws_subscribers = {} # job_id → { websocket, … }
streaming_sessions = {} # job_id → browser_controller
job_info = {} # job_id → { format, content_type, extension, prompt }

# Initialize global smart proxy manager
smart_proxy_manager = SmartProxyManager()

# Initialize bulk engine
bulk_engine = BulkEngine(proxy_manager=smart_proxy_manager)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

class JobRequest(BaseModel):
    prompt: str
    format: str = "txt" # txt | md | json | html | csv | pdf
    headless: bool = False
    enable_streaming: bool = False

async def store_job_info(job_id: str, info: dict):
    """Store job information for later retrieval"""
    job_info[job_id] = info
    print(f"📊 Stored job info for {job_id}: {info}")

@app.post("/job")
async def create_job(req: JobRequest):
    # Validate format
    valid_formats = ["txt", "md", "json", "html", "csv", "pdf"]
    if req.format not in valid_formats:
        print(f"⚠️ Invalid format '{req.format}', defaulting to 'txt'")
        req.format = "txt"
    
    job_id = str(uuid.uuid4())
    
    # Use smart proxy manager to get the best available proxy
    proxy_info = smart_proxy_manager.get_best_proxy()
    proxy = proxy_info.to_playwright_dict() if proxy_info else None
    
    print(f"🚀 Creating smart job {job_id}")
    print(f"📋 Goal: {req.prompt}")
    print(f"🌐 Format: {req.format}")
    print(f"🖥️ Headless: {req.headless}")
    print(f"📡 Streaming: {req.enable_streaming}")
    print(f"🔄 Selected proxy: {proxy.get('server', 'None') if proxy else 'None'}")
    
    # Get initial proxy stats
    proxy_stats = smart_proxy_manager.get_proxy_stats()
    print(f"📊 Proxy pool stats: {proxy_stats}")
    
    # Create the agent task
    coro = run_agent(job_id, req.prompt, req.format, req.headless, proxy, req.enable_streaming)
    tasks[job_id] = asyncio.create_task(coro)
    
    response = {
        "job_id": job_id, 
        "format": req.format,
        "proxy_stats": proxy_stats
    }
    
    if req.enable_streaming:
        response["streaming_enabled"] = True
        response["stream_url"] = f"{WS_BASE_URL}/stream/{job_id}"
    
    return response

@app.websocket("/ws/{job_id}")
async def job_ws(ws: WebSocket, job_id: str):
    await ws.accept()
    ws_subscribers.setdefault(job_id, set()).add(ws)
    
    # Send streaming info if available
    if job_id in streaming_sessions:
        browser_ctrl = streaming_sessions[job_id]
        stream_info = browser_ctrl.get_streaming_info()
        await ws.send_text(json.dumps({
            "type": "streaming_info",
            "streaming": stream_info
        }))
    
    # Send initial proxy stats
    proxy_stats = smart_proxy_manager.get_proxy_stats()
    await ws.send_text(json.dumps({
        "type": "proxy_stats",
        "stats": proxy_stats
    }))
    
    try:
        while True:
            await ws.receive_text() # keep connection alive
    except WebSocketDisconnect:
        ws_subscribers[job_id].discard(ws)

@app.websocket("/stream/{job_id}")
async def stream_ws(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time browser streaming"""
    await websocket.accept()
    
    # Wait for streaming session to be available (with timeout)
    max_wait = STREAM_SESSION_TIMEOUT_S
    wait_time = 0
    while job_id not in streaming_sessions and wait_time < max_wait:
        await asyncio.sleep(0.5)
        wait_time += 0.5
    
    if job_id not in streaming_sessions:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Streaming session not available - job may not have streaming enabled"
        }))
        await websocket.close()
        return
    
    browser_ctrl = streaming_sessions[job_id]
    browser_ctrl.add_stream_client(websocket)
    
    # Send initial connection confirmation
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": "Connected to browser stream",
        "streaming_active": browser_ctrl.streaming_active
    }))
    
    try:
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data['type'] == 'mouse':
                    await browser_ctrl.handle_mouse_event(data)
                elif data['type'] == 'keyboard':
                    await browser_ctrl.handle_keyboard_event(data)
                elif data['type'] == 'ping':
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        browser_ctrl.remove_stream_client(websocket)
        print(f"Stream client disconnected from job {job_id}")
    except Exception as e:
        print(f"Error in stream WebSocket: {e}")
        browser_ctrl.remove_stream_client(websocket)

@app.post("/streaming/create/{job_id}")
async def create_streaming_session(job_id: str):
    """Create a streaming session without starting a job"""
    if job_id in streaming_sessions:
        browser_ctrl = streaming_sessions[job_id]
        return browser_ctrl.get_streaming_info()
    
    try:
        # Get best available proxy for streaming session
        proxy_info = smart_proxy_manager.get_best_proxy()
        proxy = proxy_info.to_playwright_dict() if proxy_info else None
        
        print(f"🎥 Creating streaming session with proxy: {proxy.get('server', 'None') if proxy else 'None'}")
        
        # Create smart browser controller with streaming enabled
        browser_ctrl = SmartBrowserController(headless=False, proxy=proxy, enable_streaming=True)
        await browser_ctrl.__aenter__()
        await browser_ctrl.start_streaming(quality=80)
        streaming_sessions[job_id] = browser_ctrl
        
        stream_info = browser_ctrl.get_streaming_info()
        
        # Add proxy information to stream info
        stream_info["proxy_info"] = {
            "current_proxy": proxy.get("server", "None") if proxy else "None",
            "proxy_stats": smart_proxy_manager.get_proxy_stats()
        }
        
        # Broadcast to connected clients
        await broadcast(job_id, {
            "type": "streaming_info",
            "streaming": stream_info
        })
        
        return stream_info
        
    except Exception as e:
        print(f"❌ Failed to create streaming session: {e}")
        return {"enabled": False, "error": str(e)}

@app.get("/streaming/{job_id}")
async def get_streaming_info(job_id: str):
    """Get streaming connection information for a job"""
    if job_id in streaming_sessions:
        browser_ctrl = streaming_sessions[job_id]
        stream_info = browser_ctrl.get_streaming_info()
        
        # Add current proxy stats
        stream_info["proxy_stats"] = smart_proxy_manager.get_proxy_stats()
        
        return stream_info
    
    return {"enabled": False, "error": "Streaming not enabled for this job"}

@app.delete("/streaming/{job_id}")
async def cleanup_streaming(job_id: str):
    """Clean up streaming session for a job"""
    if job_id in streaming_sessions:
        browser_ctrl = streaming_sessions[job_id]
        try:
            await browser_ctrl.__aexit__(None, None, None)
        except Exception as e:
            print(f"Error cleaning up streaming session: {e}")
        finally:
            del streaming_sessions[job_id]
        return {"message": "Streaming session cleaned up"}
    return {"message": "No streaming session found"}

@app.get("/download/{job_id}")
def download(job_id: str):
    """Enhanced download endpoint that handles all file formats"""
    print(f"📥 Download request for job {job_id}")
    
    # Get job information
    if job_id in job_info:
        info = job_info[job_id]
        extension = info.get("extension", "output")
        content_type = info.get("content_type", "application/octet-stream")
        format_name = info.get("format", "unknown")
        
        print(f"📋 Job info found: {info}")
    else:
        # Fallback for jobs without stored info
        extension = "output"
        content_type = "application/octet-stream"
        format_name = "unknown"
        print(f"⚠️ No job info found for {job_id}, using fallback")
    
    # Try to find the file with proper extension first
    file_path = OUTPUT_DIR / f"{job_id}.{extension}"
    
    if not file_path.exists():
        # Fallback: try common extensions
        for fallback_ext in ['txt', 'pdf', 'csv', 'json', 'html', 'md', 'output']:
            fallback_path = OUTPUT_DIR / f"{job_id}.{fallback_ext}"
            if fallback_path.exists():
                file_path = fallback_path
                extension = fallback_ext
                print(f"📁 Found file with fallback extension: {file_path}")
                break
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    
    # Generate appropriate filename
    safe_filename = f"extracted_data_{job_id}.{extension}"
    
    print(f"✅ Serving file: {file_path}")
    print(f"📄 Content-Type: {content_type}")
    print(f"📎 Filename: {safe_filename}")
    
    # Serve file with proper content type and filename
    return FileResponse(
        path=file_path, 
        filename=safe_filename,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={safe_filename}",
            "X-File-Format": format_name,
            "X-Original-Extension": extension
        }
    )

@app.get("/job/{job_id}/info")
def get_job_info(job_id: str):
    """Get job information including format and status"""
    if job_id in job_info:
        info = job_info[job_id].copy()
        
        # Add file existence check
        extension = info.get("extension", "output")
        file_path = OUTPUT_DIR / f"{job_id}.{extension}"
        info["file_exists"] = file_path.exists()
        info["file_path"] = str(file_path) if file_path.exists() else None
        
        # Add current proxy stats
        info["proxy_stats"] = smart_proxy_manager.get_proxy_stats()
        
        return info
    else:
        return {"error": "Job not found", "job_id": job_id}

@app.get("/proxy/stats")
def get_proxy_stats():
    """Get current proxy pool statistics"""
    stats = smart_proxy_manager.get_proxy_stats()
    return {
        "proxy_stats": stats,
        "timestamp": time.time()
    }

@app.post("/proxy/reload")
def reload_proxies():
    """Reload proxy list from environment"""
    try:
        global smart_proxy_manager
        smart_proxy_manager = SmartProxyManager()
        stats = smart_proxy_manager.get_proxy_stats()
        return {
            "success": True,
            "message": "Proxy list reloaded successfully",
            "proxy_stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to reload proxies: {str(e)}"
        }

# ── Bulk scraping endpoints ──────────────────────────────────────────────────

class BulkJobRequest(BaseModel):
    urls: list[str]
    prompt: str
    format: str = "json"
    max_workers: int = 3
    max_retries: int = 2
    per_domain_delay_s: float = 2.0
    page_timeout_s: float = 45.0
    rotation_interval: int = 10
    use_ai_extraction: bool = False
    block_resources: bool = True


@app.post("/bulk")
async def create_bulk_job(req: BulkJobRequest):
    config = BulkJobConfig(
        urls=req.urls,
        prompt=req.prompt,
        output_format=req.format,
        max_workers=min(req.max_workers, 10),
        max_retries=req.max_retries,
        per_domain_delay_s=req.per_domain_delay_s,
        page_timeout_s=req.page_timeout_s,
        rotation_interval=req.rotation_interval,
        use_ai_extraction=req.use_ai_extraction,
        block_resources=req.block_resources,
    )
    state = await bulk_engine.create_job(config)
    bulk_engine.set_broadcast(broadcast)

    async def _run():
        await bulk_engine.run_job(state.job_id)

    tasks[state.job_id] = asyncio.create_task(_run())
    return {
        "job_id": state.job_id,
        "total_urls": len(req.urls),
        "max_workers": config.max_workers,
        "format": req.format,
    }


@app.get("/bulk/{job_id}")
def get_bulk_progress(job_id: str):
    state = bulk_engine.get_job(job_id)
    if not state:
        return {"error": "Job not found"}
    return {
        **state.progress,
        "tasks": [
            {"url": t.url, "status": t.status.value, "error": t.error, "attempts": t.attempts}
            for t in state.tasks
        ],
    }


@app.delete("/bulk/{job_id}")
def cancel_bulk_job(job_id: str):
    if bulk_engine.cancel_job(job_id):
        return {"message": "Job cancelled", "job_id": job_id}
    return {"error": "Job not found"}


@app.post("/bulk/{job_id}/resume")
async def resume_bulk_job(job_id: str):
    async def _run():
        await bulk_engine.resume_job(job_id)

    tasks[job_id] = asyncio.create_task(_run())
    return {"message": "Job resumed", "job_id": job_id}


# ── Structured scrape: URLs -> JSON rows for the generative dashboard ─────────
# Synchronous (awaits and returns rows in the response — not the async job/WS
# flow). Reuses extract_dom (HTML cleaning) + the configured Gemini MODEL with an
# array-aware parser, since neither existing path returns row-records. Ghost Mode
# is on via BrowserController.__aenter__. One bad URL is reported, never fatal.

class StructuredScrapeRequest(BaseModel):
    urls: list[str]
    prompt: str
    max_rows: int | None = None


_STRUCTURED_ROWS_PROMPT = (
    "You extract structured tabular data from a web page.\n"
    "USER GOAL: {prompt}\n"
    "SOURCE URL: {url}\n\n"
    "Return ONLY a JSON ARRAY of flat record objects that match the goal, e.g. "
    '[{{"name": "...", "price": "..."}}]. Every record MUST use the SAME keys. '
    "Use ONLY data present on the page — never invent values. No prose, no markdown.\n\n"
    "PAGE CONTENT:\n{content}"
)


def _parse_rows(raw: str) -> list:
    """Extract a JSON array of record dicts from an LLM reply (array-aware, tolerant)."""
    if not raw:
        return []
    start, end = raw.find("["), raw.rfind("]") + 1
    if start == -1 or end <= start:
        return []
    try:
        data = json.loads(raw[start:end])
    except json.JSONDecodeError:
        return []
    return [r for r in data if isinstance(r, dict)]


async def _scrape_one_structured(bc, url: str, prompt: str) -> list:
    """Scrape one URL into a list of flat record dicts (reuses extract_dom + Gemini)."""
    await bc.page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await bc.page.wait_for_timeout(1500)
    title = await bc.page.title()
    html = await bc.page.content()
    cleaned = extract_dom(html, url, title)
    content = json.dumps(cleaned, ensure_ascii=False)[:EXTRACTION_MAX_CHARS]
    prompt_text = _STRUCTURED_ROWS_PROMPT.format(prompt=prompt, url=url, content=content)
    # Gemini extraction with one retry — the API returns transient 5xx / deadline
    # errors under load, and a single retry absorbs most of them.
    response = None
    for attempt in range(2):
        try:
            response = await asyncio.to_thread(functools.partial(MODEL.generate_content, prompt_text))
            break
        except Exception as e:
            if attempt == 1:
                raise
            print(f"⚠️ Gemini extraction transient error, retrying: {e}")
    rows = _parse_rows(getattr(response, "text", "") or "")
    for r in rows:
        r.setdefault("_source_url", url)
    return rows


@app.post("/scrape/structured")
async def scrape_structured(req: StructuredScrapeRequest):
    """Scrape URLs and return structured JSON rows for the generative dashboard."""
    urls = [u for u in (req.urls or []) if isinstance(u, str) and u.strip()]
    if not urls:
        return {"success": False, "rows": [], "source": [], "error": "No URLs provided."}

    proxy_info = smart_proxy_manager.get_best_proxy()
    proxy = proxy_info.to_playwright_dict() if proxy_info else None
    proxy_country = proxy_info.location if proxy_info else None

    rows: list = []
    errors: list = []
    bc = BrowserController(headless=False, proxy=proxy,
                           proxy_country=proxy_country, block_resources=True)
    try:
        await bc.__aenter__()
        for url in urls:
            try:
                rows.extend(await _scrape_one_structured(bc, url, req.prompt))
            except Exception as e:
                print(f"⚠️ structured scrape failed for {url}: {e}")
                errors.append({"url": url, "error": str(e)})
            if req.max_rows and len(rows) >= req.max_rows:
                rows = rows[: req.max_rows]
                break
    except Exception as e:
        return {"success": False, "rows": [], "source": urls, "error": f"Browser error: {e}"}
    finally:
        try:
            await bc.__aexit__(None, None, None)
        except Exception:
            pass

    return {
        "success": bool(rows),
        "rows": rows,
        "source": urls,
        **({"error": f"{len(errors)} of {len(urls)} URL(s) failed"} if errors else {}),
    }


# Serve the built frontend (SPA). Prefer the production build in frontend/dist;
# fall back to a legacy build copied straight into frontend/. If the frontend
# isn't built, keep the API running and return a clear hint instead of crashing
# at startup (StaticFiles raises if the directory is missing).
_frontend_dist = Path("frontend/dist")
_frontend_root = Path("frontend")
if (_frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="static")
elif (_frontend_root / "index.html").exists() and not (_frontend_root / "src").exists():
    app.mount("/", StaticFiles(directory=str(_frontend_root), html=True), name="static")
else:
    print("⚠️  Frontend not built. Run: cd frontend && npm install && npm run build")

    @app.get("/")
    def _frontend_not_built():
        return {
            "status": "ok",
            "detail": "BrowserPilot API is running, but the frontend has not been built. "
                      "Run: cd frontend && npm install && npm run build",
        }

# Helper functions
async def broadcast(job_id: str, msg: dict):
    """Broadcast message to all subscribers of a job"""
    if job_id in ws_subscribers:
        for ws in list(ws_subscribers[job_id]):
            try:
                await ws.send_text(json.dumps(msg))
            except:
                ws_subscribers[job_id].discard(ws)

async def register_streaming_session(job_id: str, browser_ctrl):
    """Register streaming session information"""
    streaming_sessions[job_id] = browser_ctrl
    
    if browser_ctrl.enable_streaming:
        await browser_ctrl.start_streaming(quality=80)
    
    stream_info = browser_ctrl.get_streaming_info()
    await broadcast(job_id, {
        "type": "streaming_info",
        "streaming": stream_info
    })

# Cleanup on shutdown
@app.on_event("shutdown")
async def cleanup():
    """Cleanup resources on shutdown"""
    print("🧹 Cleaning up resources...")
    
    # Cleanup streaming sessions
    for job_id, browser_ctrl in streaming_sessions.items():
        try:
            await browser_ctrl.__aexit__(None, None, None)
            print(f"✅ Cleaned up streaming session: {job_id}")
        except Exception as e:
            print(f"❌ Error cleaning up session {job_id}: {e}")
    
    streaming_sessions.clear()
    job_info.clear()
    
    # Print final proxy stats
    final_stats = smart_proxy_manager.get_proxy_stats()
    print(f"📊 Final proxy stats: {final_stats}")
    
    print("✅ Cleanup completed")

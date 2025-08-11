import asyncio, json, os, uuid, shutil, base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from smart_browser_controller import SmartBrowserController  # Updated import
from proxy_manager import SmartProxyManager  # Updated import
from agent import run_agent
from fastapi.staticfiles import StaticFiles

app = FastAPI()

tasks = {} # job_id → async.Task
ws_subscribers = {} # job_id → { websocket, … }
streaming_sessions = {} # job_id → browser_controller
job_info = {} # job_id → { format, content_type, extension, prompt }

# Initialize global smart proxy manager
smart_proxy_manager = SmartProxyManager()

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
        response["stream_url"] = f"ws://localhost:8000/stream/{job_id}"
    
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
    
    if job_id not in streaming_sessions:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "No streaming session found for this job"
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
        "timestamp": asyncio.get_event_loop().time()
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

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

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

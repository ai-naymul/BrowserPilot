import asyncio, json, os, uuid, shutil, base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from backend.browser_controller import BrowserController
from backend.proxy_manager import ProxyManager
from backend.agent import run_agent
from fastapi.staticfiles import StaticFiles

app = FastAPI()

tasks = {} # job_id → async.Task
ws_subscribers = {} # job_id → { websocket, … }
streaming_sessions = {} # job_id → browser_controller

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

class JobRequest(BaseModel):
    prompt: str
    format: str = "txt" # txt | md | json | html | csv | pdf default is txt
    headless: bool = False
    enable_streaming: bool = False # New option for real-time browser streaming

@app.post("/job")
async def create_job(req: JobRequest):
    # Validate format
    valid_formats = ["txt", "md", "json", "html", "csv", "pdf"]
    if req.format not in valid_formats:
        req.format = "txt"
    
    job_id = str(uuid.uuid4())
    proxy = ProxyManager().get_proxy()
    
    print(f"🚀 Creating universal job {job_id}")
    print(f"📋 Goal: {req.prompt}")
    print(f"🌐 Format: {req.format}")
    print(f"🖥️ Headless: {req.headless}")
    print(f"📡 Streaming: {req.enable_streaming}")
    
    # Create the agent task
    coro = run_agent(job_id, req.prompt, req.format, req.headless, proxy, req.enable_streaming)
    tasks[job_id] = asyncio.create_task(coro)
    
    response = {"job_id": job_id, "format": req.format}
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
            # Receive messages from client (mouse/keyboard events)
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
                # Send keepalive ping
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
        # Create browser controller with streaming enabled
        browser_ctrl = BrowserController(headless=False, proxy=None, enable_streaming=True)
        
        # Start browser context
        await browser_ctrl.__aenter__()
        
        # Start streaming
        await browser_ctrl.start_streaming(quality=80)
        
        # Store session
        streaming_sessions[job_id] = browser_ctrl
        
        # Get streaming info
        stream_info = browser_ctrl.get_streaming_info()
        
        # Broadcast to connected clients
        await broadcast(job_id, {
            "type": "streaming_info",
            "streaming": stream_info
        })
        
        return stream_info
        
    except Exception as e:
        return {"enabled": False, "error": str(e)}

@app.get("/streaming/{job_id}")
async def get_streaming_info(job_id: str):
    """Get streaming connection information for a job"""
    if job_id in streaming_sessions:
        browser_ctrl = streaming_sessions[job_id]
        return browser_ctrl.get_streaming_info()
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
    file_path = OUTPUT_DIR / f"{job_id}.output"
    return FileResponse(path=file_path, filename=file_path.name)

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

# Helper for agent → frontend streaming
async def broadcast(job_id: str, msg: dict):
    """Broadcast message to all subscribers of a job"""
    if job_id in ws_subscribers:
        for ws in list(ws_subscribers[job_id]):
            try:
                await ws.send_text(json.dumps(msg))
            except:
                ws_subscribers[job_id].discard(ws)

# Function to register streaming session
async def register_streaming_session(job_id: str, browser_ctrl: BrowserController):
    """Register streaming session information"""
    streaming_sessions[job_id] = browser_ctrl
    
    # Start streaming if enabled
    if browser_ctrl.enable_streaming:
        await browser_ctrl.start_streaming(quality=80)
    
    # Broadcast streaming info to connected clients
    stream_info = browser_ctrl.get_streaming_info()
    await broadcast(job_id, {
        "type": "streaming_info",
        "streaming": stream_info
    })

# Exposed functions for agent.py
push = broadcast

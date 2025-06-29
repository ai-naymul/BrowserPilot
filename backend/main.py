import asyncio, json, os, uuid, shutil, base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from backend.browser_controller import BrowserController
from backend.proxy_manager import ProxyManager
from backend.agent import run_agent
from backend.vnc_proxy import start_vnc_proxy, stop_vnc_proxy
from fastapi.staticfiles import StaticFiles

app = FastAPI()
tasks = {}           # job_id → async.Task
ws_subscribers = {}  # job_id → { websocket, … }
vnc_sessions = {}    # job_id → vnc_info

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

class JobRequest(BaseModel):
    prompt: str
    format: str = "txt"     # txt | md | json | html default is txt
    headless: bool = False
    enable_vnc: bool = False  # New option for real-time browser viewing

@app.post("/job")
async def create_job(req: JobRequest):
    job_id = str(uuid.uuid4())
    proxy = ProxyManager().get_proxy()
    
    # Create the agent task with VNC option
    coro = run_agent(job_id, req.prompt, req.format, req.headless, proxy, req.enable_vnc)
    tasks[job_id] = asyncio.create_task(coro)
    
    print(f"Created job {job_id} with headless={req.headless}, vnc={req.enable_vnc}, proxy={proxy}")
    
    response = {"job_id": job_id}
    if req.enable_vnc:
        response["vnc_enabled"] = True
    
    return response

@app.websocket("/ws/{job_id}")
async def job_ws(ws: WebSocket, job_id: str):
    await ws.accept()
    ws_subscribers.setdefault(job_id, set()).add(ws)
    
    # Send VNC info if available
    if job_id in vnc_sessions:
        await ws.send_text(json.dumps({
            "type": "vnc_info",
            "vnc": vnc_sessions[job_id]
        }))
    
    try:
        while True:
            await ws.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        ws_subscribers[job_id].discard(ws)

@app.get("/download/{job_id}")
def download(job_id: str):
    file_path = OUTPUT_DIR / f"{job_id}.output"
    return FileResponse(path=file_path, filename=file_path.name)


@app.post("/vnc/create/{job_id}")
async def create_vnc_session(job_id: str):
    """Create a VNC session without starting a job"""
    if job_id in vnc_sessions:
        return vnc_sessions[job_id]
    
    # Create a minimal browser controller just for VNC
    try:
        browser_ctrl = BrowserController(headless=False, proxy=None, enable_vnc=True)
        await browser_ctrl._setup_vnc()
        
        vnc_info = browser_ctrl.get_vnc_info()
        if vnc_info.get("enabled"):
            websocket_port = await start_vnc_proxy(vnc_info["port"])
            if websocket_port:
                vnc_info["websocket_port"] = websocket_port
                vnc_info["websocket_url"] = f"ws://localhost:{websocket_port}"
                vnc_sessions[job_id] = vnc_info
                
                # Keep the browser controller alive
                vnc_sessions[job_id]["browser_ctrl"] = browser_ctrl
                
                await broadcast(job_id, {
                    "type": "vnc_info",
                    "vnc": vnc_info
                })
                
                return vnc_info
    except Exception as e:
        return {"enabled": False, "error": str(e)}


@app.get("/vnc/{job_id}")
async def get_vnc_info(job_id: str):
    """Get VNC connection information for a job"""
    if job_id in vnc_sessions:
        return vnc_sessions[job_id]
    return {"enabled": False, "error": "VNC not enabled for this job"}

# New endpoint to handle VNC cleanup
@app.delete("/vnc/{job_id}")
async def cleanup_vnc(job_id: str):
    """Clean up VNC session for a job"""
    if job_id in vnc_sessions:
        vnc_info = vnc_sessions[job_id]
        if vnc_info.get("websocket_port"):
            await stop_vnc_proxy(vnc_info["websocket_port"])
        del vnc_sessions[job_id]
        return {"message": "VNC session cleaned up"}
    return {"message": "No VNC session found"}

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

# Helper for agent → frontend streaming
async def broadcast(job_id: str, msg: dict):
    """Broadcast message to all subscribers of a job"""
    if job_id in ws_subscribers:
        for ws in list(ws_subscribers[job_id]):  # Create a copy to avoid modification during iteration
            try:
                await ws.send_text(json.dumps(msg))
            except:
                # Remove disconnected websockets
                ws_subscribers[job_id].discard(ws)

# Function to register VNC session
async def register_vnc_session(job_id: str, vnc_info: dict):
    """Register VNC session information"""
    if vnc_info.get("enabled"):
        # Start WebSocket proxy
        websocket_port = await start_vnc_proxy(vnc_info["port"])
        if websocket_port:
            vnc_info["websocket_port"] = websocket_port
            vnc_info["websocket_url"] = f"ws://localhost:{websocket_port}"
            
        vnc_sessions[job_id] = vnc_info
        
        # Broadcast VNC info to connected clients
        await broadcast(job_id, {
            "type": "vnc_info",
            "vnc": vnc_info
        })

# Exposed functions for agent.py
push = broadcast
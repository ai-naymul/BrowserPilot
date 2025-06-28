import asyncio, json, os, uuid, shutil, base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from backend.proxy_manager import ProxyManager
from backend.agent import run_agent
from fastapi.staticfiles import StaticFiles

app = FastAPI()
tasks = {}           # job_id → async.Task
ws_subscribers = {}  # job_id → { websocket, … }

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

class JobRequest(BaseModel):
    prompt: str
    format: str = "txt"     # txt | md | json | html default is txt
    headless: bool = False

@app.post("/job")
async def create_job(req: JobRequest):
    job_id = str(uuid.uuid4())
    proxy = ProxyManager().get_proxy()
    coro  = run_agent(job_id, req.prompt, req.format, req.headless, proxy)
    tasks[job_id] = asyncio.create_task(coro)
    print(f"Created job {job_id} with headless={req.headless}, proxy={proxy}")
    return {"job_id": job_id}

# TODO: implement the ws connection to stream the browser using the vnc and xvbf
@app.websocket("/ws/{job_id}")
async def job_ws(ws: WebSocket, job_id: str):
    await ws.accept()
    ws_subscribers.setdefault(job_id, set()).add(ws)
    try:
        while True:
            await ws.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        ws_subscribers[job_id].discard(ws)

# to download the output file
@app.get("/download/{job_id}")
def download(job_id: str):
    file_path = OUTPUT_DIR / f"{job_id}.output"
    return FileResponse(path=file_path, filename=file_path.name)

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
# helper for agent → frontend streaming
async def push(job_id: str, msg: dict):
    for ws in ws_subscribers.get(job_id, []):
        await ws.send_text(json.dumps(msg))

# exposed so agent.py can import it without circularity
broadcast = push
import os

from fastapi import BackgroundTasks, FastAPI, Request, HTTPException
from aiortc import RTCPeerConnection, RTCSessionDescription
from fastapi.middleware.cors import CORSMiddleware
from aiortc.contrib.media import MediaRelay
from contextlib import asynccontextmanager

from pydantic import BaseModel

from core.Camera_thread import Camera_thread
from core.frame_buffer import FrameBuffer

# from database.database import init_db, AsyncSessionLocal, Camera, Event, AIModel

import uuid
from sqlalchemy import text
import aiofiles
import httpx


EDGE_ID = "edge_node_1"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

class ModelSyncRequest(BaseModel):
    model_id: str
    version: str
    download_url: str

class CameraStartRequest(BaseModel):
    source: str
    model_filename: str



relay = None
cameras = {}
peer_connections = set()

@asynccontextmanager
async def lifespan(app: FastAPI):

    global relay, cameras
    relay = MediaRelay()

    # await init_db()
    # print("[SYSTEM] Edge db Initialized")


    print(f"==> [SYSTEM] Edge Node {EDGE_ID} is ONLINE")

    yield

    print(f"==> [SYSTEM] Shutting down Edge Node {EDGE_ID}....")

    coros = [pc.close() for pc in peer_connections]
    for coro in coros:
        await coro
    peer_connections.clear()

    for cam_id, cam_thread in cameras.items():
        if cam_thread :
            cam_thread.stop()
            print(f"Stopped camera {cam_id}")

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)
async def download_model(url: str, filename: str):
    filepath = os.path.join(MODEL_DIR, filename)
    if os.path.exists(filepath):
        print(f"==> Model {filename} already exists at {filepath}")
        return
    print(f"==> Downloading model from {url}")

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                async with aiofiles.open(filepath, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)
        print(f"==> Model downloaded and saved to {filepath}")
    except Exception as e:
        print(f"==> Error downloading model: {e}")

@app.post("/api/edge/sync_model")
async def sync_model(data: ModelSyncRequest, background_tasks: BackgroundTasks):
    filename = f"model_{data.model_id}_{data.version}.pt"
    background_tasks.add_task(download_model, data.download_url, filename)

    

    return {"message": "Model synchronization started", "filename": filename}

@app.post("/api/edge/start_camera/{camera_id}")
async def start_camera(camera_id: str, data: CameraStartRequest):
    if camera_id in cameras:
        return  {"message": f"Camera {camera_id} is already running"}
    
    clean_model_filename = os.path.basename(data.model_filename)
    model_path = os.path.join(MODEL_DIR, clean_model_filename)
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail=f"Model {clean_model_filename} not found on edge node")
    
    source = int(data.source) if data.source.isdigit() else data.source
    input_buffer = FrameBuffer(max_size=1)
    output_buffer = FrameBuffer(max_size=1)

    new_camera_thread = Camera_thread(
        camera_id = camera_id,
        source = source,
        model_path = model_path,
        input_buffer = input_buffer,
        output_buffer = output_buffer
    )
    cameras[camera_id] = new_camera_thread

    return {"message": f"Camera {camera_id} started successfully with model{clean_model_filename}"}

@app.post("/api/edge/stop_camera/{camera_id}")
async def stop_camera(camera_id: str):
    if camera_id in cameras:
        cameras[camera_id].stop()
        del cameras[camera_id]
        return {"message": f"Camera {camera_id} stopped successfully"}
    else:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")

@app.post("/offer/{camera_id}")
async def offer(camera_id: str, request: Request):
    if camera_id not in cameras:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    params = await request.json()
    offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])

    pc = RTCPeerConnection()
    peer_connections.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState in ["failed", "closed"]:
            peer_connections.discard(pc)

    pc.addTrack(relay.subscribe(cameras[camera_id]))

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}




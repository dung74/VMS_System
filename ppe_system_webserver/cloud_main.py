import asyncio
import json
import httpx
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager
import aiomqtt

from database.database import AsyncSessionLocal, init_db, Camera, AIModel, Event
from sqlalchemy import select

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

EDGE_NODES={
    "edge_node_1": "http://127.0.0.1:8001"

}

async def mqtt_listener_loop():
    while True:
        try:
            print("Connecting to MQTT broker...")
            async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:

                await client.subscribe("vms/events/#")
                print("Subscribed to topic: vms/events, waiting for messages...")

                async for message in client.messages:
                    payload_str = message.payload.decode()
                    event_data = json.loads(payload_str)
                    print(f"New event received {event_data['event_type']} from camera {event_data['camera_id']}")

                    async with AsyncSessionLocal() as session:
                        cam_query = await session.execute(select(Camera).where(Camera.camera_id == event_data["camera_id"]))
                        cam_db = cam_query.scalars().first()

                        if cam_db:
                            new_event = Event(
                                camera_id=cam_db.id,
                                model_id=cam_db.current_model_id,
                                event_type=event_data["event_type"],
                                metadata_info={"confidence": event_data.get("confidence", 0)}
                            )
                            session.add(new_event)
                            await session.commit()
                            print(f"Saved event {new_event.event_type} for camera {cam_db.camera_id} in database")
        except Exception as error:
            print(f"MQTT lost connection: {error}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[SYSTEM] Cloud DB Initialized.")

    mqtt_task = asyncio.create_task(mqtt_listener_loop())
    yield

    mqtt_task.cancel()
    print("==> [SYSTEM] Cloud server shutting down...")

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")

class ActionRequest(BaseModel):
    edge_id: str

class ModelCreate(BaseModel):
    name: str
    version: str
    file_path: str
    task_type: str = "detection"
class CameraCreate(BaseModel):
    camera_id: str
    name: str
    source: str
    location: str
    current_model_id: int


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/cloud/start_camera/{camera_id}")
async def cloud_start_camera(camera_id: str, payload: ActionRequest):
    edge_urls = EDGE_NODES.get(payload.edge_id)
    if not edge_urls:
        raise HTTPException(status_code=400, detail="Not found IP for edge node")
    
    async with AsyncSessionLocal() as session:
        camera_query = await session.execute(select(Camera).where(Camera.camera_id == camera_id))
        camera = camera_query.scalars().first()
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found in database")
        
        model_query = await session.execute(select(AIModel).where(AIModel.id == camera.current_model_id))
        model = model_query.scalars().first()
        edge_payload = {
            "source": camera.source,
            "model_filename": model.file_path
        }
        print(f"Sending request to edge node {payload.edge_id} to start camera {camera_id} with model {model.name}, path {model.file_path}")

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{edge_urls}/api/edge/start_camera/{camera_id}", json=edge_payload)
                resp.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Error connecting to edge node {payload.edge_id}: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to connect to edge node {payload.edge_id}: {e}")

@app.get("/api/cloud/get_stream_info/{camera_id}")
async def get_stream_info(camera_id: str):
    edge_id = "edge_node_1"
    edge_urls = EDGE_NODES.get(edge_id)

    return {
        "camera_id": camera_id,
        "webrtc_offer_url": f"{edge_urls}/offer/{camera_id}"
    }
@app.post("/api/cloud/add_camera")
async def add_camera(payload: CameraCreate):

    async with AsyncSessionLocal() as session:
        new_camera = Camera(
            camera_id=payload.camera_id,
            name=payload.name,
            source=payload.source,
            location=payload.location,
            status="active",
            current_model_id=payload.current_model_id
        )
        session.add(new_camera)
        await session.commit()
    return {"message": f"Camera {new_camera.name} added successfully"}

@app.post("/api/cloud/remove_camera/{camera_id}")
async def remove_camera(camera_id: str, payload: ActionRequest):
    edge_urls = EDGE_NODES.get(payload.edge_id)
    if not edge_urls:
        raise HTTPException(status_code=400, detail="Not found IP for edge node")
    
    async with AsyncSessionLocal() as session:
        camera_query = await session.execute(select(Camera).where(Camera.camera_id == camera_id))
        camera = camera_query.scalars().first()
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found in database")
        
        await session.delete(camera)
        await session.commit()
    return {"message": f"Camera {camera_id} removed successfully from edge node {payload.edge_id}"}


@app.post("/api/cloud/add_model")
async def add_model(payload: ModelCreate):
    async with AsyncSessionLocal() as session:
        new_model = AIModel(
            name=payload.name,
            version=payload.version,
            file_path=payload.file_path,
            task_type=payload.task_type,
            is_active=True
        )
        session.add(new_model)
        await session.commit()
    return {"message": f"Model {new_model.name} added successfully to cloud database"}

@app.post("/api/cloud/remove_model/{model_id}")
async def remove_model(model_id: int):
    async with AsyncSessionLocal() as session:
        model_query = await session.execute(select(AIModel).where(AIModel.id == model_id))
        model = model_query.scalars().first()
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found in database")
        
        await session.delete(model)
        await session.commit()
    return {"message": f"Model {model_id} removed successfully from cloud database"}

@app.get("/api/cloud/list_cameras")
async def list_cameras():
    async with AsyncSessionLocal() as session:
        camera_query = await session.execute(select(Camera))
        cameras = camera_query.scalars().all()
    return {"cameras": cameras}

@app.get("/api/cloud/list_models")
async def list_models():
    async with AsyncSessionLocal() as session:
        model_query = await session.execute(select(AIModel))
        models = model_query.scalars().all()
    return {"models": models}

@app.post("/api/cloud/stop_camera/{camera_id}")
async def cloud_stop_camera(camera_id: str, payload: ActionRequest):
    edge_urls = EDGE_NODES.get(payload.edge_id)
    if not edge_urls:
        raise HTTPException(status_code=400, detail="Not found IP for edge node")
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{edge_urls}/api/edge/stop_camera/{camera_id}")
            resp.raise_for_status()
            return {"message": f"Send request turn off camera {camera_id} to edge node {payload.edge_id} successfully"}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to edge node {payload.edge_id}: {e}")
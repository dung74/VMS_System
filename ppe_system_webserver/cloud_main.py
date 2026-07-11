import asyncio
import json
import httpx
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager
import aiomqtt

from database.database import AsyncSessionLocal, init_db, Camera, AIModel, Event, User
from sqlalchemy import select

from core.server_MQTT_sync import mqtt_config_handler
from core.auth import get_password_hash, verify_password,  create_access_token, get_current_user, require_user, require_admin

from typing import List, Optional

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

EDGE_NODES={
    "edge_node_1": "http://127.0.0.1:8001"

}
class CameraEditRequest(BaseModel):
    name: Optional[str] = None
    source: Optional[str] = None
    location: Optional[str] = None
    current_model_id: Optional[List[int]] = None 
class ModelEditRequest(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    file_path: Optional[str] = None
    task_type: Optional[str] = None
    parameters: Optional[dict] = None
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"  # Default role is "user"



async def mqtt_listener_loop():
    while True:
        try:
            print("Connecting to MQTT broker...")
            async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:

                await client.subscribe("ppe/events/#")
                print("Subscribed to topic: ppe/events, waiting for messages...")

                async for message in client.messages:
                    payload_str = message.payload.decode()
                    event_data = json.loads(payload_str)
                    print(f"New event received {event_data['event_type']} from camera {event_data['camera_id']}")

                    async with AsyncSessionLocal() as session:
                        cam_query = await session.execute(select(Camera).where(Camera.id == event_data["camera_id"]))
                        cam_db = cam_query.scalars().first()

                        if cam_db:
                            new_event = Event(
                                camera_id=event_data["camera_id"],
                                model_id=event_data["model_id"],
                                event_type=event_data["event_type"],
                                image_path = None,
                                video_path = None,
                                status='pending',
                                detections=event_data.get("detections"),
                                # timestamp=event_data["timestamp"],
                                metadata_info=event_data
                            )
                            session.add(new_event)
                            await session.commit()
                            print(f"Saved event {new_event.event_type} for camera {cam_db.id} in database")
        except Exception as error:
            print(f"MQTT lost connection: {error}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[SYSTEM] Cloud DB Initialized.")

    asyncio.create_task(mqtt_config_handler())


    print("==> [SYSTEM] Cloud server is ONLINE")

    mqtt_task = asyncio.create_task(mqtt_listener_loop())
    print("==> [SYSTEM] MQTT listener started, waiting for events...")

    yield

    mqtt_task.cancel()
    print("==> [SYSTEM] Cloud server shutting down...")


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")

class ActionRequest(BaseModel):
    edge_id: str




@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(get_current_user)):
    if not user:
        return templates.TemplateResponse(request=request, name="login.html")
    return templates.TemplateResponse(request=request, name="cameras.html", context={"active_page": "cameras", "user": user})

@app.get("/models", response_class=HTMLResponse)
async def view_models(request: Request, user: User = Depends(get_current_user)):
    if not user:
        return templates.TemplateResponse(request=request, name="login.html")
    return templates.TemplateResponse(request=request, name="models.html", context={"active_page": "models", "user": user})

@app.get("/events", response_class=HTMLResponse)
async def view_events(request: Request, user: User = Depends(get_current_user)):
    if not user:
        return templates.TemplateResponse(request=request, name="login.html")
    return templates.TemplateResponse(request=request, name="events.html", context={"active_page": "events", "user": user})






@app.post("/api/cloud/start_camera/{camera_id}", dependencies=[Depends(require_user)])
async def cloud_start_camera(camera_id: int, payload: ActionRequest):
    edge_urls = EDGE_NODES.get(payload.edge_id)
    if not edge_urls:
        raise HTTPException(status_code=400, detail="Not found IP for edge node")
    
    async with AsyncSessionLocal() as session:
        camera_query = await session.execute(select(Camera).where(Camera.id == camera_id))
        camera = camera_query.scalars().first()
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found in database")
        
        
        edge_payload = {
            "source": camera.source,
        }
        print(f"Sending request to edge node {payload.edge_id} to start camera {camera_id} with source {camera.source}")

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{edge_urls}/api/edge/start_camera/{camera_id}", json=edge_payload)
                resp.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Error connecting to edge node {payload.edge_id}: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to connect to edge node {payload.edge_id}: {e}")

@app.get("/api/cloud/get_stream_info/{camera_id}", dependencies=[Depends(require_user)])
async def get_stream_info(camera_id: int):
    edge_id = "edge_node_1"
    edge_urls = EDGE_NODES.get(edge_id)

    return {
        "camera_id": camera_id,
        "webrtc_offer_url": f"{edge_urls}/offer/{camera_id}"
    }

@app.post("/api/cloud/stop_camera/{camera_id}", dependencies=[Depends(require_user)])
async def cloud_stop_camera(camera_id: int, payload: ActionRequest):
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
    
@app.post("/api/cloud/add_camera", dependencies=[Depends(require_admin)])
async def add_camera(payload: CameraEditRequest):

    async with AsyncSessionLocal() as session:
        new_camera = Camera(
            # camera_id=payload.camera_id,
            name=payload.name,
            source=payload.source,
            location=payload.location,
            status="active",
            current_model_id=payload.current_model_id
        )
        session.add(new_camera)
        await session.commit()
    return {"message": f"Camera {new_camera.name} added successfully"}

@app.post("/api/cloud/remove_camera/{camera_id}", dependencies=[Depends(require_admin)])
async def remove_camera(camera_id: int, payload: ActionRequest):
    edge_urls = EDGE_NODES.get(payload.edge_id)
    if not edge_urls:
        raise HTTPException(status_code=400, detail="Not found IP for edge node")
    
    async with AsyncSessionLocal() as session:
        camera_query = await session.execute(select(Camera).where(Camera.id == camera_id))
        camera = camera_query.scalars().first()
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found in database")
        
        await session.delete(camera)
        await session.commit()
    return {"message": f"Camera {camera_id} removed successfully from edge node {payload.edge_id}"}


@app.post("/api/cloud/add_model", dependencies=[Depends(require_admin)])
async def add_model(payload: ModelEditRequest):
    async with AsyncSessionLocal() as session:
        new_model = AIModel(
            name=payload.name,
            type=payload.type,
            file_path=payload.file_path,
            task_type=payload.task_type,
            parameters={},
            is_active=True
        )
        session.add(new_model)
        await session.commit()
    return {"message": f"Model {new_model.name} added successfully to cloud database"}

@app.post("/api/cloud/remove_model/{model_id}", dependencies=[Depends(require_admin)])
async def remove_model(model_id: int):
    async with AsyncSessionLocal() as session:
        model_query = await session.execute(select(AIModel).where(AIModel.id == model_id))
        model = model_query.scalars().first()
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found in database")
        
        await session.delete(model)
        await session.commit()
    return {"message": f"Model {model_id} removed successfully from cloud database"}

@app.get("/api/cloud/list_cameras", dependencies=[Depends(require_user)])
async def list_cameras():
    async with AsyncSessionLocal() as session:
        camera_query = await session.execute(select(Camera))
        cameras = camera_query.scalars().all()
    return {"cameras": cameras}

@app.get("/api/cloud/list_models", dependencies=[Depends(require_user)])
async def list_models():
    async with AsyncSessionLocal() as session:
        model_query = await session.execute(select(AIModel))
        models = model_query.scalars().all()
    return {"models": models}



@app.patch("/api/cloud/edit_camera/{camera_id}", dependencies=[Depends(require_admin)])
async def edit_camera(camera_id: int, payload: CameraEditRequest):
    async with AsyncSessionLocal() as session:
        camera_query = await session.execute(select(Camera).where(Camera.id == camera_id))
        camera = camera_query.scalars().first()
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found in database")
        
        # Update the camera fields
        update_data = payload.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(camera, key, value)
        camera.status = "active"  # Ensure the camera is active after editing
        
        await session.commit()
    return {"message": f"Camera {camera_id} updated successfully"}

@app.patch("/api/cloud/edit_model/{model_id}", dependencies=[Depends(require_admin)])
async def edit_model(model_id: int, payload: ModelEditRequest):
    async with AsyncSessionLocal() as session:
        model_query = await session.execute(select(AIModel).where(AIModel.id == model_id))
        model = model_query.scalars().first()
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found in database")
        
        # Update the model fields
        update_data = payload.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(model, key, value)
        model.is_active = True
        await session.commit()
    return {"message": f"Model {model_id} updated successfully"}



@app.get("/api/cloud/list_events", dependencies=[Depends(require_user)])
async def list_events(page: int = 1, limit: int = 10):
    offset = (page - 1) * limit

    total_query = await AsyncSessionLocal().execute(select(Event.id))
    total_events = total_query.scalars().all()

    event_query = await AsyncSessionLocal().execute(
        select(Event).order_by(Event.created_at.desc()).offset(offset).limit(limit)
    )
    events = event_query.scalars().all()

    total_pages = (len(total_events) + limit - 1) //limit

    return {
        "events": events,
        "total_pages": total_pages,
        "current_page": page,
    }

@app.post("/api/cloud/auth/register")
async def register_user(user: UserCreate):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == user.username))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Username already exists")
        print(f"Registering new user: {user.username}, role: {user.role}, password: {user.password}")
        new_user = User(
            username=user.username,
            hashed_password=get_password_hash(user.password),
            email=user.email,
            role= "user"
        )
        session.add(new_user)
        await session.commit()
    return {"message": "User registered successfully", "username": new_user.username, "role": new_user.role}




@app.post("/api/cloud/auth/login")
async def login_user(response: Response, user: UserCreate):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == user.username))
        db_user = result.scalars().first()

        if not db_user or not verify_password(user.password, db_user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid username or password")
        
        access_token = create_access_token(data={"sub": db_user.username, "role": db_user.role})
        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=86400)  # 1 day in seconds
        return {"message": "Login successful", "access_token": access_token, "token_type": "bearer", "role": db_user.role}
    


@app.post("/api/cloud/auth/logout")
async def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logout successful"}

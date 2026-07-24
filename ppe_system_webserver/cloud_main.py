import asyncio
from datetime import datetime, timedelta, timezone
import json
import shutil
import uuid
import httpx
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends, Response, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from contextlib import asynccontextmanager
import aiomqtt

from database.database import AsyncSessionLocal, init_db, Camera, AIModel, Event, User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from core.server_MQTT_sync import mqtt_config_handler
from core.auth import get_password_hash, verify_password,  create_access_token, get_current_user, require_user, require_admin

from typing import List, Optional

import os

VN_TZ = timezone(timedelta(hours=7))  # Vietnam timezone (UTC+7)


# MQTT_BROKER = "localhost"
# MQTT_PORT = 1883

# EDGE_NODES={
#     "edge_node_1": "http://127.0.0.1:8001"

# }

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

# Tương tự với Edge Node
EDGE_NODES = {
    "edge_node_1": os.getenv("EDGE_NODE_1_URL", "http://127.0.0.1:8001")
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
                                event_code=event_data.get("event_code", str(uuid.uuid4().hex)),
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


os.makedirs("static_images", exist_ok=True)
app.mount("/media", StaticFiles(directory="static_images"), name="media")


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
        target_url = f"{edge_urls}/api/edge/start_camera/{camera_id}"
        
        # In rõ URL ra log để kiểm tra xem nó đang là 192.168.x hay 127.0.0.1
        print(f"Sending request to {payload.edge_id} -> TARGET URL: {target_url}")
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

    public_edge_url = "http://127.0.0.1:8001"
    # use when open browser on the same machine as the edge node. If you are accessing from a different machine, replace with the actual public IP or domain of the edge node.

    return {
        "camera_id": camera_id,
        # "webrtc_offer_url": f"{edge_urls}/offer/{camera_id}"
        "webrtc_offer_url": f"{public_edge_url}/offer/{camera_id}"

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
    async with AsyncSessionLocal() as session:
        total_query = await session.execute(select(Event.id))
        total_events = total_query.scalars().all()

        event_query = await session.execute(
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
            # role=user.role
            role="user"  # Force all new users to have the "user" role
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

@app.get("/api/cloud/auth/me", dependencies=[Depends(require_user)])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    return {"username": current_user.username, "email": current_user.email, "role": current_user.role}


@app.post("/api/cloud/auth/logout")
async def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logout successful"}



def cleanup_old_images(base_dir: str = "static_images", keep_days: int = 3):

    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} does not exist. No cleanup needed.")
        return
    current_date = datetime.now(VN_TZ).date()
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)

        if os.path.isdir(folder_path):
            try:
                folder_date = datetime.strptime(folder_name, "%Y-%m-%d").date()
                delta_days = (current_date - folder_date).days
                if delta_days > keep_days:
                    shutil.rmtree(folder_path)
                    print(f"Deleted folder {folder_path} as it is older than {keep_days} days.")
            except ValueError:
                print(f"Skipping folder {folder_path} as it does not match the date format YYYY-MM-DD.")
                continue

@app.post("/api/cloud/upload_image")
async def upload_image(
    background_tasks: BackgroundTasks,
    camera_id: int = Form(...),
    event_type: str = Form(...),
    event_code: str = Form(...),
    event_datetime: str = Form(...),
    file: UploadFile = File(...)
    ):

    date_part, time_part = event_datetime.split(" ")
    date_folder = date_part
    time_str = time_part.replace(":", "-")  # Replace ':' with '-' for filename compatibility


    background_tasks.add_task(cleanup_old_images)

    relative_folder = os.path.join(date_folder, f"cam{camera_id}")
    absolute_folder = os.path.join("static_images", relative_folder)
    os.makedirs(absolute_folder, exist_ok=True)



    file_name = f"cam{camera_id}_{event_type}_{event_code}_{time_str}.jpg"
    file_path = os.path.join(absolute_folder, file_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    db_image_path = f"/media/{relative_folder}/{file_name}".replace("\\", "/")  # Ensure the path uses forward slashes

    async with AsyncSessionLocal() as session:
        event_of_image_query = await session.execute(select(Event).where(Event.event_code == event_code))
        event_of_image = event_of_image_query.scalars().first()
        if event_of_image:
            event_of_image.image_path = db_image_path
            await session.commit()
        else:
            try:

                new_event = Event(
                    event_code=event_code,
                    camera_id=camera_id,
                    model_id=None,
                    event_type=event_type,
                    image_path=db_image_path,
                    video_path=None,
                    status='pending',
                    detections=[],
                    metadata_info={"event_datetime": event_datetime}
                )
                session.add(new_event)
                await session.commit()
            except IntegrityError:
                await session.rollback()
                return {"message": f"Event with event_code {event_code} already exists. Image not saved to database."}
    
    return {"message": "Image uploaded successfully", "image_path": db_image_path}

from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import Camera
from database.deps import get_db
from schemas.api_schemas import CameraEditRequest, ActionRequest
from core.auth import require_user, require_admin
from core.config import EDGE_NODES

router = APIRouter(prefix="/api/cloud", tags=["Cameras"])

@router.get("/list_cameras", dependencies=[Depends(require_user)])
async def list_cameras(db: AsyncSession = Depends(get_db)):
    camera_query = await db.execute(select(Camera))
    return {"cameras": camera_query.scalars().all()}

@router.post("/add_camera", dependencies=[Depends(require_admin)])
async def add_camera(payload: CameraEditRequest, db: AsyncSession = Depends(get_db)):
    new_camera = Camera(
        name=payload.name,
        source=payload.source,
        location=payload.location,
        status="active",
        current_model_id=payload.current_model_id
    )
    db.add(new_camera)
    await db.commit()
    return {"message": f"Camera {new_camera.name} added successfully"}

@router.patch("/edit_camera/{camera_id}", dependencies=[Depends(require_admin)])
async def edit_camera(camera_id: int, payload: CameraEditRequest, db: AsyncSession = Depends(get_db)):
    camera_query = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = camera_query.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found in database")
    
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(camera, key, value)
    camera.status = "active"
    await db.commit()
    return {"message": f"Camera {camera_id} updated successfully"}

@router.post("/remove_camera/{camera_id}", dependencies=[Depends(require_admin)])
async def remove_camera(camera_id: int, payload: ActionRequest, db: AsyncSession = Depends(get_db)):
    edge_urls = EDGE_NODES.get(payload.edge_id)
    if not edge_urls:
        raise HTTPException(status_code=400, detail="Not found IP for edge node")
    
    camera_query = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = camera_query.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found in database")
    
    await db.delete(camera)
    await db.commit()
    return {"message": f"Camera {camera_id} removed successfully from edge node {payload.edge_id}"}

@router.post("/start_camera/{camera_id}", dependencies=[Depends(require_user)])
async def cloud_start_camera(camera_id: int, payload: ActionRequest, db: AsyncSession = Depends(get_db)):
    edge_urls = EDGE_NODES.get(payload.edge_id)
    if not edge_urls:
        raise HTTPException(status_code=400, detail="Not found IP for edge node")
    
    camera_query = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = camera_query.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found in database")
    
    edge_payload = {"source": camera.source}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{edge_urls}/api/edge/start_camera/{camera_id}", json=edge_payload)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to edge node {payload.edge_id}: {e}")
    return {"message": f"Camera {camera_id} started successfully"}

@router.post("/stop_camera/{camera_id}", dependencies=[Depends(require_user)])
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

@router.get("/get_stream_info/{camera_id}", dependencies=[Depends(require_user)])
async def get_stream_info(camera_id: int):
    public_edge_url = "http://127.0.0.1:8001" 
    return {
        "camera_id": camera_id,
        "webrtc_offer_url": f"{public_edge_url}/offer/{camera_id}"
    }
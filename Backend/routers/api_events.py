import os
import shutil
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database.database import Event
from database.deps import get_db
from core.auth import require_user

router = APIRouter(prefix="/api/cloud", tags=["Events"])
VN_TZ = timezone(timedelta(hours=7))

def cleanup_old_images(base_dir: str = "static_images", keep_days: int = 3):
    if not os.path.exists(base_dir):
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
            except ValueError:
                continue

@router.get("/list_events", dependencies=[Depends(require_user)])
async def list_events(page: int = 1, limit: int = 10, db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * limit
    total_query = await db.execute(select(Event.id))
    total_events = total_query.scalars().all()

    event_query = await db.execute(
        select(Event).order_by(Event.created_at.desc()).offset(offset).limit(limit)
    )
    events = event_query.scalars().all()
    total_pages = (len(total_events) + limit - 1) // limit

    return {
        "events": events,
        "total_pages": total_pages,
        "current_page": page,
    }

@router.post("/upload_image")
async def upload_image(
    background_tasks: BackgroundTasks,
    camera_id: int = Form(...),
    event_type: str = Form(...),
    event_code: str = Form(...),
    event_datetime: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    date_part, time_part = event_datetime.split(" ")
    time_str = time_part.replace(":", "-")
    
    background_tasks.add_task(cleanup_old_images)

    relative_folder = os.path.join(date_part, f"cam{camera_id}")
    absolute_folder = os.path.join("static_images", relative_folder)
    os.makedirs(absolute_folder, exist_ok=True)

    file_name = f"cam{camera_id}_{event_type}_{event_code}_{time_str}.jpg"
    file_path = os.path.join(absolute_folder, file_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    db_image_path = f"/media/{relative_folder}/{file_name}".replace("\\", "/")

    event_query = await db.execute(select(Event).where(Event.event_code == event_code))
    event_of_image = event_query.scalars().first()
    
    if event_of_image:
        event_of_image.image_path = db_image_path
        await db.commit()
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
            db.add(new_event)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            return {"message": f"Event with event_code {event_code} already exists. Image not saved to database."}
    
    return {"message": "Image uploaded successfully", "image_path": db_image_path}
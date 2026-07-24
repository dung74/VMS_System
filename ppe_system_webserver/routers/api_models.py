from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import AIModel
from database.deps import get_db
from schemas.api_schemas import ModelEditRequest
from core.auth import require_user, require_admin

router = APIRouter(prefix="/api/cloud", tags=["Models"])

@router.get("/list_models", dependencies=[Depends(require_user)])
async def list_models(db: AsyncSession = Depends(get_db)):
    model_query = await db.execute(select(AIModel))
    return {"models": model_query.scalars().all()}

@router.post("/add_model", dependencies=[Depends(require_admin)])
async def add_model(payload: ModelEditRequest, db: AsyncSession = Depends(get_db)):
    new_model = AIModel(
        name=payload.name,
        type=payload.type,
        file_path=payload.file_path,
        task_type=payload.task_type,
        parameters={},
        is_active=True
    )
    db.add(new_model)
    await db.commit()
    return {"message": f"Model {new_model.name} added successfully to cloud database"}

@router.patch("/edit_model/{model_id}", dependencies=[Depends(require_admin)])
async def edit_model(model_id: int, payload: ModelEditRequest, db: AsyncSession = Depends(get_db)):
    model_query = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = model_query.scalars().first()
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found in database")
    
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)
    model.is_active = True
    await db.commit()
    return {"message": f"Model {model_id} updated successfully"}

@router.post("/remove_model/{model_id}", dependencies=[Depends(require_admin)])
async def remove_model(model_id: int, db: AsyncSession = Depends(get_db)):
    model_query = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = model_query.scalars().first()
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found in database")
    
    await db.delete(model)
    await db.commit()
    return {"message": f"Model {model_id} removed successfully from cloud database"}
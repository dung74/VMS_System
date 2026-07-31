from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database.deps import get_db
from database.database import User
from core.auth import require_admin, get_password_hash
from schemas.api_schemas import UserCreate, UserResponse, UserUpdate


router = APIRouter(
    prefix="/api/cloud/users",
    tags=["Users Management"],
    dependencies=[Depends(require_admin)]
)


@router.get("/", response_model=List[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.post("/")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        email=user.email,
        role=user.role
    )
    db.add(new_user)
    await db.commit()
    return {"message": f"User {new_user.username} created successfully"}


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.username == "admin1":
        raise HTTPException(status_code=403, detail="Cannot delete an admin root user")

    await db.delete(user)
    await db.commit()
    return {"message": f"User {user.username} deleted successfully"}
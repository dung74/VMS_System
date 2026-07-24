from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import User
from database.deps import get_db
from schemas.api_schemas import UserCreate
from core.auth import get_password_hash, verify_password, create_access_token, get_current_user, require_user

router = APIRouter(prefix="/api/cloud/auth", tags=["Auth"])

@router.post("/register")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        email=user.email,
        role="user" 
    )
    db.add(new_user)
    await db.commit()
    return {"message": "User registered successfully", "username": new_user.username, "role": new_user.role}

@router.post("/login")
async def login_user(response: Response, user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalars().first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": db_user.username, "role": db_user.role})
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=86400)
    return {"message": "Login successful", "access_token": access_token, "token_type": "bearer", "role": db_user.role}

@router.get("/me", dependencies=[Depends(require_user)])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return {"username": current_user.username, "email": current_user.email, "role": current_user.role}

@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logout successful"}
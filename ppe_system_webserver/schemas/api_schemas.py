from pydantic import BaseModel
from typing import List, Optional


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
    role: str = "user"
class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

class ActionRequest(BaseModel):
    edge_id: str
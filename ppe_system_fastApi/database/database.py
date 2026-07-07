import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

# 1. THIẾT LẬP KẾT NỐI BẤT ĐỒNG BỘ
# Cú pháp: postgresql+asyncpg://<username>:<password>@<host>:<port>/<dbname>
DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/ppe_db_edge"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

# =====================================================================
# 2. ĐỊNH NGHĨA CÁC CLASS (ORM MODELS)
# =====================================================================

class AIModel(Base):
    __tablename__ = 'ai_models'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    file_path = Column(String(255), nullable=False)
    task_type = Column(String(50), default='detection')
    parameters = Column(JSONB, default=dict)  
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class Camera(Base):
    __tablename__ = 'cameras'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    source = Column(String(255), nullable=False)
    location = Column(String(150))
    status = Column(String(20), default='active')
    # current_model_id = Column(Integer, ForeignKey('ai_models.id', ondelete='SET NULL'))
    # one camera can have many model
    current_model_id = Column(JSONB, default=list)  # Store a list of model IDs
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class Event(Base):
    __tablename__ = 'events'
    
    # Sử dụng UUID tự sinh cho khóa chính
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(50), ForeignKey('cameras.camera_id', ondelete='CASCADE'))
    model_id = Column(Integer, ForeignKey('ai_models.id', ondelete='SET NULL'))
    event_type = Column(String(50), nullable=False)
    image_path = Column(String(255))
    video_path = Column(String(255))
    status = Column(String(20), default='pending')
    
    # Trường JSONB mạnh mẽ của PostgreSQL
    detections = Column(JSONB, default=list)
    metadata_info = Column(JSONB, default=dict) # Đổi tên tránh trùng keyword metadata
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# Hàm tiện ích để tự động tạo bảng nếu chưa có
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
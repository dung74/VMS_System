import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import timezone, timedelta
import os


DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:123456@localhost:5432/ppe_db_edge"
)
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

VN_TZ = timezone(timedelta(hours=7))  # Vietnam timezone (UTC+7)
def get_vn_timezone():
    
    return datetime.now(VN_TZ)  # Vietnam timezone (UTC+7)

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
    created_at = Column(DateTime(timezone=True), default=get_vn_timezone)
    updated_at = Column(DateTime(timezone=True), default=get_vn_timezone, onupdate=get_vn_timezone)

class Camera(Base):
    __tablename__ = 'cameras'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    # camera_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    source = Column(String(255), nullable=False)
    location = Column(String(150))
    status = Column(String(20), default='active')
    # current_model_id = Column(Integer, ForeignKey('ai_models.id', ondelete='SET NULL'))
    # one camera can have many model
    current_model_id = Column(JSONB, default=list)  # Store a list of model IDs
    created_at = Column(DateTime(timezone=True), default=get_vn_timezone)
    updated_at = Column(DateTime(timezone=True), default=get_vn_timezone, onupdate=get_vn_timezone)

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_code = Column(String(100), unique=True, nullable=False)
    camera_id = Column(Integer, ForeignKey('cameras.id', ondelete='CASCADE'))
    model_id = Column(Integer, ForeignKey('ai_models.id', ondelete='SET NULL'))
    event_type = Column(String(50), nullable=False)
    image_path = Column(String(255))
    video_path = Column(String(255))
    status = Column(String(20), default='pending')
    
    detections = Column(JSONB, default=list)
    metadata_info = Column(JSONB, default=dict) # Đổi tên tránh trùng keyword metadata
    
    created_at = Column(DateTime(timezone=True), default=get_vn_timezone)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if os.path.exists("init.sql"):
        # Đọc nội dung file
        with open("init.sql", "r", encoding="utf-8") as f:
            sql_commands = f.read()
            
        async with engine.begin() as conn:
            for command in sql_commands.split(';'):
                if command.strip():
                    await conn.execute(text(command))
        
        print("Đã nạp dữ liệu mặc định từ file init.sql thành công!")
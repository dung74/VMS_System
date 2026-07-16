-- Kích hoạt extension để tự động sinh chuỗi UUID ngẫu nhiên
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================
-- 1. BẢNG QUẢN LÝ AI MODELS
-- =====================================================================
CREATE TABLE ai_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,               -- Ví dụ: 'YOLOv8-PPE-Detection'
    version VARCHAR(20) NOT NULL,             -- Ví dụ: 'v1.3.2'
    file_path VARCHAR(255) NOT NULL,          -- Đường dẫn file: 'models/best.pt'
    task_type VARCHAR(50) DEFAULT 'detection', -- 'detection', 'classification', 'counting'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- 2. BẢNG QUẢN LÝ CAMERAS
-- =====================================================================
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    cam_id VARCHAR(50) UNIQUE NOT NULL,       -- Mã định danh dạng text: 'cam1', 'cam_iphone'
    name VARCHAR(100) NOT NULL,               -- Tên gợi nhớ: 'Camera Cổng Chính'
    source VARCHAR(255) NOT NULL,             -- Cổng vật lý hoặc link mạng: '0', 'rtsp://...'
    location VARCHAR(150),                    -- Vị trí lắp đặt
    status VARCHAR(20) DEFAULT 'active',      -- 'active', 'inactive', 'error'
    current_model_id INT REFERENCES ai_models(id) ON DELETE SET NULL, -- Model đang chạy trên cam này
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- 3. BẢNG QUẢN LÝ SỰ KIỆN (EVENTS / VI PHẠM)
-- =====================================================================
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), -- Dùng UUID để tránh trùng lặp khi mở rộng hệ thống
    camera_id INT REFERENCES cameras(id) ON DELETE CASCADE,
    model_id INT REFERENCES ai_models(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,          -- Loại sự kiện: 'no_helmet', 'vehicle_counting'
    image_path VARCHAR(255),                  -- Đường dẫn ảnh chụp lúc xảy ra sự kiện
    video_path VARCHAR(255),                  -- Đường dẫn clip ngắn (nếu có)
    status VARCHAR(20) DEFAULT 'pending',     -- Trạng thái xử lý: 'pending', 'verified', 'false_alarm'
    
    -- Trường JSONB ma thuật của Postgres để lưu danh sách vật thể kèm tọa độ bounding box
    -- Cấu trúc mẫu: [{"label": "person", "box": [10, 20, 100, 200], "conf": 0.89}]
    detections JSONB DEFAULT '[]'::jsonb, 
    
    metadata JSONB DEFAULT '[]'::jsonb,      -- Lưu thông tin mở rộng (VD: số lượng xe máy: 5, ô tô: 2)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- 4. KHU VỰC TẠO INDEX ĐỂ TỐI ƯU TỐC ĐỘ TRUY VẤN (QUAN TRỌNG)
-- =====================================================================
-- Index theo thời gian vì Dashboard sẽ liên tục lấy các sự kiện mới nhất
CREATE INDEX idx_events_created_at ON events(created_at DESC);

-- Index khóa ngoại để tăng tốc các câu lệnh JOIN lấy sự kiện theo từng Camera
CREATE INDEX idx_events_camera_id ON events(camera_id);

-- GIN Index cho trường JSONB để có thể tìm kiếm siêu tốc các vật thể bên trong cấu trúc JSON
CREATE INDEX idx_events_detections_gin ON events USING gin (detections);
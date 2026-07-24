# PPE System (Cloud + Edge + Frontend)

Hệ thống giám sát PPE theo mô hình **Cloud - Edge AI**, gồm 3 phần chính:

- **Cloud WebServer** (`ppe_system_webserver`): quản lý user/camera/model, nhận sự kiện từ Edge, lưu ảnh sự kiện, cung cấp API.
- **Edge FastAPI** (`ppe_system_fastApi`): chạy AI theo camera, stream WebRTC, publish sự kiện MQTT, upload ảnh về Cloud.
- **Frontend React** (`ppe_system_frontend`): giao diện quản trị (login, camera, model, events).

---

## 1) Kiến trúc tổng quan

```text
Frontend React (Vite)
        |
        v
Cloud API (FastAPI) <----- MQTT -----> Edge AI (FastAPI)
        |                                   |
        v                                   v
   Cloud PostgreSQL                    Edge PostgreSQL
        ^
        |
  Ảnh sự kiện upload từ Edge
```

Luồng chính:
1. Cloud quản lý cấu hình camera/model.
2. Edge định kỳ gửi yêu cầu đồng bộ qua MQTT.
3. Cloud publish cấu hình cho Edge qua MQTT.
4. Edge chạy detection, publish event MQTT và upload ảnh lên Cloud.
5. Frontend hiển thị camera/model/sự kiện qua Cloud API.

---

## 2) Cấu trúc thư mục

```text
ppe_system/
├── ppe_system_webserver/     # Cloud service (FastAPI + Jinja2 templates)
│   ├── cloud_main.py
│   ├── core/
│   ├── database/
│   ├── templates/
│   ├── static_images/
│   ├── init.sql
│   ├── docker-compose.yaml
│   └── .env.sample
├── ppe_system_fastApi/       # Edge service (FastAPI + AI + WebRTC)
│   ├── edge_main.py
│   ├── core/
│   ├── ai_models/
│   ├── database/
│   ├── init.sql
│   ├── docker-compose.yaml
│   └── .env.sample
├── ppe_system_frontend/      # Frontend React + Vite + Tailwind
│   ├── src/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
└── createdb.sql              # Script schema tham khảo
```

---

## 3) Công nghệ sử dụng

### Backend/Edge
- Python 3.10
- FastAPI + Uvicorn
- SQLAlchemy async + asyncpg + PostgreSQL
- aiomqtt (MQTT)
- aiortc + av (WebRTC)
- OpenCV + Ultralytics YOLO

### Frontend
- React 19 + Vite 8
- react-router-dom
- axios
- Tailwind CSS

---

## 4) Chạy bằng Docker (khuyến nghị)

> Cả Cloud và Edge dùng chung external network `ppe_shared_net`.

### Bước 1: Tạo env, network dùng chung
```bash
conda create -n ai_env python=3.10
```

```bash
docker network create ppe_shared_net
```

### Bước 2: Chuẩn bị biến môi trường

```bash
cp ppe_system_webserver/.env.sample ppe_system_webserver/.env
cp ppe_system_fastApi/.env.sample ppe_system_fastApi/.env
```

Sau đó chỉnh các biến trong `.env` theo hạ tầng thật.

### Bước 3: Chạy Cloud stack

```bash
cd ppe_system_webserver
docker compose up -d --build
```

Mặc định:
- Cloud API: `http://localhost:8000`
- Cloud DB host port: `5433`
- Cloud MQTT host port: `1884`

### Bước 4: Chạy Edge stack

```bash
cd ppe_system_fastApi
docker compose up -d --build
```

Mặc định:
- Edge API: `http://localhost:8001`
- Edge DB host port: `5436`
- Edge MQTT host port: `1885`

### Bước 5: Chạy Frontend

**Cách A (local dev):**
```bash
cd ppe_system_frontend
npm install
npm run dev
```
Truy cập: `http://localhost:5173`

Frontend dev server đã cấu hình proxy `/api/cloud` về `http://localhost:8000`.

**Cách B (Docker Nginx):**
```bash
cd ppe_system_frontend
docker build -t ppe_frontend .
docker run -d --name ppe_frontend --network ppe_shared_net -p 8080:80 ppe_frontend
```
Truy cập: `http://localhost:8080`

---

## 5) Biến môi trường quan trọng

### Cloud (`ppe_system_webserver/.env`)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DB_HOST_PORT` (mặc định `5433`)
- `MQTT_HOST_PORT` (mặc định `1884`)
- `MQTT_BROKER` (Docker: `web_mqtt`)
- `MQTT_PORT` (nội bộ container: `1883`)
- `EDGE_NODE_1_URL` (Docker: `http://edge_ai:8001`)
- `CLOUD_API_PORT` (mặc định `8000`)

### Edge (`ppe_system_fastApi/.env`)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DB_HOST_PORT` (mặc định `5436`)
- `MQTT_HOST_PORT` (mặc định `1885`)
- `MQTT_BROKER` (Docker: `edge_mqtt`)
- `MQTT_PORT` (nội bộ container: `1883`)
- `EDGE_URL` (Docker: `http://cloud_api:8000`)
- `EDGE_AI_PORT` (mặc định `8001`)

---

## 6) API chính

### Cloud API (`cloud_main.py`)
- Auth:
  - `POST /api/cloud/auth/register`
  - `POST /api/cloud/auth/login`
  - `GET /api/cloud/auth/me`
  - `POST /api/cloud/auth/logout`
- Camera:
  - `GET /api/cloud/list_cameras`
  - `POST /api/cloud/add_camera`
  - `PATCH /api/cloud/edit_camera/{camera_id}`
  - `POST /api/cloud/remove_camera/{camera_id}`
  - `POST /api/cloud/start_camera/{camera_id}`
  - `POST /api/cloud/stop_camera/{camera_id}`
  - `GET /api/cloud/get_stream_info/{camera_id}`
- Model:
  - `GET /api/cloud/list_models`
  - `POST /api/cloud/add_model`
  - `PATCH /api/cloud/edit_model/{model_id}`
  - `POST /api/cloud/remove_model/{model_id}`
- Event:
  - `GET /api/cloud/list_events`
  - `POST /api/cloud/upload_image`

### Edge API (`edge_main.py`)
- `POST /api/edge/sync_model`
- `POST /api/edge/start_camera/{camera_id}`
- `POST /api/edge/stop_camera/{camera_id}`
- `POST /offer/{camera_id}` (WebRTC signaling)

---

## 7) Frontend routes hiện có

Theo `src/App.jsx`:
- `/login`
- `/` (camera dashboard)
- `/models`
- `/events`

---

## 8) AI models đang hỗ trợ ở Edge

Thông qua `ModelFactory`:
- `person_card`
- `cell_phone`
- `person_only`

---

## 9) Dữ liệu seed

Khi service khởi động, `init_db()` sẽ:
1. tạo bảng nếu chưa có,
2. nạp dữ liệu từ `init.sql` (nếu file tồn tại).

Cloud seed có sẵn user/camera/model mẫu để test nhanh.

---

## 10) Chạy không Docker (tham khảo)

### Cloud
```bash
cd ppe_system_webserver
pip install -r requirements.txt
uvicorn cloud_main:app --host 0.0.0.0 --port 8000
```

### Edge
```bash
cd ppe_system_fastApi
pip install -r requirements.txt
uvicorn edge_main:app --host 0.0.0.0 --port 8001
```

### Frontend
```bash
cd ppe_system_frontend
npm install
npm run dev
```

---

## 11) Lưu ý vận hành

- Edge container cần quyền thiết bị camera (`/dev/video0`...).
- Nếu Cloud/Edge ở 2 máy khác nhau, cập nhật `EDGE_NODE_1_URL` và `EDGE_URL` theo IP/domain thật.
- Ảnh sự kiện lưu tại `ppe_system_webserver/static_images/`.
- Cloud hiện có route UI Jinja (`/`, `/models`, `/events`), đồng thời dự án cũng có frontend React tách riêng.

# PPE System (Cloud + Edge + Frontend)

Hệ thống giám sát PPE theo mô hình **Cloud - Edge AI**, gồm 3 phần chính:

- **Cloud WebServer** (`ppe_system_webserver`): quản lý user/camera/model, nhận sự kiện từ Edge, lưu ảnh sự kiện, cung cấp API.
- **Edge FastAPI** (`ppe_system_fastApi`): chạy AI theo camera, stream WebRTC, publish sự kiện MQTT, upload ảnh về Cloud.
- **Frontend React** (`ppe_system_frontend`): giao diện quản trị (login, camera, model, events).
# PPE System (Cloud + Edge + Frontend)



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
1. Edge định kỳ gửi yêu cầu sync cấu hình qua MQTT.
2. Cloud publish config camera/model cho Edge.
3. Edge chạy detection theo cấu hình local.
4. Edge publish event qua MQTT topic `ppe/events/#`.
5. Edge upload ảnh event về `POST /api/cloud/upload_image`.
6. Frontend lấy dữ liệu từ Cloud API để hiển thị.

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
├── ppe_system_webserver/
│   ├── cloud_main.py                # Entry Cloud API
│   ├── routers/                     # API routers (auth/cameras/models/events)
│   ├── services/                    # MQTT listener service
│   ├── schemas/                     # Pydantic request schemas
│   ├── core/                        # auth, config, mqtt config handler
│   ├── database/                    # SQLAlchemy models + deps + init
│   ├── static_images/               # Lưu ảnh sự kiện
│   ├── templates/                   # Template cũ (không mount route trong cloud_main hiện tại)
│   ├── init.sql
│   ├── docker-compose.yaml
│   └── .env.sample
├── ppe_system_fastApi/       # Edge service (FastAPI + AI + WebRTC)
│   ├── edge_main.py
│   ├── core/
│   ├── ai_models/
│   ├── database/
│   ├── init.sql
├── ppe_system_fastApi/
│   ├── edge_main.py                 # Entry Edge API
│   ├── core/                        # Camera thread, frame buffer, MQTT sync
│   ├── ai_models/                   # person_card, cell_phone, person_only...
│   ├── database/                    # SQLAlchemy models + init
│   ├── init.sql
│   ├── docker-compose.yaml
│   └── .env.sample
├── ppe_system_frontend/
│   ├── src/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
└── createdb.sql
```

---

## 3) Công nghệ sử dụng

### Cloud/Edge
- Python 3.10
- FastAPI + Uvicorn
- SQLAlchemy async + asyncpg + PostgreSQL
- aiomqtt
- aiortc + av (WebRTC)
- OpenCV + Ultralytics YOLO (Edge)

### Frontend
- React 19 + Vite 8
- react-router-dom
- axios
- Tailwind CSS

---

## 4) Chạy bằng Docker (khuyến nghị)

### Bước 1: Tạo network dùng chung
```bash
docker network create ppe_shared_net
```

### Bước 2: Chuẩn bị env
```bash
cp ppe_system_webserver/.env.sample ppe_system_webserver/.env
cp ppe_system_fastApi/.env.sample ppe_system_fastApi/.env
```

### Bước 3: Chạy Cloud
```bash
cd ppe_system_webserver
docker compose up -d --build
```

Mặc định:
- Cloud API: `http://localhost:8000`
- Cloud DB: `5433`
- Cloud MQTT: `1884`

### Bước 4: Chạy Edge
```bash
cd ppe_system_fastApi
docker compose up -d --build
```

Mặc định:
- Edge API: `http://localhost:8001`
- Edge DB: `5436`
- Edge MQTT: `1885`

### Bước 5: Chạy Frontend

**Local dev**
```bash
cd ppe_system_frontend
npm install
npm run dev
```
Truy cập: `http://localhost:5173`  
(Vite proxy `/api/cloud` -> `http://localhost:8000`)

**Docker**
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
- `DB_HOST_PORT` (default `5433`)
- `MQTT_HOST_PORT` (default `1884`)
- `MQTT_BROKER` (`web_mqtt` khi chạy Docker)
- `MQTT_PORT` (`1883` nội bộ)
- `EDGE_NODE_1_URL` (vd `http://edge_ai:8001`)
- `CLOUD_API_PORT` (default `8000`)

### Edge (`ppe_system_fastApi/.env`)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DB_HOST_PORT` (default `5436`)
- `MQTT_HOST_PORT` (default `1885`)
- `MQTT_BROKER` (`edge_mqtt` khi chạy Docker)
- `MQTT_PORT` (`1883` nội bộ)
- `EDGE_URL` (vd `http://cloud_api:8000`)
- `EDGE_AI_PORT` (default `8001`)

---

## 6) API hiện có

### Cloud
**Auth**
- `POST /api/cloud/auth/register`
- `POST /api/cloud/auth/login`
- `GET /api/cloud/auth/me`
- `POST /api/cloud/auth/logout`

**Cameras**
- `GET /api/cloud/list_cameras`
- `POST /api/cloud/add_camera`
- `PATCH /api/cloud/edit_camera/{camera_id}`
- `POST /api/cloud/remove_camera/{camera_id}`
- `POST /api/cloud/start_camera/{camera_id}`
- `POST /api/cloud/stop_camera/{camera_id}`
- `GET /api/cloud/get_stream_info/{camera_id}`

**Models**
- `GET /api/cloud/list_models`
- `POST /api/cloud/add_model`
- `PATCH /api/cloud/edit_model/{model_id}`
- `POST /api/cloud/remove_model/{model_id}`

**Events**
- `GET /api/cloud/list_events`
- `POST /api/cloud/upload_image`

### Edge
- `POST /api/edge/sync_model`
- `POST /api/edge/start_camera/{camera_id}`
- `POST /api/edge/stop_camera/{camera_id}`
- `POST /offer/{camera_id}` (WebRTC signaling)

---

## 7) Frontend routes

Theo `ppe_system_frontend/src/App.jsx`:
- `/login`
- `/`
- `/models`
- `/events`

---

## 8) AI models hiện hỗ trợ (Edge)

- `person_card`
- `cell_phone`
- `person_only`

---

## 9) Seed dữ liệu

Khi service khởi động:
1. `init_db()` tạo bảng nếu chưa có.
2. Nạp dữ liệu từ `init.sql` nếu file tồn tại.

---

## 10) Chạy local không Docker (tham khảo)

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

## 11) Ghi chú vận hành

- Edge cần mount thiết bị camera (`/dev/video0`...).
- Nếu Cloud và Edge chạy khác máy, cập nhật `EDGE_NODE_1_URL` và `EDGE_URL` theo IP/domain thật.
- Ảnh sự kiện lưu trong `ppe_system_webserver/static_images/`.
- Trong bản Cloud hiện tại, route template page trong `pages.py` đang được comment; luồng UI chính là frontend React.

Tk ADMIN: admin1
password: 123456

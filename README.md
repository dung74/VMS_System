# PPE System (Cloud + Edge AI)

Hệ thống giám sát PPE theo kiến trúc **Cloud - Edge**, gồm:

- **Cloud WebServer** (`ppe_system_webserver`): quản trị camera/model/user, nhận sự kiện và ảnh, hiển thị dashboard.
- **Edge FastAPI** (`ppe_system_fastApi`): đọc camera, chạy AI detection, phát stream WebRTC, gửi event lên Cloud.
- **PostgreSQL** cho mỗi cụm (Cloud DB, Edge DB).
- **MQTT** để đồng bộ cấu hình và truyền sự kiện.

---

## 1) Kiến trúc tổng quan

```text
[Camera/RTSP/USB]
       |
       v
[Edge AI - FastAPI]
  - Nhận cấu hình từ Cloud qua MQTT
  - Chạy model AI theo từng camera
  - Publish event MQTT
  - Upload ảnh sự kiện về Cloud API
  - Cấp WebRTC stream (/offer/{camera_id})
       |
       v
[Cloud WebServer - FastAPI + Jinja2]
  - CRUD camera/model/user
  - Lắng nghe event MQTT
  - Lưu event + ảnh vào DB/storage
  - Dashboard: /, /models, /events
```

---

## 2) Cấu trúc thư mục

```text
ppe_system/
├── ppe_system_fastApi/         # Edge service
│   ├── edge_main.py            # Entry API Edge
│   ├── core/                   # Camera thread, AI, MQTT sync, frame buffer
│   ├── ai_models/              # Predictor classes (person_card, cell_phone, person_only)
│   ├── database/               # SQLAlchemy models + init DB
│   ├── init.sql                # Seed dữ liệu camera/model
│   ├── docker-compose.yaml
│   ├── Dockerfile
│   └── .env.sample
├── ppe_system_webserver/       # Cloud service
│   ├── cloud_main.py           # Entry API Cloud + UI routes
│   ├── core/                   # Auth + MQTT sync handler
│   ├── database/               # SQLAlchemy models + init DB
│   ├── templates/              # login/cameras/models/events
│   ├── static_images/          # Ảnh sự kiện upload
│   ├── init.sql                # Seed camera/model/user
│   ├── docker-compose.yaml
│   ├── Dockerfile
│   └── .env.sample
├── createdb.sql                # Script schema tham khảo
└── outputtest/                 # Thư mục output thử nghiệm model
```

---

## 3) Công nghệ sử dụng

- Python 3.10
- FastAPI, Uvicorn
- SQLAlchemy Async + asyncpg + PostgreSQL
- aiomqtt (MQTT)
- aiortc + av (WebRTC stream)
- OpenCV + Ultralytics YOLO
- Jinja2 (Cloud UI)

---

## 4) Chạy hệ thống bằng Docker Compose (khuyến nghị)

> Cả Cloud và Edge dùng chung external network `ppe_shared_net`.

### Bước 1: Tạo network dùng chung

```bash
docker network create ppe_shared_net
```

### Bước 2: Cấu hình môi trường

Sao chép file mẫu:

```bash
cp ppe_system_webserver/.env.sample ppe_system_webserver/.env
cp ppe_system_fastApi/.env.sample ppe_system_fastApi/.env
```

Điền lại biến môi trường cho phù hợp hạ tầng.

### Bước 3: Chạy Cloud stack

```bash
cd ppe_system_webserver
docker compose up -d --build
```

- Cloud API mặc định: `http://localhost:8000`
- DB Cloud host port mặc định: `5433`
- MQTT Cloud host port mặc định: `1884`

### Bước 4: Chạy Edge stack

```bash
cd ppe_system_fastApi
docker compose up -d --build
```

- Edge API mặc định: `http://localhost:8001`
- DB Edge host port mặc định: `5436`
- MQTT Edge host port mặc định: `1885`

---

## 5) Biến môi trường chính

### Cloud (`ppe_system_webserver/.env`)

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DB_HOST_PORT` (mặc định `5433`)
- `MQTT_BROKER` (trong docker thường là `web_mqtt`)
- `MQTT_PORT` (mặc định `1883` nội bộ container)
- `EDGE_NODE_1_URL` (URL Edge API, ví dụ `http://edge_ai:8001`)
- `CLOUD_API_PORT` (mặc định `8000`)

### Edge (`ppe_system_fastApi/.env`)

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DB_HOST_PORT` (mặc định `5436`)
- `MQTT_BROKER` (trong docker thường là `edge_mqtt`)
- `MQTT_PORT` (mặc định `1883` nội bộ container)
- `EDGE_URL` (URL Cloud API để upload ảnh, ví dụ `http://cloud_api:8000`)
- `EDGE_AI_PORT` (mặc định `8001`)

---

## 6) Luồng đồng bộ Cloud - Edge - MQTT


1. Edge chạy `periodic_sync_request()` publish yêu cầu full sync mỗi 30s lên topic:
   - `edge/edge_node_1/sync_request`
2. Cloud `mqtt_config_handler()` nhận yêu cầu, lấy camera/model active từ DB.
3. Cloud publish cấu hình lên:
   - `server/config/edge_node_1`
4. Edge `mqtt_config_listener()` nhận payload và cập nhật DB local.
5. Khi AI phát hiện object:
   - Edge publish event lên `ppe/events/{camera_id}`
   - Cloud listener subscribe `ppe/events/#` và ghi event vào DB
   - Edge upload ảnh sự kiện qua `POST /api/cloud/upload_image`

---



## 7) API chính

### Cloud API (`cloud_main.py`)

- Auth:
  - `POST /api/cloud/auth/register`
  - `POST /api/cloud/auth/login`
  - `POST /api/cloud/auth/logout`
- Camera:
  - `POST /api/cloud/start_camera/{camera_id}`
  - `POST /api/cloud/stop_camera/{camera_id}`
  - `POST /api/cloud/add_camera` (admin)
  - `PATCH /api/cloud/edit_camera/{camera_id}` (admin)
  - `POST /api/cloud/remove_camera/{camera_id}` (admin)
  - `GET /api/cloud/list_cameras`
- Model:
  - `POST /api/cloud/add_model` (admin)
  - `PATCH /api/cloud/edit_model/{model_id}` (admin)
  - `POST /api/cloud/remove_model/{model_id}` (admin)
  - `GET /api/cloud/list_models`
- Event:
  - `GET /api/cloud/list_events`
  - `POST /api/cloud/upload_image`
- Stream helper:
  - `GET /api/cloud/get_stream_info/{camera_id}`

UI routes: `/login`, `/`, `/models`, `/events`

### Edge API (`edge_main.py`)

- `POST /api/edge/sync_model`
- `POST /api/edge/start_camera/{camera_id}`
- `POST /api/edge/stop_camera/{camera_id}`
- `POST /offer/{camera_id}` (WebRTC signaling)

---

## 8) AI models đang hỗ trợ

Qua `ModelFactory`:

- `person_card`
- `cell_phone`
- `person_only`

Model file mặc định nằm trong thư mục `models/` của Edge service.

---

## 9) Database schema chính (Cloud/Edge)

- `ai_models`: thông tin model AI
- `cameras`: nguồn camera + model gán cho camera (`current_model_id` dạng JSON list)
- `events`: sự kiện phát hiện + detections JSON
- `users` (chỉ Cloud): người dùng + role (`admin` / `user`)

Khi service khởi động, `init_db()` sẽ:

1. Tạo bảng nếu chưa có
2. Nạp seed từ `init.sql` nếu file tồn tại

---

## 10) Ghi chú vận hành

- Cần mount đúng thiết bị camera cho Edge container (`/dev/video0`...).
- Nếu Cloud và Edge nằm trên 2 máy khác nhau, cập nhật `EDGE_NODE_1_URL` và `EDGE_URL` theo IP/domain thật.
- `mosquitto.conf` ở Edge đang cấu hình bridge sang `web_mqtt:1883` để đồng bộ topic 2 chiều.
- Thư mục ảnh sự kiện được lưu trong `ppe_system_webserver/static_images/` và mount vào container Cloud.

---

## 12) Giao diện hiển thị
Giao diện chính ( quản lý camera, xem stream)
<img width="2812" height="1658" alt="Screenshot From 2026-07-17 10-37-03" src="https://github.com/user-attachments/assets/cd427b4b-3561-4e33-96a2-fbd77162ea02" />
Quản lý sự kiện
<img width="2380" height="1386" alt="Screenshot From 2026-07-17 10-42-57" src="https://github.com/user-attachments/assets/4baa64ed-1a5d-4172-b7d3-d6d13c79c2a6" />
Quản lý model
<img width="2826" height="1668" alt="Screenshot From 2026-07-17 10-43-59" src="https://github.com/user-attachments/assets/ca6865a1-a483-425b-965d-2ee0a13c9053" />
Đăng nhập, đăng ký
<img width="2826" height="1668" alt="Screenshot From 2026-07-17 10-44-14" src="https://github.com/user-attachments/assets/a3e319be-f91e-483d-b888-70a0e67cf476" />






## 11) Chạy local không Docker (tham khảo)

Mỗi service cần:

1. Cài dependencies từ `requirements.txt`
2. Có PostgreSQL + MQTT broker sẵn
3. Thiết lập biến môi trường tương ứng
4. Chạy:
   - Cloud: `uvicorn cloud_main:app --host 0.0.0.0 --port 8000`
   - Edge: `uvicorn edge_main:app --host 0.0.0.0 --port 8001`

---

Nếu cần, có thể tách tiếp thành:

- README tổng ở root (file này)
- README riêng cho `ppe_system_webserver`
- README riêng cho `ppe_system_fastApi`

để tài liệu chi tiết hơn theo từng service.



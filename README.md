# VMS System

Hệ thống giám sát camera phân tán gồm Cloud API, Edge AI và giao diện web. Cloud quản lý người dùng, camera, model và sự kiện; Edge lấy cấu hình từ Cloud, chạy nhận diện YOLO trên luồng camera, phát WebRTC và gửi sự kiện/ảnh về Cloud.

## Thành phần và luồng dữ liệu

```text
React + Vite / Nginx
        │ HTTP / WebRTC signaling
        ▼
Cloud API ── PostgreSQL (Cloud) ── static_images/
   ▲  │
   │  └──── MQTT (web_mqtt) ⇄ MQTT bridge ⇄ MQTT (edge_mqtt)
   │                                             │
   └────────── ảnh sự kiện qua HTTP ─────────────┤
                                                 ▼
                                      Edge AI + PostgreSQL (Edge)
                                                 │
                                      Camera / RTSP + YOLO + WebRTC
```

- Edge gửi yêu cầu đồng bộ định kỳ 30 giây qua MQTT. Cloud trả về toàn bộ camera đang `active` và model đang `is_active`; Edge ghi đè dữ liệu camera/model cục bộ theo gói đồng bộ.
- Khi một camera được bật từ Cloud, Cloud gọi Edge qua HTTP. Edge đọc camera/RTSP, chạy các model gắn với camera, vẽ detection lên frame và phát frame bằng WebRTC.
- Với detection mới theo `track_id`, Edge publish sự kiện vào `ppe/events/{camera_id}` và upload ảnh JPEG lên Cloud. Cloud lưu event, ảnh và phục vụ ảnh dưới `/media/...`.

## Cấu trúc thư mục

```text
ppe_system/
├── ppe_system_webserver/        # (BE)Cloud FastAPI, DB, MQTT listener và ảnh sự kiện
├── ppe_system_fastApi/          # (BE_AI)Edge FastAPI, nhận diện YOLO, WebRTC và MQTT bridge
├── ppe_system_frontend/         # (FE)React 19 + Vite + Tailwind
├── createdb.sql                 # Schema SQL cũ,  
```

Các model có sẵn ở `ppe_system_fastApi/models/`: `best(33).pt`, `yolov8m.pt`, `yolov8n.pt` và `yolo11n.pt`.

## Yêu cầu

- Docker Engine kèm Docker Compose plugin để chạy các service.
- Camera tương thích OpenCV hoặc URL RTSP để Edge nhận luồng.
- Nếu chạy Edge trong Docker với webcam vật lý, máy chủ phải có `/dev/video0`; Compose đã map thiết bị này vào container.

## Chạy bằng Docker

Từ thư mục gốc, tạo network dùng chung một lần:

```bash
docker network create ppe_shared_net
```

Tạo file cấu hình nếu chưa có:

```bash
cp ppe_system_webserver/.env.sample ppe_system_webserver/.env
cp ppe_system_fastApi/.env.sample ppe_system_fastApi/.env
```

Điền giá trị database phù hợp trong hai file `.env`. Với hai Compose chạy cùng một máy và cùng network, giữ các hostname nội bộ mặc định:

- Cloud: `DATABASE_URL=...@web_db:5432/ppe_db`, `MQTT_BROKER=web_mqtt`, `EDGE_NODE_1_URL=http://edge_ai:8001`.
- Edge: `DATABASE_URL=...@edge_db:5432/ppe_db_edge`, `MQTT_BROKER=edge_mqtt`, `EDGE_URL=http://cloud_api:8000`.

Khởi động Cloud trước, rồi Edge:

```bash
cd ppe_system_webserver
docker compose up -d --build

cd ../ppe_system_fastApi
docker compose up -d --build
```

Chạy Frontend bằng Compose (cũng dùng network trên):

```bash
cd ../ppe_system_frontend
docker compose up -d --build
```

Các cổng mặc định:

| Service | Địa chỉ |
| --- | --- |
| Cloud API | `http://localhost:8000` |
| Cloud PostgreSQL | `localhost:5433` |
| Cloud MQTT | `localhost:1884` |
| Edge API | `http://localhost:8001` |
| Edge PostgreSQL | `localhost:5436` |
| Edge MQTT | `localhost:1885` |
| Frontend Docker | `http://localhost:3000` |

Lần khởi động đầu tiên, mỗi API tạo bảng từ SQLAlchemy rồi chạy `init.sql` cùng thư mục để seed model, camera và user nếu ID chưa tồn tại. Các volume PostgreSQL được giữ lại giữa các lần `docker compose down` thông thường.

## Chạy Frontend khi phát triển

```bash
cd ppe_system_frontend
npm install
npm run dev
```

Vite phục vụ ứng dụng tại `http://localhost:5173` và proxy `/api/cloud` đến `http://localhost:8000`. Bản Docker dùng Nginx, chuyển mọi request `/api/` đến container `cloud_api:8000` và hỗ trợ SPA fallback.

## API đang được mount

Cloud API không mount các HTML template cũ trong `templates/`; giao diện chính là React frontend. Cloud có CORS mở cho mọi origin và sử dụng cookie `access_token`/JWT cho các endpoint bảo vệ.

### Xác thực

| Phương thức | Endpoint | Quyền |
| --- | --- | --- |
| POST | `/api/cloud/auth/login` | Công khai |
| GET | `/api/cloud/auth/me` | User đã đăng nhập |
| POST | `/api/cloud/auth/logout` | Công khai |

`POST /api/cloud/auth/register` không tồn tại trong mã hiện tại. Dữ liệu seed có tài khoản `admin1`; mật khẩu mặc định được ghi trong source trước đây là `123456`. Hãy thay đổi thông tin đăng nhập và khóa JWT trước khi triển khai thực tế.

### Camera và stream

| Phương thức | Endpoint | Quyền |
| --- | --- | --- |
| GET | `/api/cloud/list_cameras` | User |
| POST | `/api/cloud/add_camera` | Admin |
| PATCH | `/api/cloud/edit_camera/{camera_id}` | Admin |
| POST | `/api/cloud/remove_camera/{camera_id}` | Admin |
| POST | `/api/cloud/start_camera/{camera_id}` | User |
| POST | `/api/cloud/stop_camera/{camera_id}` | User |
| GET | `/api/cloud/get_stream_info/{camera_id}` | User |
| POST | `/api/edge/start_camera/{camera_id}` | Edge |
| POST | `/api/edge/stop_camera/{camera_id}` | Edge |
| POST | `/offer/{camera_id}` | Edge WebRTC signaling |

Start/stop từ Cloud nhận body `{"edge_id":"edge_node_1"}`. `get_stream_info` hiện trả về URL WebRTC cố định `http://127.0.0.1:8001/offer/{camera_id}`, vì vậy trình duyệt phải truy cập được Edge qua địa chỉ này. Nếu Cloud/Edge/người dùng nằm khác máy, URL này chưa được cấu hình qua biến môi trường.

### Model, sự kiện và người dùng

| Phương thức | Endpoint | Quyền |
| --- | --- | --- |
| GET | `/api/cloud/list_models` | User |
| POST | `/api/cloud/add_model` | Admin |
| PATCH | `/api/cloud/edit_model/{model_id}` | Admin |
| POST | `/api/cloud/remove_model/{model_id}` | Admin |
| GET | `/api/cloud/list_events?page=1&limit=10` | User |
| POST | `/api/cloud/upload_image` | Công khai, multipart |
| GET | `/api/cloud/users/` | Admin |
| POST | `/api/cloud/users/` | Admin |
| DELETE | `/api/cloud/users/{user_id}` | Admin |

Edge còn có `POST /api/edge/sync_model`, tải model theo URL ở background. Endpoint này độc lập với luồng MQTT và hiện không được Frontend gọi.

## Giao diện

Sau khi đăng nhập, Frontend cung cấp các route:

- `/` — danh sách camera; admin có thể thêm/sửa/xóa camera, mọi user đã đăng nhập có thể bật/tắt AI và mở video WebRTC.
- `/models` — xem model; admin có thể thêm/sửa/xóa.
- `/events` — danh sách event phân trang, phóng to ảnh và xem JSON detections.
- `/users` — chỉ hiển thị liên kết cho admin, tạo/xóa người dùng; không cho xóa user `admin1`.

Edge hỗ trợ ba `type` model thông qua `ModelFactory`: `person_card`, `cell_phone` và `person_only`. Cả ba dùng Ultralytics YOLO tracking (ByteTrack) trên CPU.

## Lưu ý về trạng thái hiện tại

- Hai Mosquitto broker đều cho phép anonymous access. Edge bridge toàn bộ topic (`topic # both 0`) sang Cloud broker.
- Sự kiện được lọc theo `track_id` với khoảng cách tối thiểu 2 giây; thư mục ảnh quá 3 ngày được dọn khi Cloud nhận upload ảnh mới.
- Cloud `requirements.txt` hiện có dòng `python-multipartaiofiles` thay vì dependency `python-multipart` cần cho `UploadFile`/`Form`. Nếu container Cloud không khởi động được do multipart, đây là lỗi dependency của source hiện tại, không phải bước cấu hình bị thiếu.
- Trường chọn model của form Camera trong Frontend dùng tên `current_model`, trong khi Cloud schema nhận `current_model_id`. Vì vậy việc gắn model từ form hiện có thể không được lưu đúng; có thể kiểm tra/chỉnh API trực tiếp nếu cần.
- `createdb.sql` mô tả schema cũ, khác ORM hiện tại. Cơ chế khởi tạo đang dùng là `database/database.py` và `init.sql` trong từng service.

## Chạy API trực tiếp (tham khảo)

Các lệnh này cần PostgreSQL, MQTT, biến môi trường và model/camera được chuẩn bị thủ công; Docker Compose là cách chạy được cấu hình sẵn trong repository.

```bash
cd ppe_system_webserver
pip install -r requirements.txt
uvicorn cloud_main:app --host 0.0.0.0 --port 8000

cd ../ppe_system_fastApi
pip install -r requirements.txt
uvicorn edge_main:app --host 0.0.0.0 --port 8001
```

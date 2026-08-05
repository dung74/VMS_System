# VMS System

Distributed camera surveillance platform with three main parts:

- **Cloud API** for authentication, camera/model/user management, event storage, and MQTT coordination.
- **Edge AI** for camera capture, YOLO-based inference, WebRTC streaming, and event publishing.
- **Web Frontend** for operators/admins to manage cameras, models, events, and users.

The system is designed to keep long-running video processing close to the camera while centralizing management and event history in the cloud.

## Key capabilities

- JWT-based authentication with cookie/session support
- Role-based access control: `admin` and `user`
- Camera CRUD and camera-to-model assignment
- Edge-controlled camera start/stop from the Cloud API
- Live WebRTC video streaming from Edge AI
- Event detection history with image preview and JSON payload viewer
- Cloud-side model CRUD
- Admin user management
- MQTT-based sync between cloud and edge nodes
- PostgreSQL storage on both cloud and edge
- Docker Compose setup for the full stack

## System architecture

```text
React + Vite + Tailwind
        |
        |  /api/cloud
        v
Cloud API  <------------------------+
   |                                |
   | PostgreSQL                     | MQTT
   v                                |
Cloud DB                            Edge MQTT Bridge
   |                                |
   | static_images/                 v
   +---- /media/*             Edge AI + PostgreSQL
                                   |
                                   | Camera / RTSP / /dev/video0
                                   v
                              YOLO + ByteTrack + WebRTC
```

### Data flow

1. The frontend talks to the Cloud API.
2. The Cloud API stores users, cameras, models, and events in PostgreSQL.
3. The Cloud and Edge services exchange sync messages through MQTT.
4. When a camera is started, Cloud forwards the request to Edge.
5. Edge reads the camera source, runs YOLO inference, draws detections, and streams the result through WebRTC.
6. When a new detection is accepted, Edge publishes an event to MQTT and uploads an event image back to Cloud.
7. Cloud stores the event record and serves the image under `/media/...`.

## Technologies used

- **Backend:** FastAPI, SQLAlchemy, asyncpg, Pydantic, JWT, Passlib, HTTPX, aiofiles
- **Edge AI:** FastAPI, aiortc, aiomqtt, OpenCV, Ultralytics YOLO, AV, HTTPX
- **Frontend:** React 19, Vite, React Router, Axios, Tailwind CSS
- **Database:** PostgreSQL
- **Messaging:** MQTT / Mosquitto
- **Deployment:** Docker, Docker Compose

## Repository structure

```text
ppe_system/
├── Backend/      # Cloud FastAPI service, DB, MQTT listener, event image storage
├── Edge_ai/      # Edge FastAPI service, camera capture, YOLO, WebRTC, MQTT bridge
├── Frontend/     # React dashboard
└── createdb.sql  # Legacy schema file
```

## Main application features

### Cloud API

- Login, logout, and current-user lookup
- List/add/edit/remove cameras
- Start/stop cameras on a selected edge node
- Expose WebRTC offer URL for a camera
- List/add/edit/remove AI models
- List events with pagination
- Upload and store event images
- Create/list/delete users

### Edge AI

- Start camera streams from RTSP URLs, USB devices, or indexed sources
- Build a WebRTC track per active camera
- Run YOLO-based detection models per camera
- Publish detections to MQTT
- Upload event images to the Cloud API
- Periodically sync cameras/models from the cloud via MQTT

### Web Frontend

- Login screen
- Camera management page
- Model management page
- Event history page
- User management page for admins
- Embedded WebRTC live video wall

## Supported AI model types

The current Edge implementation supports these model types through `ModelFactory`:

- `person_card`
- `cell_phone`
- `person_only`

Default model files are stored in `Edge_ai/models/`.

## Prerequisites

- Docker Engine and Docker Compose plugin
- A camera source that OpenCV can open, or a valid RTSP URL
- If you want to use a physical webcam inside Docker, the host should expose `/dev/video0`

## Configuration

Copy the sample environment files before starting:

```bash
cp Backend/.env.sample Backend/.env
cp Edge_ai/.env.sample Edge_ai/.env
```

Update the important values:

### Cloud

- `DATABASE_URL`
- `MQTT_BROKER`
- `MQTT_PORT`
- `EDGE_NODE_1_URL`

### Edge

- `DATABASE_URL`
- `MQTT_BROKER`
- `MQTT_PORT`
- `EDGE_URL`

If Cloud and Edge run on different machines, replace the default service hostnames such as `edge_ai` and `cloud_api` with real IP addresses or reachable hostnames.

## Run the full stack with Docker

### 1) Create the shared network

```bash
docker network create ppe_shared_net
```

### 2) Start Cloud

```bash
cd Backend
docker compose up -d --build
```

### 3) Start Edge

```bash
cd ../Edge_ai
docker compose up -d --build
```

### 4) Start Frontend

```bash
cd ../Frontend
docker compose up -d --build
```

### Default ports

| Service | URL |
| --- | --- |
| Cloud API | `http://localhost:8000` |
| Cloud PostgreSQL | `localhost:5433` |
| Cloud MQTT | `localhost:1884` |
| Edge API | `http://localhost:8001` |
| Edge PostgreSQL | `localhost:5436` |
| Edge MQTT | `localhost:1885` |
| Frontend | `http://localhost:3000` |

## Run the frontend in development

```bash
cd Frontend
npm install
npm run dev
```

Vite serves the app at `http://localhost:3000` and proxies `/api/cloud` to `http://localhost:8000`.

## API overview

### Authentication

| Method | Endpoint | Access |
| --- | --- | --- |
| POST | `/api/cloud/auth/login` | Public |
| GET | `/api/cloud/auth/me` | Authenticated user |
| POST | `/api/cloud/auth/logout` | Public |

Notes:

- There is **no public register endpoint** in the current codebase.
- Users are seeded in the database or created by admins.

### Cameras and streaming

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/cloud/list_cameras` | User |
| POST | `/api/cloud/add_camera` | Admin |
| PATCH | `/api/cloud/edit_camera/{camera_id}` | Admin |
| POST | `/api/cloud/remove_camera/{camera_id}` | Admin |
| POST | `/api/cloud/start_camera/{camera_id}` | User |
| POST | `/api/cloud/stop_camera/{camera_id}` | User |
| GET | `/api/cloud/get_stream_info/{camera_id}` | User |
| POST | `/api/edge/start_camera/{camera_id}` | Edge internal |
| POST | `/api/edge/stop_camera/{camera_id}` | Edge internal |
| POST | `/offer/{camera_id}` | WebRTC signaling |

The Cloud start/stop endpoints expect a body like:

```json
{ "edge_id": "edge_node_1" }
```

### Models, events, and users

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/cloud/list_models` | User |
| POST | `/api/cloud/add_model` | Admin |
| PATCH | `/api/cloud/edit_model/{model_id}` | Admin |
| POST | `/api/cloud/remove_model/{model_id}` | Admin |
| GET | `/api/cloud/list_events?page=1&limit=10` | User |
| POST | `/api/cloud/upload_image` | Public multipart upload |
| GET | `/api/cloud/users/` | Admin |
| POST | `/api/cloud/users/` | Admin |
| DELETE | `/api/cloud/users/{user_id}` | Admin |

### Edge-only utility endpoint

- `POST /api/edge/sync_model`

This downloads a model file in the background and is not currently called by the frontend.

## Frontend routes

- `/login` - login page
- `/` - camera management
- `/models` - model management
- `/events` - event history and image viewer
- `/users` - admin user management

## Current project notes

- The Cloud and Edge Mosquitto brokers allow anonymous access.
- Edge syncs camera/model data from Cloud every 30 seconds over MQTT.
- Event uploads are deduplicated using `track_id` timing logic on the edge.
- Old image folders older than 3 days are cleaned up on Cloud when a new upload arrives.
- `get_stream_info` currently returns a hard-coded Edge URL of `http://127.0.0.1:8001`.
  If Cloud/Edge/browser are on different hosts, this must be aligned with your deployment.
- `createdb.sql` is a legacy schema file; the live startup flow uses SQLAlchemy models plus each service's `init.sql`.
- The repository currently seeds default users, cameras, and models on first startup.

## Seed data

Initial database records are loaded from each service's `init.sql`.

### Default users

- `user1`
- `user2`
- `admin1`

`admin1` is protected from deletion in the current implementation.

### Default models

- `person_card`
- `cell_phone`
- `person_only`

### Default cameras

Several sample cameras are seeded for local testing, including RTSP and indexed-source examples.

## Run the APIs directly

Docker Compose is the recommended way to run the project, but the services can also be started manually.

### Cloud

```bash
cd Backend
pip install -r requirements.txt
uvicorn cloud_main:app --host 0.0.0.0 --port 8000
```

### Edge

```bash
cd ../Edge_ai
pip install -r requirements.txt
uvicorn edge_main:app --host 0.0.0.0 --port 8001
```

## Notes for production use

- Replace the default JWT secret before deploying.
- Use strong PostgreSQL credentials.
- Review public endpoints such as image upload and broker access before exposing the system to the internet.
- Ensure camera URLs and Edge hostnames are reachable from the running environment.

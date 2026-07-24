import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.database import init_db
from core.server_MQTT_sync import mqtt_config_handler
from services.mqtt_service import mqtt_listener_loop

from routers import pages, api_auth, api_cameras, api_events, api_models


@asynccontextmanager
async def lifespan(app: FastAPI):

    await init_db()
    print("[System] Database initialized successfully.")

    asyncio.create_task(mqtt_listener_loop())
    print("[System] MQTT listener started successfully.")

    mqtt_task = asyncio.create_task(mqtt_config_handler())
    print("[System] MQTT config handler started successfully.")

    yield

    mqtt_task.cancel()
    print("[System] Cloud server shutting down. MQTT config handler stopped.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static_images", exist_ok=True)
app.mount("/media", StaticFiles(directory="static_images"), name="media")

# app.include_router(pages.router)
app.include_router(api_auth.router)
app.include_router(api_cameras.router)
app.include_router(api_models.router)
app.include_router(api_events.router)
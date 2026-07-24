import asyncio
import json
import uuid
import aiomqtt
from sqlalchemy import select

from database.database import AsyncSessionLocal, Camera, Event
from core.config import MQTT_BROKER, MQTT_PORT

async def mqtt_listener_loop():
    while True:
        try:
            print("Connecting to MQTT broker...")
            async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:
                await client.subscribe("ppe/events/#")
                print("Subscribed to topic: ppe/events, waiting for messages...")

                async for message in client.messages:
                    payload_str = message.payload.decode()
                    event_data = json.loads(payload_str)
                    print(f"New event received {event_data['event_type']} from camera {event_data['camera_id']}")

                    async with AsyncSessionLocal() as session:
                        cam_query = await session.execute(select(Camera).where(Camera.id == event_data["camera_id"]))
                        cam_db = cam_query.scalars().first()

                        if cam_db:
                            new_event = Event(
                                event_code=event_data.get("event_code", str(uuid.uuid4().hex)),
                                camera_id=event_data["camera_id"],
                                model_id=event_data["model_id"],
                                event_type=event_data["event_type"],
                                image_path=None,
                                video_path=None,
                                status='pending',
                                detections=event_data.get("detections"),
                                metadata_info=event_data
                            )
                            session.add(new_event)
                            await session.commit()
                            print(f"Saved event {new_event.event_type} for camera {cam_db.id} in database")
        except Exception as error:
            print(f"MQTT lost connection: {error}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
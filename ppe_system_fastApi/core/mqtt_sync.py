import asyncio
import json
import aiomqtt
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert

from database.database import AsyncSessionLocal, Camera, Event, AIModel


MQTT_HOSTNAME = "localhost"
MQTT_PORT = 1883
EDGE_ID = "edge_node_1"

TOPIC_SUBCRIBE_CONFIG = f"server/config/{EDGE_ID}"
TOPIC_PUBLISH_REQUEST = f"edge/{EDGE_ID}/sync_request"

async def process_sync_data(payload: dict):
    try:
        sync_type = payload.get("type")
        async with AsyncSessionLocal() as session:
            if sync_type == "sync_camera" or sync_type == "full_sync":
                cameras_data = payload.get("cameras", [])
                for cam_data in cameras_data:
                    Cam_id = cam_data.get("id")
                    existing_camera = await session.execute(select(Camera).where(Camera.id == Cam_id))
                    existing_camera = existing_camera.scalars().first()
                    if existing_camera:
                        # Update existing camera
                        existing_camera.name = cam_data.get("name", existing_camera.name)
                        existing_camera.source = cam_data.get("source", existing_camera.source)
                        existing_camera.location = cam_data.get("location", existing_camera.location)
                        existing_camera.status = cam_data.get("status", existing_camera.status)
                        existing_camera.current_model_id = cam_data.get("current_model_id", existing_camera.current_model_id)
                    else:
                        # Create new camera
                        new_camera = Camera(
                            id=cam_data.get("id"),
                            camera_id=cam_data.get("camera_id"),
                            name=cam_data.get("name"),
                            source=cam_data.get("source"),
                            location=cam_data.get("location"),
                            status=cam_data.get("status", "active")
                        )
                        session.add(new_camera)
            if sync_type == "sync_model" or sync_type == "full_sync":
                models_data = payload.get("models", [])
                for model_data in models_data:
                    model_id = model_data.get("id")
                    print(f"value of model_id: {model_id}, type: {type(model_id)}")
                    existing_model = await session.execute(select(AIModel).where(AIModel.id == model_id))
                    existing_model = existing_model.scalars().first()
                    if existing_model:
                        #Update existing model
                        existing_model.name = model_data.get("name", existing_model.name)
                        existing_model.type = model_data.get("type", existing_model.type)
                        existing_model.file_path = model_data.get("file_path", existing_model.file_path)
                        existing_model.task_type = model_data.get("task_type", existing_model.task_type)
                        existing_model.parameters = model_data.get("parameters", existing_model.parameters)
                        existing_model.is_active = model_data.get("is_active", existing_model.is_active)
                    else:
                        #Create new model
                        new_model = AIModel(
                            id=model_data.get("id"),
                            name=model_data.get("name"),
                            type=model_data.get("type"),
                            file_path=model_data.get("file_path"),
                            task_type=model_data.get("task_type"),
                            parameters=model_data.get("parameters", {}),
                            is_active=model_data.get("is_active", True)
                        )
                        session.add(new_model)
            await session.commit()
            print(f"saved sync data to database successfully for sync_type: {sync_type}")
    except Exception as e:
        print(f"Error processing sync data: {e}")


async def mqtt_config_listener():
    while True:
        try:
            async with aiomqtt.Client(hostname=MQTT_HOSTNAME, port=MQTT_PORT) as client:
                await client.subscribe(TOPIC_SUBCRIBE_CONFIG)
                print(f"Subscribed to topic: {TOPIC_SUBCRIBE_CONFIG}")
                
                async for message in client.messages:
                    payload_str = message.payload.decode()
                    payload = json.loads(payload_str)
                    print(f"Received sync data")
                    await process_sync_data(payload)

        except aiomqtt.MqttError as e:
            print(f"MQTT connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}")
            await asyncio.sleep(5)

async def periodic_sync_request():
    while True:
        try:
            async with aiomqtt.Client(hostname=MQTT_HOSTNAME, port=MQTT_PORT) as client:
                while True:
                    request_payload = {
                        "action": "request_full_sync",
                        "edge_id": EDGE_ID,
                        "timestamp": asyncio.get_event_loop().time()
                    }

                    await client.publish(
                        TOPIC_PUBLISH_REQUEST,
                        json.dumps(request_payload).encode(),
                    )
                    print(f"Published sync request to topic: {TOPIC_PUBLISH_REQUEST}")

                    await asyncio.sleep(30)

        except aiomqtt.MqttError as e:
            print(f"MQTT connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)






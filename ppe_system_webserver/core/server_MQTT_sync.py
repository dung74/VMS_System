import asyncio 
import json
import aiomqtt
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select

from database.database import AsyncSessionLocal, Camera, AIModel


MQTT_HOSTNAME = "localhost"
MQTT_PORT = 1883

TOPIC_LISTEN_EVENTS = "edge/edge_node_1/sync_request"

async def get_latest_config_from_db(edge_id: str) -> dict:
    # print(f"Fetching latest config for edge_id: {edge_id} from database...")
    async with AsyncSessionLocal() as db:

        result_cams = await db.execute(select(Camera).where(Camera.status == 'active'))
        cameras_db = result_cams.scalars().all()
        cam_list = []
        for cam in cameras_db:
            cam_list.append({
                "id": cam.id,
                # "camera_id": cam.camera_id,
                "name": cam.name,
                "source": cam.source,
                "location": cam.location,
                "status": cam.status,
                "current_model_id": cam.current_model_id
            })
        result_models = await db.execute(select(AIModel).where(AIModel.is_active == True))
        models_db = result_models.scalars().all()
        model_list = []
        for model in models_db:
            model_list.append({
                "id": model.id,
                "name": model.name,
                "type": model.type,
                "file_path": model.file_path,
                "task_type": model.task_type,
                "parameters": model.parameters,
                "is_active": model.is_active
            })

            # print(f"model_id: {model.id}, type: {type(model.id)}")  # Debugging line
        return {
            "type": "full_sync",
            "cameras": cam_list,
            "models": model_list
        }

async def mqtt_config_handler():

    # print(f"Starting MQTT config handler, listening to topic: {TOPIC_LISTEN_EVENTS}")
    while True:
        try:
            async with aiomqtt.Client(hostname=MQTT_HOSTNAME, port=MQTT_PORT) as client:
                await client.subscribe(TOPIC_LISTEN_EVENTS)
                async for message in client.messages:
                    try:
                        payload_str = message.payload.decode()
                        request_data = json.loads(payload_str)
                        if request_data.get("action") == "request_full_sync":
                            edge_id = request_data.get("edge_id")
                            # print(f"Received full sync request from edge_id: {edge_id}")
                            if edge_id:
                                latest_config = await get_latest_config_from_db(edge_id)
                                response_topic = f"server/config/{edge_id}"
                                await client.publish(response_topic, payload=json.dumps(latest_config))
                                # print(f"Published latest config to topic: {response_topic}")
                            else:
                                print("Edge ID not provided in the request.")
                        else:
                            print(f"Unknown action received: {request_data.get('action')}")
                    except json.JSONDecodeError:
                        print("Received invalid JSON payload.")
                    except Exception as e:
                        print(f"Error processing message: {e}")

        except aiomqtt.MqttError as error:
            print(f"MQTT connection error: {error}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Unexpected error in MQTT config handler: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


# if __name__ == "__main__":
#     asyncio.run(mqtt_config_handler())

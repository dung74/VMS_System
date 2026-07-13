import json

import cv2
import av
from aiortc import VideoStreamTrack
from sqlalchemy import select
from ultralytics import YOLO
from core.read_frame import FrameReader
from core.ai_thread import ModelPredictor
from core.frame_buffer import FrameBuffer
from database.database import AsyncSessionLocal, Camera, AIModel, Event
import time
import asyncio
import aiomqtt
import numpy as np

from core.model_factory import ModelFactory
import requests
import uuid
from datetime import datetime, timezone, timedelta

import httpx

VN_TZ = timezone(timedelta(hours=7))  # Vietnam timezone (UTC+7)

MQTT_BROKER_URL = "localhost"
MQTT_PORT = 1883

            # payload = {
            #             "edge_id": 'edge_001',
            #             "camera_id":self.camera_id,
            #             # take the model id 
            #             "model_id": model_id,
            #             "detections": detections,
            #             "timestamp": time.time()
            #         }

EDGE_URL = "http://localhost:8000"  # Replace with your actual edge URL
TIME_RESET_TRACKS = 6


class Camera_thread(VideoStreamTrack):
    def __init__(self,camera_id, source, input_buffer=None, output_buffer=None):
        super().__init__()
        self.camera_id = camera_id
        # self.model = YOLO(model_path)
        self.frame_reader = FrameReader(source)
        self.frame_count_fps = 0
        self.start_time = time.time()
        self.current_fps = 0.0

        self.input_buffer = input_buffer if input_buffer is not None else FrameBuffer(max_size=1)
        self.output_buffer = output_buffer if output_buffer is not None else FrameBuffer(max_size=1)

        self._ai_thread_task = False
        self.ai_predictor = ModelPredictor(camera_id=self.camera_id)
        # self.readyState = "live"
        self.is_running = True
        self.last_saved_tracks = {} 
        self.gap_time = 2
        self.backgroud_task = set()


    def StopCameraStream(self):
        self.is_running = False
        self.frame_reader.release()
        print(f"Camera stream {self.camera_id} stopped.")


    async def get_models_of_camera(self, camera_id):
        list_models_info = []
        #select * from all_info model where model_id == all camera current_model_id
        async with AsyncSessionLocal() as session:
            camera = await session.scalar(select(Camera).where(Camera.id == camera_id))
            if camera:
                model_ids = camera.current_model_id
                if not isinstance(model_ids, list):
                    model_ids = [model_ids]
                result = await session.execute(select(AIModel).where(AIModel.id.in_(model_ids)))
                for model in result.scalars().all():
                    list_models_info.append(model)
        return list_models_info
            


    def load_models_for_camera(self, list_model_info): 
        model_instances = {}
        for model_info in list_model_info:
            model_type = model_info.type
            parameters = model_info.parameters or ModelFactory._get_model_parameters(model_type)
            model_instance = ModelFactory.create_model_instance(model_type, parameters)
            model_instances[model_info.id] = model_instance
        return model_instances

    def draw_detections_on_frame(self, frame, all_detections):
        for detections in all_detections:
            for det in detections:
                track_id = det.get("track_id", "Unknown")
                class_name = det.get("class_name", "Unknown")
                confidence = det.get("confidence", 0.0)
                bbox = det.get("bbox", (0, 0, 0, 0))
                x1, y1, x2, y2 = bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{class_name} : {confidence:.2f} (ID: {track_id})", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame
    def check_if_event_should_be_saved(self, payload):

        time_event = payload.get("timestamp", time.time())
        detections = payload.get("detections", [])
        if not detections:
            return False
        
        should_save = False

        self.last_saved_tracks = {
            tr_id: ts for tr_id, ts in self.last_saved_tracks.items()
            if (time_event - ts) < (self.gap_time * 4) 
        }

        for det in detections:
            track_id = det.get("track_id")
            if track_id is None:
                continue
            last_time = self.last_saved_tracks.get(track_id, 0)
            if  (time_event - last_time) >= self.gap_time and track_id not in self.last_saved_tracks:
                should_save = True
                self.last_saved_tracks[track_id] = time_event
        
        return should_save
    

    


    async def save_event_to_db(self, payload):
    
        event_type = payload.get("event_type", "object_detected")
 
        try:
            async with AsyncSessionLocal() as session:
                new_event = Event(
                    event_code=payload.get("event_code", str(uuid.uuid4().hex)),
                    camera_id=self.camera_id,
                    model_id=payload.get("model_id"),  # You can set this if you have a specific model ID
                    event_type=event_type,
                    image_path=None,  # Set this if you save images
                    video_path=None,  # Set this if you save videos
                    status='pending',
                    detections=payload.get("detections"),
                    metadata_info=payload
                )
                session.add(new_event)
                await session.commit()
                print(f"Event saved to database for camera {self.camera_id}")
        except Exception as e:
            print(f"Error saving event to database for camera {self.camera_id}: {e}")


    async def handle_event(self, edge_url: str, payload: dict, frame_result):

        upload_url = f"{edge_url}/api/cloud/upload_image"

        success, encoded_image = cv2.imencode('.jpg', frame_result)
        if not success:
            print(f"Failed to encode image for camera {self.camera_id}")
            return
        image_bytes = encoded_image.tobytes()
        event_code = payload.get("event_code", str(uuid.uuid4().hex))
        
        form_data = {
            "camera_id": str(self.camera_id),
            "event_type": payload.get("event_type", "object_detected"),
            "event_code": event_code,
            "event_datetime": str(payload.get("event_datetime", datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S"))),
        }

        files = {
            "file": (f"{event_code}.jpg", image_bytes, "image/jpeg")
        }


        try:
            async with httpx.AsyncClient() as client:
                print(f"Uploading image for camera {self.camera_id}, event {event_code} to {upload_url}")
                response = await client.post(upload_url, data=form_data, files=files, timeout=10)
                if response.status_code == 422:
                    print(f"Error 422: {response.text}")

                response.raise_for_status()
                
                print(f"Image uploaded successfully for camera {self.camera_id}, event {event_code}")
        except httpx.HTTPError as e:
            print(f"Failed to upload image for camera {self.camera_id}, event {event_code}: {e}")

        
        
        



    async def _ai_worker_loop(self):
        print("AI worker loop started")
        

        dict_models_instances = {}
        try:
            list_models_of_camera = await self.get_models_of_camera(camera_id=self.camera_id)
            print(f"list_models_of_camera for camera {self.camera_id}: {list_models_of_camera}")
            dict_models_instances = self.load_models_for_camera(list_models_of_camera)
        except Exception as e:
            print(f"Error loading model instances for camera {self.camera_id}: {e}")


        try:
            async with aiomqtt.Client(hostname=MQTT_BROKER_URL, port=MQTT_PORT) as client:

                while self.is_running:
                    
                    try:
                        if not self.input_buffer.is_empty():
                            frame = self.input_buffer.get_frame()
                            self.input_buffer.clear_buffer()
                            if frame is not None :
                                all_detections, all_payload = await asyncio.to_thread(self.ai_predictor.predict_frame, frame, dict_models_instances)
                                topic = f"ppe/events/{self.camera_id}"
                                result_frame = self.draw_detections_on_frame(frame.copy(), all_detections)
                                if result_frame is not None:
                                    self.output_buffer.clear_buffer()
                                    self.output_buffer.add_frame(result_frame)
                                if len(all_detections) > 0:

                                    for payload in all_payload:
                                        if self.check_if_event_should_be_saved(payload):
                                            event_code = str(uuid.uuid4().hex)
                                            payload["event_code"] = event_code

                                            # asyncio.create_task(self.save_event_to_db(payload))

                                            await client.publish(topic, payload=json.dumps(payload))
                                            # self.handle_event(edge_url=EDGE_URL, payload=payload, frame_result=result_frame)
                                            task = asyncio.create_task(
                                                
                                                    self.handle_event(
                                                        edge_url=EDGE_URL,
                                                        payload=payload,
                                                        frame_result=result_frame
                                                        )
                                                )
                                            self.backgroud_task.add(task)
                                            task.add_done_callback(self.backgroud_task.discard)


                                    # print(f"Published event {event_type_str}")
                    except Exception as e:
                        print(f"Error in AI worker loop: {e}")


                    await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error in AI worker loop: {e}")
        # print("AI worker loop stopped")
    async def stop(self):
        self.is_running = False

    async def recv(self):
        if not self._ai_thread_task:
            asyncio.create_task(self._ai_worker_loop())
            self._ai_thread_task = True
        
        pts, time_base = await self.next_timestamp()
        frame = await asyncio.to_thread(self.frame_reader.read_frame)
        if frame is None:
            black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            new_frame = av.VideoFrame.from_ndarray(black_frame, format='bgr24')
            new_frame.pts = pts
            new_frame.time_base = time_base
            return new_frame
        
        self.input_buffer.clear_buffer()
        self.input_buffer.add_frame( frame)

        time_counter = 0
        while self.output_buffer.is_empty() and time_counter < 100:
            await asyncio.sleep(0.01)
            time_counter +=1

        if not self.output_buffer.is_empty():
            result_frame = self.output_buffer.get_frame()
            self.output_buffer.clear_buffer()
        else:
            result_frame = frame


        self.frame_count_fps += 1
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        if elapsed_time >= 1.0:
            self.current_fps = self.frame_count_fps / elapsed_time
            print(f"FPS: {self.current_fps:.2f} of {self.camera_id}")
            self.frame_count_fps = 0
            self.start_time = time.time()
        cv2.putText(result_frame, f'FPS: {self.current_fps:.2f}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)


        
        new_frame = av.VideoFrame.from_ndarray(result_frame, format='bgr24')
        new_frame.pts = pts
        new_frame.time_base = time_base
        

        return new_frame
    





       
        



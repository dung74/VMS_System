import asyncio
import time
from datetime import datetime, timezone, timedelta

from requests import session
from ultralytics import YOLO
import cv2
from database.database import AsyncSessionLocal, Camera, AIModel, Event
import json
from core.model_factory import ModelFactory
# from ppe_system_fastApi.core.Camera_thread import VN_TZ

VN_TZ = timezone(timedelta(hours=7))  # Vietnam timezone (UTC+7)



class ModelPredictor:
    def __init__(self, camera_id):
        self.camera_id = camera_id



    def predict_frame(self, frame_reader, dict_model_instances):

        frame = frame_reader

        if frame is None:
            return [], []
        
        all_detections = []
        all_payload = []
        self.dict_models_instance_of_camera = dict_model_instances

        
        for model_id, model in self.dict_models_instance_of_camera.items():
            detections = model.predict_frame(frame)
            if not detections:
                continue
            all_detections.append(detections)
            # for detection in detections:
            #     track_id = detection["track_id"]
            #     class_name = detection["class_name"]
            #     confidence = detection["confidence"]
            #     bbox = detection["bbox"]
            #     x1, y1, x2, y2 = bbox
            #     cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            #     cv2.putText(frame, f"{class_name} : {confidence:.2f} (ID: {track_id})", (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
          

            # send mqtt message with detections
            time
            payload = {
                        "edge_id": 'edge_001',
                        "camera_id":self.camera_id,
                        # take the model id 
                        "model_id": model_id,
                        "event_type": "object_detected",
                        "detections": detections,
                        "timestamp": time.time(),
                        "datetime": datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    }
            all_payload.append(payload)

            
                                        

        return all_detections, all_payload



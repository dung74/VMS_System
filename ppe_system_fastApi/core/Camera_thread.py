import cv2
import av
from aiortc import VideoStreamTrack
from ultralytics import YOLO
from core.read_frame import FrameReader
from core.ai_thread import ModelPredictor
from core.frame_buffer import FrameBuffer
import time
import asyncio
import aiomqtt

MQTT_BROKER_URL = "localhost"
MQTT_PORT = 1883


class Camera_thread(VideoStreamTrack):
    def __init__(self,camera_id, model_path, source, input_buffer=None, output_buffer=None):
        super().__init__()
        self.camera_id = camera_id
        self.model = YOLO(model_path)
        self.frame_reader = FrameReader(source)
        self.frame_count_fps = 0
        self.start_time = time.time()
        self.current_fps = 0.0

        self.input_buffer = input_buffer if input_buffer is not None else FrameBuffer(max_size=1)
        self.output_buffer = output_buffer if output_buffer is not None else FrameBuffer(max_size=1)

        self._ai_thread_task = False
        self.ai_predictor = ModelPredictor(self.model)
        # self.readyState = "live"
        self.is_running = True




    async def _ai_worker_loop(self):
        print("AI worker loop started")

        try:
            async with aiomqtt.Client(hostname=MQTT_BROKER_URL, port=MQTT_PORT) as client:
                while self.is_running:
                    try:
                        if not self.input_buffer.is_empty():
                            frame = self.input_buffer.get_frame()
                            self.input_buffer.clear_buffer()
                            if frame is not None :
                                result_frame, detections = await asyncio.to_thread(self.ai_predictor.predict_frame, frame)

                                if result_frame is not None:
                                    self.output_buffer.clear_buffer()
                                    self.output_buffer.add_frame(result_frame)
                                
                                for det in detections:
                                    if det["class_id"] in[ self.ai_predictor.CLASS_PERSON, self.ai_predictor.CLASS_CARD]:
                                        event_type_str = "person_detected" if det["class_id"] == self.ai_predictor.CLASS_PERSON else "card_detected"
                                        payload = {
                                            "edge_id": "edge_001",
                                            "camera_id": self.camera_id,
                                            "event_type": event_type_str,
                                            "timestamp": asyncio.get_event_loop().time()
                                        }
                                        topic = f"ppe/events/{self.camera_id}"
                                        await client.publish(topic, payload=str(payload))
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
            black_frame = cv2.Mat.zeros((480, 640, 3), dtype=cv2.CV_8UC3)
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
    





       
        



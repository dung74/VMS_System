#class predictor for cell phone detection

import cv2
from ultralytics import YOLO
from ai_models.base_model import BaseModel

class CellPhonePredictor(BaseModel):
    def __init__(self, model_path):
        super().__init__(model_name="CellPhoneModel", confidence_threshold=0.5, model_path=model_path)
        self.model = YOLO(self.model_path)
        self.CLASS_CELL_PHONE = 67

    def predict_frame(self, frame_reader):
            frame = frame_reader

            if frame is None:
                return None
            results = self.model.predict(
                frame,
                conf=0.5,
                iou=0.5,
                classes=[self.CLASS_CELL_PHONE],
                verbose=False,
            )

            detections = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    detections.append({
                        "class_name": "cell_phone",
                        "confidence": conf,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)]
                    })
            return detections
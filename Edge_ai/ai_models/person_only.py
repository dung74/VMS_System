#class predictor for cell phone detection

import cv2
from ultralytics import YOLO
from ai_models.base_model import BaseModel

class PersonOnlyPredictor(BaseModel):
    def __init__(self, model_path, confidence_threshold=0.5):
        super().__init__(model_name="PersonOnlyModel", confidence_threshold=confidence_threshold, model_path=model_path)
        self.model = YOLO(self.model_path)
        self.CLASS_PERSON = 0
        # self.confidence_threshold = confidence_threshold

    def predict_frame(self, frame_reader):
            frame = frame_reader

            if frame is None:
                return None
            results = self.model.track(
                frame,
                conf=self.confidence_threshold,
                iou=0.5,
                classes=[self.CLASS_PERSON],
                tracker="bytetrack.yaml",
                persist=True,
                verbose=False,
                device='cpu'
            )

            detections = []
            for r in results:
                for box in r.boxes:
                    # cls_id = int(box.cls[0])

                    if box.id is not None:
                        trk_id = int(box.id[0])
                    else:
                         trk_id = None
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    detections.append({
                        "track_id": trk_id,
                        "class_name": "person",
                        "confidence": conf,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)]
                    })
            return detections
from ultralytics import YOLO
import cv2
from ai_models.base_model import BaseModel


COLOR_PERSON = (0, 255, 0)
COLOR_CARD = (0, 0, 255)
CLASS_MAP = {
    2: "person",
    3: "card"
}

class PersonCardPredictor(BaseModel):
    def __init__(self, confidence_threshold=0.5, model_path=None, class_person=2, class_card=3):
        super().__init__(model_name="PersonCardModel", confidence_threshold=0.5, model_path=model_path)

        self.model = YOLO(model_path)
        self.CLASS_PERSON = class_person
        self.CLASS_CARD = class_card



    
    # def draw_bounding_boxes(self, frame, results):
    #     detections = []
    #     for r in results:
    #         for box in r.boxes:

    #             cls_id = int(box.cls[0])
    #             conf = float(box.conf[0])
    #             x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
    #             if cls_id == self.CLASS_PERSON:
                    
    #                 cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), COLOR_PERSON, 2)
    #                 cv2.putText(frame, f'Person {conf:.2f}', (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_PERSON, 2)
    #             elif cls_id == self.CLASS_CARD:
    #                 cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), COLOR_CARD, 2)
    #                 cv2.putText(frame, f'Card {conf:.2f}', (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_CARD, 2)
        
    #             detections.append({
    #                 "class_id": cls_id,
    #                 "confidence": conf,
    #                 "bbox": [int(x1), int(y1), int(x2), int(y2)]
    #             })
    #     return frame, detections
    

    def predict_frame(self, frame_reader):

        frame = frame_reader
        

        if frame is None:
            return None
        results = self.model.track(
            frame,
            conf=0.5,
            iou=0.5,
            classes = [self.CLASS_PERSON, self.CLASS_CARD],
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False,
            device='cpu'
        )

        # result_frame, detections = self.draw_bounding_boxes(frame, results)
        detections = []
        for r in results:
            for box in r.boxes:
                if box.id is not None:
                    trk_id = int(box.id[0])
                else:
                    trk_id = None
                cls_name = CLASS_MAP.get(int(box.cls[0]), "unknown")
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                detections.append({
                    "track_id": trk_id,
                    "class_name": cls_name,
                    "confidence": conf,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)]
                })
        

        return detections



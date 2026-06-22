import os
import threading
import cv2
import time
from ultralytics import YOLO
from django.conf import settings
from django.utils import timezone
from datetime import datetime

GLOBAL_IS_DETECTING = True
GLOBAL_FRAME_BYTES = None
GLOBAL_IS_RECORDING = True

class AIEdgeScanner:
    def __init__(self, model_path = '../models/best(33).pt', source = 0):
        self.model = YOLO(model_path)
        self.camera = cv2.VideoCapture(source)

        self.CLASS_PERSON = 2
        self.CLASS_CARD = 3


        self.last_albert_time = 0
        self.albert_cooldown = 4

        self.frame_counter = 0
        self.process_every_n_frames = 5

        self.last_persons = []
        self.last_cards = []

    def __del__(self):
         if self.camera.isOpened():
              self.camera.release()

    def extract_bounding_boxes(self, results):

            persons, cards = [], []

            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])

                    
                    if cls_id == self.CLASS_PERSON:
                        persons.append(box.xyxy[0].cpu().numpy())
                    elif cls_id == self.CLASS_CARD:
                        cards.append(box.xyxy[0].cpu().numpy())

            return persons, cards
        
    def check_card_association(self, person_box, card_boxes):
            px1, py1, px2, py2 = person_box
            for c_box in card_boxes:
                cx1, cy1, cx2, cy2 = c_box
                center_x = (cx1 + cx2) /2
                center_y = (cy1 + cy2) /2

                if px1 <= center_x <= px2 and py1 <= center_y <= py2:
                    return True
            return False
        
    def handle_violation_trigger(self, frame, person_box):
        current_time = timezone.now().timestamp()
        if current_time - self.last_albert_time >= self.albert_cooldown:
            self.last_albert_time = current_time

            now = timezone.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H-%M-%S')

            relative_folder_path = os.path.join('violations', date_str)
            absolute_folder_path = os.path.join(settings.MEDIA_ROOT, relative_folder_path)

            os.makedirs(absolute_folder_path, exist_ok = True)

            px1, py1, px2, py2 = [int(v) for v in person_box]
            height, width, _ = frame.shape
            px1, py1 = max(0, px1), max(0, py1)
            px2, py2 = min(width-1, px2), min(height-1, py2)

            cropped_person_img = frame[py1:py2, px1:px2]

            filename = f"no_card_{time_str}_{int(current_time)}.jpg"

            absolute_image_path = os.path.join(absolute_folder_path, filename)
            relative_image_path = os.path.join(relative_folder_path, filename)

            if cropped_person_img.size >0:
                cv2.imwrite(absolute_image_path, cropped_person_img)
            from detector.models import ViolationLog
            ViolationLog.objects.create(
                violation_type = "NO_CARD",
                image_path = relative_image_path
            )
            print(f"==> He thong da luu mot ban ghi vi pham vao database")
            print(f"==> Anh vi pham duoc luu tai: {absolute_image_path}")


    def run_background_loop(self):
            
            global GLOBAL_IS_DETECTING, GLOBAL_FRAME_BYTES, GLOBAL_IS_RECORDING
            video_out = None
            video_start_time = None
            current_video_db_path = None

            while True:

                success, frame = self.camera.read()
                if not success:
                    time.sleep(0.1)
                    continue
                if GLOBAL_IS_DETECTING:
                    self.frame_counter +=1
                    if self.frame_counter % self.process_every_n_frames == 0:
                        
                        
                    
                        results = self.model.predict(
                            frame, 
                            conf = 0.3,
                            classes = [self.CLASS_PERSON, self.CLASS_CARD],
                            imgsz = 480,

                            verbose = False,
                            device = 'cpu',
                            )

                        persons, cards = self.extract_bounding_boxes(results)

                        self.last_persons = persons
                        self.last_cards = cards

                    for c_box in self.last_cards:
                            
                            cx1, cy1, cx2, cy2 = c_box
                            cv2.rectangle(frame, (int(cx1), int(cy1)),(int(cx2), int(cy2)), (0, 165, 255), 2 )
                            cv2.putText(frame, "Card", (int(cx1), int(cy1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
                    for p_box in self.last_persons:
                            px1, py1, px2, py2 = p_box
                            is_valid = self.check_card_association(p_box, self.last_cards)

                            color = (0, 255, 0) if is_valid else (0, 0, 255)
                            label = "hop le" if is_valid else "vi pham"

                            cv2.rectangle(frame, (int(px1), int(py1)), (int(px2), int(py2)), color, 2)
                            cv2.putText(frame, label, (int(px1), int(py1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                            if not is_valid:
                                self.handle_violation_trigger(frame, p_box)
                else:
                    cv2.putText(frame, "AI DETECTION OFF (LIVE VIEW ONLY)",(20, 40), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2 )
                
                now = datetime.now()
                height, width = frame.shape[ :2]
                if GLOBAL_IS_RECORDING:
                    if now.second % 2 == 0:
                        cv2.circle(frame, (width - 30, 30), 10, (0, 0, 255), -1)
                    if video_out is None or (now-video_start_time).seconds > 60:
                        if video_out is not None:
                            video_out.release()
                            from detector.models import VideoRecord
                            VideoRecord.objects.create(timestamp=video_start_time, video_path = current_video_db_path)
                            print(f"==> Da luu doan video mot phut : {current_video_db_path}")

                        video_start_time = now
                        date_str = now.strftime('%Y-%m-%d')
                        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos', date_str)
                        os.makedirs(folder_path, exist_ok = True)

                        filename = now.strftime('%H-%M-%S') + '.webm'
                        full_path = os.path.join(folder_path, filename)
                        current_video_db_path = f"videos/{date_str}/{filename}"

                        fourcc = cv2.VideoWriter_fourcc(*'VP80')
                        video_out = cv2.VideoWriter(full_path, fourcc, 20.0, (width, height))

                    if video_out is not None:
                        video_out.write(frame)
                else:
                    if video_out is not None:
                        video_out.release()
                        from detector.models import VideoRecord
                        VideoRecord.objects.create(timestamp=video_start_time, video_path = current_video_db_path)
                        video_out = None
                        print(f"==> Da tat ghi hinh va luu video hien tai")
                    cv2.putText(frame, "RECORDING: STOPPED", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

                        


                _, jpeg = cv2.imencode('.jpg', frame)
                GLOBAL_FRAME_BYTES = jpeg.tobytes()

                time.sleep(0.02)

# print("Kich hoat luong giam sat AI")
# scanner_instance = AIEdgeScanner(model_path = '/home/dunghoangviet/Dungx/Dungx/ppe_system/models/best(33).pt')
# ai_thread = threading.Thread(target = scanner_instance.run_background_loop, daemon = True)
# ai_thread.start()
            

              

            








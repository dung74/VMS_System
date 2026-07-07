import os

from ultralytics import YOLO
import cv2


CLASS_NAMES = [
    "bus",
    "car",
    "motorcycle",
    "truck",
    
]


def predict_frame(model, frame):
    if frame is None:
        return None
    results = model.predict(
        frame, 
        conf=0.3,
        iou=0.3,
        verbose=False,
        device='cpu'

    )
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(frame, f'Class {CLASS_NAMES[cls_id]} {conf:.2f}', (int(x1), int(y2) - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
    return frame

def process_image(model_path, image_path):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at path: {model_path}")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at path: {image_path}")

    model = YOLO(model_path)
    frame = cv2.imread(image_path)
    result_frame = predict_frame(model, frame)
    cv2.namedWindow("Result", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Result", 800, 600)
    cv2.imshow("Result", result_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def process_video(model_path, video_path):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at path: {model_path}")
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at path: {video_path}")
    model = YOLO(model_path)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        result_frame = predict_frame(model, frame)
        #show with window size 800x600
        cv2.namedWindow("Result", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Result", 800, 600)
        cv2.imshow("Result", result_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif cv2.waitKey(int(1000/fps)) & 0xFF == ord('d'):
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + (int(fps) * 10))
            
        
        
    cap.release()
    cv2.destroyAllWindows()

model_path = "/home/dunghoangviet/Projects/pathtech/vehicle_gate/models/best_vehicle_v7.pt"  # Update with your model path

print("Choice an option:")
print("1. Process an image")
print("2. Process a video")
choice = input("Enter your choice (1 or 2): ")
if choice == '1':
    # image_path = "/home/dunghoangviet/Projects/pathtech/vehicle_gate/data_vehicle/to_06_30/cong_chinh_nhadhsx/"
    image_path = "/home/dunghoangviet/Downloads/2026-07-01/"  
    # image_path = "/home/dunghoangviet/Downloads/2026-06-30/cong chinh/"
    file_name = input("Enter the file name for the image: ")

    image_show = image_path + file_name
    print(f"Processing image: {image_show}")

    process_image(model_path, image_show)
elif choice == '2':
    video_path = input("Enter the path to the video: ")
    process_video(model_path, video_path)
else:
    print("Invalid choice. Please enter 1 or 2.")


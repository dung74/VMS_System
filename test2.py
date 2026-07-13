from ultralytics import YOLO

# Nếu chưa có file yolov8m.pt, Ultralytics sẽ tự động tải về
model = YOLO("yolo11n.pt")

print("Download hoàn tất!")
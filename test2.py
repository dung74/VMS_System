from ultralytics import YOLO

# Nếu chưa có file yolov8m.pt, Ultralytics sẽ tự động tải về
model = YOLO("yolov8n.pt")

print("Download hoàn tất!")
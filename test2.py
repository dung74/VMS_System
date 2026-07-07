import os
import shutil
import uuid
import uuid
from roboflow import Roboflow

# 1. Khai báo thông tin xác thực
API_KEY = "tSfJySaBYA1OpadSfDCs"
WORKSPACE_NAME = "dngs-workspace-nmwpa"
PROJECT_NAME = "fire_smoke_caongan-jvb32"

# 2. Khởi tạo kết nối với Roboflow
rf = Roboflow(api_key=API_KEY)
project = rf.workspace(WORKSPACE_NAME).project(PROJECT_NAME)

# 3. Đường dẫn tới thư mục chứa ảnh của bạn
# (Giả sử thư mục data_for_caongan nằm cùng chỗ với file code này)
folder_path = "/home/dunghoangviet/Projects/pathtech/fire_smoke/data_for_caongan"

temp_folder = "/home/dunghoangviet/Projects/pathtech/fire_smoke/temp"

os.makedirs(temp_folder, exist_ok=True)

success_count = 0
print(f"Bắt đầu xử lý đổi tên và upload từ thư mục: {folder_path}...")
# take image from all subfolders and folder

for root, dirs, files in os.walk(folder_path):
    for filename in files:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            old_image_path = os.path.join(root, filename)

            # Tạo tên file mới, ví dụ: 8a4b2c1d_anh1.jpg
        unique_id = uuid.uuid4().hex[:8]
        new_filename = f"{unique_id}_{filename}"
        new_image_path = os.path.join(temp_folder, new_filename)
        
        try:
            # Copy ảnh gốc sang file tạm với tên mới
            shutil.copy2(old_image_path, new_image_path)
            
            print(f"Đang tải lên: {new_filename}...")
            
            # Upload file đã đổi tên
            project.upload(new_image_path)
            success_count += 1
            
            # Xóa file tạm sau khi upload thành công để dọn dẹp
            os.remove(new_image_path)
            
        except Exception as e:
            print(f"Lỗi khi tải {new_filename}: {e}")

# Xóa thư mục tạm sau khi hoàn tất vòng lặp
try:
    os.rmdir(temp_folder)
except OSError:
    pass

print(f"\nHoàn tất! Đã đổi tên và tải lên thành công {success_count} ảnh.")
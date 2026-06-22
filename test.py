import os

from ultralytics import YOLO
import cv2


list_of_models = [
    'smoke_fire_v3.pt',
    'yolo11m.pt',
    'petrolimex_v3b.pt'
]

list_of_input_folders = [
    'Bang_tai_C-1_b1c6b4f6',
    'Bo_dieu_tiet_da_voi_259f1069',
    'C-2_Tram_T1_2aecdb51', 

    'C-5_Tram_T2_3121440d',

    'Cao_da_e0559b62',

    'Cong_Chinh_Nha_May_4480e98c',


    'Cong_chinh_nha_DHSX_359e1c2b',

    'Dau_C-2_37a26d1c',

    'Dau_vao_T-4_3982ebde',

    'Dinh_C-3_5877e4c6',

    'Kho_than_b99a0047',

    'Loi_vao_toa_nha_83663379',

    'May_cap_868af8ce',


    'May_nghien_a514605f',

    'Nha_dau_bbe34159',
    'Tang_am_B_785a253b',

    'Tram_T-3_bceebac8',

    'Van_3.4_C-3_43aead0a'
]
list_of_input_folders = [
    'khothan'
]



# 1. Load mô hình với file trọng số vừa tải về
# model_name = 'smoke_fire_v3.pt'  # Tên file trọng số của mô hình bạn muốn sử dụng
# # Nếu file best.pt nằm ở thư mục khác, bạn trỏ lại đường dẫn cho đúng
# input_folder_name ='Cao_da_e0559b62'
for model_name in list_of_models:
    for input_folder_name in list_of_input_folders:
        # model = YOLO('/home/dunghoangviet/Downloads/model_weights_copy/petrolimex_v3b.pt')
        # model = YOLO('/home/dunghoangviet/Downloads/model_weights_copy/yolo11m.pt')
        model = YOLO(f'/home/dunghoangviet/Downloads/model_weights_copy/{model_name}')

        output_folder = f'/home/dunghoangviet/Dungx/Dungx/ppe_system/outputtest/{input_folder_name}_{model_name.split(".")[0]}'
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        # output_folder = '/home/dunghoangviet/Projects/pathtech/fire_smoke/data_test/images/images_output'
        # if not os.path.exists(output_folder):
        #     os.makedirs(output_folder)
        # 2. Đường dẫn tới bức ảnh bạn muốn test

        # image_folder = f'/home/dunghoangviet/Downloads/camera-capture/{input_folder_name}/2026-06-17/'
        image_folder = f'/home/dunghoangviet/Downloads/{input_folder_name}/'
        # image_path = f'/home/dunghoangviet/Projects/pathtech/dataset_caongan_use/Kho_than_b99a0047/2026-06-17/16-44-52.jpg'

        # 3. Chạy dự đoán (inference)
        # conf=0.4: Chỉ lấy các dự đoán có độ tin cậy từ 40% trở lên (bạn có thể tùy chỉnh)
        images = [f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.jpeg', '.png'))][:100]  # Test với 30 ảnh đầu tiên trong thư mục
        for image_file in images:
            image_path = os.path.join(image_folder, image_file)
            results = model.predict(source=image_path, conf=0.5)

            # 4. Trích xuất và in kết quả ra terminal để kiểm tra
            print("\n--- KẾT QUẢ NHẬN DIỆN ---")
            for r in results:
                # Lấy danh sách các class được mô hình phát hiện
                detected_classes = r.boxes.cls.tolist()
                
                if len(detected_classes) == 0:
                    print("Không phát hiện thấy fire hay smoke trong ảnh này.")
                else:
                    for cls_id in detected_classes:
                        class_name = model.names[int(cls_id)]
                        print(f"- Đã phát hiện: {class_name}")

            # 5. Trích xuất ảnh đã được vẽ bounding box và lưu lại
            # plot() sẽ tự động vẽ nhãn "fire" hoặc "smoke" kèm box lên ảnh
            annotated_image = results[0].plot()
            
            # Lưu ảnh ra máy
            output_filename = f'ket_qua_test_{image_file}'
            cv2.imwrite(os.path.join(output_folder, output_filename), annotated_image)
            print(f"\nĐã lưu ảnh kết quả thành công vào file: {output_filename}")
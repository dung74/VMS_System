-- Chèn dữ liệu cho bảng ai_models
INSERT INTO ai_models (id, name, type, file_path, task_type, is_active, created_at, updated_at, parameters) VALUES
(2, 'model2', 'person_card', 'models/best(33).pt', 'detection', true, '2026-06-09 03:53:51.814901+07', '2026-06-09 03:53:51.814905+07', '{"class_card": 3, "model_path": "models/best(33).pt", "class_person": 2, "confidence_threshold": 0.5}'),
(3, 'yolo1', 'person_card', 'models/best(33).pt', 'detection', true, '2026-06-17 14:10:27.614952+07', '2026-06-17 14:10:27.614955+07', '{"class_card": 3, "model_path": "models/best(33).pt", "class_person": 2, "confidence_threshold": 0.5}'),
(6, 'dien thoai', 'cell_phone', 'models/yolov8m.pt', 'detection', true, '2026-07-08 02:54:21.343256+07', '2026-07-08 02:54:21.34326+07', '{}'),
(7, 'dien thoai (v8n)', 'cell_phone', 'models/yolov8n.pt', 'detection', true, '2026-07-08 08:14:35.348977+07', '2026-07-08 08:14:35.348981+07', '{}'),
(1, 'person', 'person_card', 'models/best(33).pt', 'detection', true, '2026-06-09 03:51:20.998639+07', '2026-07-10 08:23:17.797704+07', '{"class_card": 3, "model_path": "models/best(33).pt", "class_person": 2, "confidence_threshold": 0.5}'),
(10, 'person_only(v11n)', 'person_only', 'models/yolo11n.pt', 'detection', true, '2026-07-12 06:15:02.963469+07', '2026-07-12 06:17:11.444912+07', '{}');

-- Reset lại sequence của ai_models để khi thêm model mới không bị lỗi trùng ID
SELECT setval(pg_get_serial_sequence('ai_models', 'id'), (SELECT MAX(id) FROM ai_models));


-- Chèn dữ liệu cho bảng cameras
-- Lưu ý: Cột current_model_id đang hiển thị dạng mảng/JSON, nên được truyền vào dưới dạng string '[]' để Postgres tự ép kiểu.
INSERT INTO cameras (id, name, source, location, status, current_model_id, created_at, updated_at) VALUES
(3, 'iphone', '4', 'b', 'active', '[2]', '2026-06-09 03:56:31.792868+07', '2026-06-09 03:56:31.792872+07'),
(16, 'ip_two model', '4', '', 'active', '[2, 7]', '2026-07-09 08:33:59.156411+07', '2026-07-09 08:33:59.156415+07'),
(15, 'cam_lap', '0', 'homee', 'active', '[1, 7]', '2026-07-09 08:32:33.41211+07', '2026-07-10 08:27:08.840932+07'),
(19, 'rtsp', 'rtsp://127.0.0.1:8554/stream_people', 'factory', 'active', '[10, 7]', '2026-07-12 04:05:50.486462+07', '2026-07-12 06:15:13.426417+07');

-- Reset lại sequence của cameras
SELECT setval(pg_get_serial_sequence('cameras', 'id'), (SELECT MAX(id) FROM cameras));

INSERT INTO users (id, username, email, hashed_password, role) VALUES
(1, 'user1', 'user1@gm.com', '$2b$12$cHux99ttLmkFpnLCmQ/LzuaijELA.K9zAcV.6u2nlgp4LagFGxxU.', 'user'),
(2, 'admin1', 'admin@email.com', '$2b$12$crYNx5UCkFvtHFmiVFr8X.zeCwKWaJyYms4bgZ9Qv7Bj2pcsoDufK', 'admin'),
(3, 'user2', 'user2@gmail.com', '$2b$12$Wnf6LaTeoSSsU/wcGTEvBegcRffo0ZymwmGImHF2qJd3yinNpthUS', 'user');

-- Reset lại sequence của users để đảm bảo ID tự tăng không bị lỗi khi tạo user mới
SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users));
from django.apps import AppConfig
import os
import threading

class DetectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'detector'

    def ready(self):

        if os.environ.get('RUN_MAIN', None) == 'true' or os.environ.get('RUN_MAIN') == True:
            pass

        if os.environ.get('RUN_MAIN') == 'true':
            from detector.services.ai_engine import AIEdgeScanner
            print("==> He thong : Chuong trinh khoi dong thanh cong...")
            print("==> He thong: Dang kich hoat AI detect doc lap...")

            scanner = AIEdgeScanner(model_path = '/home/dunghoangviet/Dungx/Dungx/ppe_system/models/best(33).pt')

            ai_thread = threading.Thread(target = scanner.run_background_loop, daemon = True)
            ai_thread.start()

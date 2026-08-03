import cv2


class FrameReader:
    def __init__(self, source=0):
        self.camera = cv2.VideoCapture(source)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    def read_frame(self):
        success, frame = self.camera.read()
        if not success:
            return None
        return frame
    def release(self):
        self.camera.release()
    
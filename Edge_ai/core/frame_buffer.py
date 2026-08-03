

class FrameBuffer:
    def __init__(self, max_size=1):
        self.buffer = []
        self.max_size = max_size

    def add_frame(self, frame):
        if len(self.buffer) >= self.max_size:
            self.buffer.pop(0)
        self.buffer.append(frame)

    def get_frame(self):
        if self.buffer:
            return self.buffer[-1]
        return None
    def is_empty(self):
        return len(self.buffer) == 0
    def clear_buffer(self):
        self.buffer.clear()



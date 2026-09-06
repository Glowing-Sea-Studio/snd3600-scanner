import glob
import cv2

class Camera:
    def __init__(self, device="/dev/video0"):
        self.device = device
        self.cap = None

    @staticmethod
    def get_devices():
        devices = sorted(glob.glob("/dev/video*"))
        return devices if devices else ["/dev/video0"]

    def start(self, w=2592, h=1944):
        self.release()
        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            return False
        self.set_size(w, h)
        return True

    def set_size(self, w, h):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))

    def read(self):
        if self.cap:
            return self.cap.read()
        return False, None

    def grab_and_read(self):
        if self.cap:
            self.cap.grab()
            return self.cap.read()
        return False, None

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None

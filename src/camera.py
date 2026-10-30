"""Camera Manager."""
import cv2


class Camera:
    def __init__(self, index=0, width=640, height=480, mirror=True):
        self.index, self.width, self.height, self.mirror = index, width, height, mirror
        self.cap = None

    def open(self) -> bool:
        self.release()
        cap = cv2.VideoCapture(self.index)
        if not cap.isOpened():
            cap.release()
            return False
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap = cap
        return True

    def read(self):
        """Return a BGR frame, or None if the camera is missing / disconnected."""
        if self.cap is None:
            return None
        ok, frame = self.cap.read()
        if not ok or frame is None:
            return None
        return cv2.flip(frame, 1) if self.mirror else frame

    @staticmethod
    def available(max_index=4):
        found = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                found.append(i)
            cap.release()
        return found

    def switch(self):
        """Cycle to the next available camera."""
        cams = self.available()
        if len(cams) > 1:
            self.index = cams[(cams.index(self.index) + 1) % len(cams)] if self.index in cams else cams[0]
            return self.open()
        return False

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

from threading import Thread
import cv2 as cv


class VideoStream:
    def __init__(self, stream_url):
        self.cap = cv.VideoCapture(stream_url)
        self.frame = None
        self.running = True
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        """ 스트림에서 계속 프레임을 읽어 최신 상태 유지 """
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame

    def get_frame(self):
        """ 최신 프레임 반환 """
        return self.frame

    def stop(self):
        """ 스트림 중지 """
        self.running = False
        self.thread.join()
        self.cap.release()

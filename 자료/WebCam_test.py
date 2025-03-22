from ultralytics import YOLO

# Load the YOLO11 model
model = YOLO("./yolo11/yolo11n.pt")

# Export the model to NCNN format
model.export(format="ncnn")  # creates '/yolo11n_ncnn_model'

# Load the exported NCNN model
ncnn_model = YOLO("./yolo11n_ncnn_model")

import cv2
import numpy as np
import time
from flask import Flask, Response
from ultralytics import YOLO
import psutil

# Flask 앱 초기화
app = Flask(__name__)

def print_memory_usage():

    process = psutil.Process()

    mem_info = process.memory_info()

    print(f"Memory Usage: {mem_info.rss / 1024 / 1024:.2f} MB")

# YOLO 탐지 클래스
class YOLODetector:
    def __init__(self, stream_url):
        self.model = "./yolo11/yolo11n.pt"  # YOLO 모델 경로
        self.stream_url = stream_url   # 라즈베리파이 MJPEG 스트림 URL
        self.ncnn_model = YOLO(self.model)  # YOLO 모델 로드
        self.cap = cv2.VideoCapture(self.stream_url)

        if not self.cap.isOpened():
            raise ValueError("라즈베리파이 스트림을 열 수 없습니다. URL을 확인하세요.")

        self.colors = np.random.uniform(0, 255, size=(len(self.ncnn_model.names), 3))  # 탐지 색상

    def get_processed_frame(self):
        start_time = time.time()

        # 스트림에서 프레임 읽기
        ret, frame = self.cap.read()
        if not ret:
            return None

        img = frame.copy()
        results = self.ncnn_model(img)  # YOLO 탐지 수행

        end_time = time.time()
        inference_time = (end_time - start_time) * 1000 

        print(f"Inference Time: {inference_time:.2f} ms")
        # Print memory usage after capturing frame
        print_memory_usage()
        # 탐지 결과 처리
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].item()
                cls = box.cls[0].item()
                class_name = self.ncnn_model.names[int(cls)]

                if conf >= 0.65:  # 신뢰도 임계값
                    color = self.colors[int(cls)]
                    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
                    cv2.putText(
                        img,
                        f"{class_name} {conf:.2f}",
                        (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        color,
                        3,
                    )

        _, buffer = cv2.imencode('.jpg', img)
        return buffer.tobytes()

# YOLO 탐지기 초기화 (라즈베리파이 스트림 URL 지정)
yolo_detector = YOLODetector("http://192.168.10.250:8000/stream.mjpg")

@app.route('/')
def processed_video_feed():
    # 스트림으로 연산된 데이터를 전송
    def generate_frames():
        while True:
            frame = yolo_detector.get_processed_frame()
            if frame is None:       
                break
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)

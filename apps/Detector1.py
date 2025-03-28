from ultralytics import YOLO
import cv2 as cv
import numpy as np
import logging

from apps.auth.models import Camera


# logging.getLogger("ultralytics").disabled = True  # YOLO 로깅 완전 비활성화
logging.getLogger("ultralytics").setLevel(logging.CRITICAL)  # 최소 로그만 출력

# YOLO 탐지 클래스
class YOLODetector:
    def __init__(self, stream_url):
        self.stream_url = stream_url 
        self.ncnn_model = YOLO("./yolo11/yolo11n_ncnn_model")

        self.colors = np.random.uniform(0, 255, size=(len(self.ncnn_model.names), 3))  # 탐지 색상

    def get_processed_frame(self):
        # 스트림에서 프레임 읽기

        cap = cv.VideoCapture()

        if not cap.isOpened():
            raise ValueError("라즈베리파이 스트림을 열 수 없습니다. URL을 확인하세요.")

        ret, frame = cap.read()  # fail 
        if not ret:
            return None

        img = frame.copy()
        results = self.ncnn_model(img)  # YOLO 탐지 수행

        # 탐지 결과 처리
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].item()
                cls = box.cls[0].item()
                class_name = self.ncnn_model.names[int(cls)]

                if conf >= 0.65:  # 신뢰도 임계값
                    color = self.colors[int(cls)]
                    cv.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
                    cv.putText(
                        img,
                        f"{class_name} {conf:.2f}",
                        (int(x1), int(y1) - 10),
                        cv.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        color,
                        3,
                    )

        _, buffer = cv.imencode('.jpg', img)
        return buffer.tobytes()
    

from ultralytics import YOLO
import cv2
import numpy as np

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

        # 스트림에서 프레임 읽기
        ret, frame = self.cap.read()
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

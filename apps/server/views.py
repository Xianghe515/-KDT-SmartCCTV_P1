from flask import Flask, Blueprint, Response, render_template
from flask_login import current_user, login_required
import cv2 as cv
from ultralytics import YOLO
import numpy as np
import logging

from apps.auth.models import Camera

streaming = Blueprint(
    "streaming",
    __name__,
    template_folder="templates",
)

# logging.getLogger("ultralytics").disabled = True  # YOLO 로깅 완전 비활성화
logging.getLogger("ultralytics").setLevel(logging.CRITICAL)  # 최소 로그만 출력

# YOLO 탐지기 초기화 (라즈베리파이 스트림 URL 지정)
# cap= cv.VideoCapture("http://192.168.10.250:8000/")
# yolo_detector = YOLODetector("http://192.168.10.250:8000/")

@streaming.route("/index")
def index():
    return render_template("server/index.html")

@streaming.route("/")
def home():
        # 유저가 가지고 있는 device_id를 통해 ip_address를 불러와야 함
        # 한 유저가 가지고 있는 디바이스 개수 세서 3개면 3개 전부 출력할 수 있어야 함     * 아직 등록한 디바이스가 없다면?
    if current_user.is_authenticated:
        cameras = Camera.query.filter_by(user_id=current_user.id).all()
        print(cameras)
        return render_template("server/home.html", cameras=cameras)
    else:
        return render_template("server/home.html")



@streaming.route("/video")
@login_required
def video():
    user_id = current_user.id
    cam = Camera.query.filter_by(user_id=user_id).first()
    ip_address = cam.ip_address
    try:
        cap = cv.VideoCapture(f"http://{ip_address}:8000/")
    except:
        print("등록된 기기가 없습니다.")
    # 웹캠 데이터를 스트림으로 송출
    def generate_frames():
        while True:
            ret, frame = cap.read()
            if not ret:
                print("웹캠 프레임을 읽을 수 없습니다.")
                break
            _, buffer = cv.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



@streaming.route("/yolo_video")
@login_required
def yolo_video():
    user_id = current_user.id
    cam = Camera.query.filter_by(user_id=user_id).first()
    if not cam:
        return "등록된 기기가 없습니다."  # 또는 다른 적절한 처리

    ip_address = cam.ip_address
    stream_url = f"http://{ip_address}:8000/"

    ncnn_model = YOLO("./yolo11/yolo11n_ncnn_model")
    colors = np.random.uniform(0, 255, size=(len(ncnn_model.names), 3))  # 탐지 색상
    
    

    def generate_frames():
        while True:
            # 매 프레임마다 VideoCapture 객체를 초기화합니다. (성능에 좋지 않은 방식입니다.)
            cap = cv.VideoCapture(stream_url)
            if not cap.isOpened():
                print(f"스트림 URL을 열 수 없습니다: {stream_url}")
                cap.release()  # 스트림을 열지 못하면 해제
                break  # 또는 재시도 로직 추가

            ret, frame = cap.read()
            if not ret:
                print("프레임을 읽을 수 없습니다. 스트림 종료.")
                cap.release()
                break

            img = frame.copy()
            results = ncnn_model(img)  # YOLO 탐지 수행

            # 탐지 결과 처리
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].item()
                    cls = box.cls[0].item()
                    class_name = ncnn_model.names[int(cls)]

                    if conf >= 0.65:  # 신뢰도 임계값
                        color = colors[int(cls)]
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
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type:image/jpeg\r\n'
                   b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
                   b'\r\n' + frame_bytes + b'\r\n')

            cap.release()  # 매 프레임 처리 후 VideoCapture 객체 해제

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@streaming.route("/live")
def streaming_page():
    return render_template("server/live.html")


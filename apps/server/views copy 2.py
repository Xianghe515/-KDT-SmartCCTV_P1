from flask import Flask, Blueprint, Response, render_template
from flask_login import current_user
import cv2 as cv
from ultralytics import YOLO
import numpy as np
import logging

from apps.Detector1 import YOLODetector
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
        return render_template("server/home.html")



@streaming.route("/video")
def video():
    user_id = current_user.id
    cam = Camera.query.filter_by(user_id=user_id).first()
    ip_address = cam.ip_address
    try:
        cap = cv.VideoCapture(f"http://{ip_address}:8000/")
    except Exception as e:
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
def yolo_video():
    user_id = current_user.id
    cam = Camera.query.filter_by(user_id=user_id).first()
    ip_address = cam.ip_address
    try:
        yolo_detector = YOLODetector(f"http://{ip_address}:8000/")
    except Exception as e:
        print("등록된 기기가 없습니다.")
    # 스트림으로 연산된 데이터를 전송
    def generate_frames():
        while True:
            frame = yolo_detector.get_processed_frame()
            if frame is None:
                print("프레임을 찾을 수 없음")
                break
            yield (b'--frame\r\n'
                        b'Content-Type:image/jpeg\r\n'
                        b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n'
                        b'\r\n' + frame + b'\r\n')
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@streaming.route("/live")
def streaming_page():
    return render_template("server/live.html")

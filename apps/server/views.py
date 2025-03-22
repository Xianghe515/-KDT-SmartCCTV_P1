from flask import Flask, Blueprint, Response, render_template
import cv2 as cv
from apps.Detector1 import YOLODetector

streaming = Blueprint(
    "streaming",
    __name__,
    template_folder="templates",
)

# YOLO 탐지기 초기화 (라즈베리파이 스트림 URL 지정)
yolo_detector = YOLODetector("http://192.168.10.250:8000/stream.mjpg")

@streaming.route("/")
def index():
    return render_template("server/index.html")

@streaming.route("/video")
def video():
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


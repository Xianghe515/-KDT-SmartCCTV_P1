from flask import Flask, Blueprint, Response, render_template
import cv2 as cv
from apps.Detector1 import YOLODetector


streaming = Blueprint(
    "streaming",
    __name__,
    template_folder="templates",
)


@streaming.route("/")
def index():
    return render_template("server/index.html")

# YOLO 탐지기 초기화 (라즈베리파이 스트림 URL 지정)
# cap_rpi = cv.VideoCapture("http://192.168.10.250:8000/stream.mjpg")
yolo_detector = YOLODetector("http://192.168.10.250:8000/stream.mjpg")

# @streaming.route("/video")
# def video_test():
#     # 웹캠 데이터를 스트림으로 송출
#     def generate_frames():
#         while True:
#             ret, frame = cap_rpi.read()
#             if not ret:
#                 print("웹캠 프레임을 읽을 수 없습니다.")
#                 break
#             _, buffer = cv.imencode('.jpg', frame)
#             frame_bytes = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@streaming.route("/yolo_video")
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


# test YOLODetector
from apps.test_Detector1 import test_YOLODetector

cap = cv.VideoCapture(0)
test_yolo_detector = test_YOLODetector("http://127.0.0.1:5000/knockx2/video_test")

@streaming.route("/video_test")
def video_test():
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

@streaming.route("yolo_video_test")
def yolo_video_test():
    def generate_frames():
        while True:
            frame = test_yolo_detector.get_processed_frame()
            if frame is None:
                print("프레임을 찾을 수 없음")
                break
            yield (b'--frame\r\n'
                        b'Content-Type:image/jpeg\r\n'
                        b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n'
                        b'\r\n' + frame + b'\r\n')
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@streaming.route("live_test")
def streaming_test():
    return render_template("server/live_test.html")
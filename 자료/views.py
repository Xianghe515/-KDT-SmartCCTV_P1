from flask import Flask, Blueprint, Response, render_template
import cv2 as cv
import sys
from Detector1 import YOLODetector

streaming = Blueprint(
    "streaming",
    __name__,
    template_folder="templates",
)

# def generate_frames():  # 프레임 생성 함수 
#     cap = cv.VideoCapture(0)  # 웹캠 연결
#     cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
#     cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
#     if not cap.isOpened():
#         sys.exit('웹캠 연결 실패')

#     while True:
#         ret, frame = cap.read()  # 웹캠에서 프레임 읽기
#         if not ret:
#             print('프레임 읽기 실패')
#             break
#         else:
#             _, buffer = cv.imencode('.jpg', frame)
#             frame = buffer.tobytes()
#             yield (b'--frame\r\n'
#                 b'Content-Type: image/jpg\r\n\r\n' + frame + b'\r\n')
#                 # WebP 평균 인코딩 시간: 약 0.0124초 (1 프레임당)
#                 # JPG 평균 인코딩 시간: 약 0.0022초 (1 프레임당)           

#     cap.release()
#     cv.destroyAllWindows()

# YOLO 탐지기 초기화 (라즈베리파이 스트림 URL 지정)
yolo_detector = YOLODetector("http://192.168.10.250:8000/stream.mjpg")

@streaming.route("/")
def index():
    return render_template("index.html")

# @streaming.route("/video")
# def video():
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@streaming.route("/video")
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

@streaming.route("/live")
def streaming_page():
    return render_template("live.html")


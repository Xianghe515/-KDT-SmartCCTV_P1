from flask import Flask, Blueprint, Response, render_template
from flask_login import current_user, login_required
import cv2 as cv
from ultralytics import YOLO
import numpy as np
import logging
import datetime
import os
from threading import Lock, Thread

from apps.auth.models import Camera, Log, Video
from apps.app import db
from apps.VideoStream import VideoStream

streaming = Blueprint(
    "streaming",
    __name__,
    template_folder="templates",
)

logging.getLogger("ultralytics").setLevel(logging.CRITICAL)

@streaming.route("/index")
def index():
    return render_template("server/index.html")

@streaming.route("/")
def home():
    if current_user.is_authenticated:
        cameras = Camera.query.filter_by(user_id=current_user.id).all()
        print(cameras)
        return render_template("server/home.html", cameras=cameras)
    else:
        return render_template("server/home.html")

@streaming.route("/video/<camera_id>")
@login_required
def video(camera_id):
    user_id = current_user.id
    cam = Camera.query.filter_by(user_id=user_id, camera_id=camera_id).first()
    ip_address = cam.ip_address
    try:
        cap = cv.VideoCapture(f"http://{ip_address}:8000/")
    except:
        print("등록된 기기가 없습니다.")
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


@streaming.route("/yolo_video/<camera_id>")
@login_required
def yolo_video(camera_id):
    user_id = current_user.id
    cam = Camera.query.filter_by(user_id=user_id, camera_id=camera_id).first()
    if not cam:
        return "등록된 기기가 없습니다."

    ip_address = cam.ip_address
    stream_url = f"http://{ip_address}:8000/"

    ncnn_model = YOLO("./yolo11/yolo11n_ncnn_model")
    colors = np.random.uniform(0, 255, size=(len(ncnn_model.names), 3))

    # 멀티 스레딩 방식으로 프레임 가져오기
    stream = VideoStream(stream_url)

    def generate_frames():
        while True:
            frame = stream.get_frame()
            if frame is None:
                continue  # 프레임이 아직 준비되지 않았으면 다시 시도

            img = frame.copy()
            results = ncnn_model(img)

            now = datetime.datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            cv.putText(
                img,
                current_time,
                (img.shape[1] - 280, img.shape[0] - 20),
                cv.FONT_HERSHEY_DUPLEX,
                0.7,
                (83, 115, 219),
                2,
            )

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].item()
                    cls = box.cls[0].item()
                    class_name = ncnn_model.names[int(cls)]

                    if conf >= 0.65:
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

            _, buffer = cv.imencode('.jpg', img, [cv.IMWRITE_JPEG_QUALITY, 70])
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type:image/jpeg\r\n'
                   b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
                   b'\r\n' + frame_bytes + b'\r\n')

    # while true 루프가 끝나지 않아 stream.stop() 실행되지 않음 
    #   -> Flask Response 객체를 사용할 때, call_on_close()를 이용하여 스트리밍이 종료될 때 stream.stop()을 호출하도록 변경.
    #   => 사용자가 페이지를 떠나거나 브라우저에서 스트리밍을 중단하면 자동으로 stream.stop()이 실행됨.
    response = Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.call_on_close(stream.stop)     

    return response

# @streaming.route("/yolo_video/<camera_id>")
# @login_required
# def yolo_video(camera_id):
#     user_id = current_user.id
#     cam = Camera.query.filter_by(user_id=user_id, camera_id=camera_id).first()
#     if not cam:
#         return "등록된 기기가 없습니다."

#     ip_address = cam.ip_address
#     stream_url = f"http://{ip_address}:8000/"

#     ncnn_model = YOLO("./yolo11/yolo11n_ncnn_model")
#     colors = np.random.uniform(0, 255, size=(len(ncnn_model.names), 3))

#     def generate_frames():
#         cap = cv.VideoCapture(stream_url)
#         if not cap.isOpened():
#             print(f"스트림 URL을 열 수 없습니다: {stream_url}")
#             yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n\r\n'
#             return
#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 print("프레임을 읽을 수 없습니다. 스트림 종료.")
#                 break

#             img = frame.copy()
#             results = ncnn_model(img)

#             now = datetime.datetime.now()
#             current_time = now.strftime("%Y-%m-%d %H:%M:%S")
#             cv.putText(
#                 img,
#                 current_time,
#                 (img.shape[1] - 280, img.shape[0] - 20),
#                 cv.FONT_HERSHEY_DUPLEX,
#                 0.7,
#                 (83, 115, 219),
#                 2,
#             )

#             for result in results:
#                 for box in result.boxes:
#                     x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
#                     conf = box.conf[0].item()
#                     cls = box.cls[0].item()
#                     class_name = ncnn_model.names[int(cls)]

#                     if conf >= 0.65:
#                         color = colors[int(cls)]
#                         cv.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
#                         cv.putText(
#                             img,
#                             f"{class_name} {conf:.2f}",
#                             (int(x1), int(y1) - 10),
#                             cv.FONT_HERSHEY_SIMPLEX,
#                             0.8,
#                             color,
#                             3,
#                         )

#             _, buffer = cv.imencode('.jpg', img, [cv.IMWRITE_JPEG_QUALITY, 70])
#             frame_bytes = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type:image/jpeg\r\n'
#                    b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
#                    b'\r\n' + frame_bytes + b'\r\n')

#         cap.release()
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@streaming.route("/live/<camera_id>")
def streaming_page(camera_id):
    user_id = current_user.id
    cam = Camera.query.filter_by(user_id=user_id, camera_id=camera_id).first()
    if not cam:
        return "등록된 기기가 없습니다."
    return render_template("server/live.html", camera_id=camera_id)

@streaming.route("/live/<camera_id>/capture")
def capture(camera_id):
    user_id = current_user.id
    cam = Camera.query.filter_by(user_id=user_id, camera_id=camera_id).first()
    if not cam:
        return "등록된 기기가 없습니다."

    ip_address = cam.ip_address
    stream_url = f"http://{ip_address}:8000/"

    ncnn_model = YOLO("./yolo11/yolo11n_ncnn_model")
    colors = np.random.uniform(0, 255, size=(len(ncnn_model.names), 3))

    cap = cv.VideoCapture(stream_url)
    if not cap.isOpened():
        return "스트림을 열 수 없습니다."

    ret, frame = cap.read()
    cap.release()
    if not ret:
        return "프레임을 읽을 수 없습니다."

    img = frame.copy()
    results = ncnn_model(img)

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].item()
            cls = box.cls[0].item()
            class_name = ncnn_model.names[int(cls)]

            if conf >= 0.65:
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
    return Response(buffer.tobytes(), mimetype="image/jpeg")

@streaming.route("/videos")
@login_required
def view_videos():
    videos = Video.query.filter_by(user_id=current_user.id).order_by(Video.created_at.desc()).all()
    return render_template("server/videos.html", videos=videos)

# @streaming.route("/video_feed/<filename>")
# @login_required
# def video_feed(filename):
#     file_path = os.path.join(VIDEO_STORAGE_PATH, filename)
#     if not os.path.exists(file_path):
#         return "비디오 파일을 찾을 수 없습니다.", 404

#     def generate():
#         with open(file_path, "rb") as f:
#             while True:
#                 chunk = f.read(4096)
#                 if not chunk:
#                     break
#                 yield chunk

#     return Response(generate(), mimetype="video/avi")
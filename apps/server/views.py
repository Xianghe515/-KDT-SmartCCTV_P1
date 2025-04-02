from flask import Flask, Blueprint, Response, render_template
from flask_login import current_user, login_required
import cv2 as cv
from ultralytics import YOLO
import numpy as np
import logging
import datetime
import os
import time
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

from apps.auth.models import Camera, Log, Video
from apps.app import db
from apps.VideoStream import VideoStream


# dll을 못 불러오는 오류 발생       *dll - C언어 동적 라이브러리
import ctypes  # c 동적 라이브러리 모듈
# print(os.getcwd())
ctypes.windll.LoadLibrary('./openh264-1.8.0-win64.dll')  # windll 라이브러리를 직접 로드하여 해결

logging.getLogger("ultralytics").setLevel(logging.CRITICAL)

streaming = Blueprint(
    "streaming",
    __name__,
    template_folder="templates",
)
VIDEO_STORAGE_PATH = "./apps/server/static/videos"  # 저장할 비디오 폴더 경로

engine = create_engine('mysql+pymysql://knockx2:knockx2@localhost/knockx2')
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

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
    user_name = current_user.user_name
    cam = Camera.query.filter_by(user_id=user_id, camera_id=camera_id).first()
    if not cam:
        return "등록된 기기가 없습니다."

    ip_address = cam.ip_address
    stream_url = f"http://{ip_address}:8000/"

    ncnn_model = YOLO("./yolo11/yolo11n_ncnn_model")
    colors = np.random.uniform(0, 255, size=(len(ncnn_model.names), 3))

    stream = VideoStream(stream_url)
    
    fourcc = cv.VideoWriter_fourcc(*'avc1')
    
    is_recording = False
    video_writer = None
    last_detection_time = None
    recording_start_time = None
    min_record_duration = 5  # 최소 녹화 시간 (초)
    countdown_timer = 0 # 카운트다운 타이머 추가
    detection_start_time = None # 감지 시작 시간 변수 추가
    detection_delay = 5 # 녹화 시작 전 감지 유지 시간 (초)

    if not os.path.exists(VIDEO_STORAGE_PATH):
        os.makedirs(VIDEO_STORAGE_PATH)

    def generate_frames():
        nonlocal is_recording, video_writer, last_detection_time, recording_start_time, countdown_timer, detection_start_time

        while True:
            frame = stream.get_frame()
            if frame is None:
                continue

            img = frame.copy()
            results = ncnn_model(img)
            detected = False

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
                    if conf >= 0.40:
                        detected = True
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
                        break  # 하나의 객체라도 감지되면 녹화 시작/유지

                if detected:
                    break

            if detected:
                last_detection_time = datetime.datetime.now()
                countdown_timer = 0
                if not is_recording:
                    is_recording = True
                    recording_start_time = datetime.datetime.now()
                    filename = f"{user_name}_{camera_id}_{now.strftime('%Y%m%d_%H%M%S')}.mp4"
                    filepath = os.path.join(VIDEO_STORAGE_PATH, filename)
                    video_writer = cv.VideoWriter(filepath, fourcc, 20.0, (img.shape[1], img.shape[0]))
                    print("─" * 81)
                    print(f"\t녹화 시작: {filepath}")
                    print("─" * 81)

            if is_recording:
                video_writer.write(img)
                elapsed_time = (datetime.datetime.now() - (last_detection_time if last_detection_time else recording_start_time)).total_seconds()
                total_elapsed_time = (datetime.datetime.now() - recording_start_time).total_seconds()

                if not detected:
                    if countdown_timer > 0:
                        print("─" * 81)
                        print(f"\t\t감지 대상이 없습니다. {countdown_timer}초 후 녹화를 종료합니다.")
                        print("─" * 81)
                        countdown_timer -= 1
                        time.sleep(1)
                        if countdown_timer == 0:
                            is_recording = False
                            video_writer.release()
                            video_writer = None
                            print("─" * 81)
                            print("\t\t\t\t   녹화 종료")
                            print("─" * 81)
                            filename = f"{user_name}_{camera_id}_{recording_start_time.strftime('%Y%m%d_%H%M%S')}.mp4"
                            
                            new_video = Video(
                                user_id=user_id,
                                camera_id=camera_id,
                                filename=filename,
                                created_at=recording_start_time,
                                duration=total_elapsed_time,
                                detected_objects = class_name,
                            )
                            session.add(new_video)
                            session.commit()

                    elif elapsed_time >= min_record_duration and countdown_timer == 0:
                        countdown_timer = 5
                # 감지된 대상이 있고 녹화 중이면 last_detection_time 업데이트
                elif detected:
                    pass
                # 아직 최소 녹화 시간을 채우지 못했으면 계속 녹화
                elif not detected and total_elapsed_time < min_record_duration:
                    pass # 녹화 유지

            if is_recording:
                video_writer.write(img)
            _, buffer = cv.imencode('.jpg', img)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type:image/jpeg\r\n'
                   b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
                   b'\r\n' + frame_bytes + b'\r\n')

    response = Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.call_on_close(stream.stop)
    return response

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
def video_storage():
    user_id = current_user.id
    cameras = Camera.query.filter_by(user_id=current_user.id).all()
    videos = Video.query.filter_by(user_id=user_id).order_by(Video.created_at.desc()).all()
    return render_template("server/videos.html", videos=videos, cameras=cameras)



@streaming.route("/video_feed/<filename>")
@login_required
def video_feed(filename):
    file_path = os.path.join(VIDEO_STORAGE_PATH, filename)
    if not os.path.exists(file_path):
        return "비디오 파일을 찾을 수 없습니다.", 404

    def generate():
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                yield chunk

    return Response(generate(), mimetype="video/mp4")
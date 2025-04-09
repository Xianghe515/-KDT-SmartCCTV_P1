from flask import Flask, Blueprint, Response, render_template, request, send_from_directory, flash, redirect, url_for
from flask_login import current_user, login_required
import cv2 as cv
from ultralytics import YOLO
import numpy as np
import logging
import datetime
import os
import time
import re
from datetime import datetime
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from flask_wtf.csrf import validate_csrf
from apps.auth.forms import DeleteForm
from apps.auth.models import Camera, Log, Video
from apps.app import db
from apps.VideoStream import VideoStream

# dll을 못 불러오는 오류 발생         *dll - C언어 동적 라이브러리
import ctypes  # c 동적 라이브러리 모듈
# print(os.getcwd())
ctypes.windll.LoadLibrary('./openh264-1.8.0-win64.dll')  # windll 라이브러리를 직접 로드하여 해결

logging.getLogger("ultralytics").setLevel(logging.CRITICAL)

streaming = Blueprint(
    "streaming",
    __name__,
    template_folder="templates",
)
BLUR_RADIUS = 25  # 사람 전체 블러 강도
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
        return render_template("server/home.html", cameras=cameras, active_page='home')
    else:
        return render_template("server/home.html", active_page='home')


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

    # YOLO 모델 초기화
    try:
        ncnn_model = YOLO(".\\yolo11\\yolo11n_ncnn_model")
        print("YOLO 모델 로드 성공")
    except Exception as e:
        print(f"YOLO 모델 로드 실패: {str(e)}")
        return f"모델 로드 실패: {str(e)}"

    colors = np.random.uniform(0, 255, size=(len(ncnn_model.names), 3))
    stream = VideoStream(stream_url)
    fourcc = cv.VideoWriter_fourcc(*'avc1')

    target_class_indices = [0]
    detection_interval = 30  # 인터벌 시간 (초)
    BLUR_RADIUS = 1

    if not os.path.exists(VIDEO_STORAGE_PATH):
        os.makedirs(VIDEO_STORAGE_PATH)

    def generate_frames():
        print("프레임 생성 시작 (YOLO 반복 인터벌)")
        while True:
            interval_start_time = time.time()
            interval_has_detection = False
            detection_start_time = None
            detection_active = False
            detection_end_time = None
            is_recording = True

            now = datetime.now()
            filename = f"{user_name}_{camera_id}_{now.strftime('%Y%m%d_%H%M%S')}.mp4"
            recorded_filename = os.path.join(VIDEO_STORAGE_PATH, filename)
            video_writer = None

            frame = stream.get_frame()

            height, width = frame.shape[:2]
            video_writer = cv.VideoWriter(recorded_filename, fourcc, 20.0, (width, height))
            print(f"녹화 시작: {recorded_filename}")

            while True:
                frame = stream.get_frame()
                if frame is None:
                    continue

                img = frame.copy()
                results = ncnn_model(img)

                now = datetime.now()
                current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                cv.putText(img, current_time_str, (img.shape[1] - 280, img.shape[0] - 20),
                        cv.FONT_HERSHEY_DUPLEX, 0.7, (83, 115, 219), 2)

                detected_this_frame = False

                for result in results:
                    for box in result.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].item()
                        cls = box.cls[0].item()
                        class_index = int(cls)

                        if class_index in target_class_indices and conf >= 0.4:
                            detected_this_frame = True
                            color = colors[class_index]
                            cv.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
                            cv.putText(img, f"{ncnn_model.names[class_index]} {conf:.2f}",
                                    (int(x1), int(y1) - 10), cv.FONT_HERSHEY_SIMPLEX, 0.8, color, 3)
                            roi = img[int(y1):int(y2), int(x1):int(x2)]
                            if roi.size != 0:
                                blurred = cv.GaussianBlur(roi, (BLUR_RADIUS, BLUR_RADIUS), 0)
                                img[int(y1):int(y2), int(x1):int(x2)] = blurred

                # 감지 상태 처리
                if detected_this_frame:
                    if not detection_active:
                        print("🔵 감지됨")
                        detection_active = True
                        detection_start_time = time.time()
                        detected_names = [ncnn_model.names[int(res.boxes.cls[0].item())] for res in results if res.boxes and int(res.boxes.cls[0].item()) in target_class_indices]
                    else:
                        print("🟢 감지 유지")
                        if time.time() - detection_start_time >= 10:
                            interval_has_detection = True
                            detection_end_time = None  # 감지 유지 중이므로 감지 해제 타이머 초기화
                else:
                    if detection_active:
                        if detection_end_time is None:
                            print("🟡 감지 해제됨 (대기)")
                            detection_end_time = time.time()
                        elif time.time() - detection_end_time >= 10:
                            # 감지가 해제되고 10초 이상 지났으면 종료
                            detection_duration = detection_end_time - detection_start_time
                            if detection_duration < 10:
                                print("🔴 감지 지속 시간이 10초 미만 → 영상 삭제 및 인터벌 종료")
                                interval_has_detection = False
                            else:
                                print("⚪ 감지 종료 후 10초 경과 → 인터벌 종료")
                            break
                    else:
                        print("⚫ 감지 없음")
                        if time.time() - interval_start_time >= detection_interval:
                            print("⏹️ 감지 없음 + 인터벌 종료")
                            break

                if not detection_active and time.time() - interval_start_time >= detection_interval:
                    print("⏹️ 감지 없음 + 인터벌 종료")
                    break

                if is_recording and video_writer:
                    video_writer.write(img)

                _, buffer = cv.imencode('.jpg', img)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type:image/jpeg\r\n'
                    b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
                    b'\r\n' + frame_bytes + b'\r\n')


            # 녹화 종료 후 파일 처리
            if video_writer:
                video_writer.release()

            if interval_has_detection:
                print("저장 조건 충족 → DB 저장")
                created_at = datetime.fromtimestamp(interval_start_time)
                end_time = datetime.now()
                duration = (end_time - created_at).total_seconds()

                new_video = Video(
                    user_id=user_id,
                    camera_id=camera_id,
                    filename=os.path.basename(recorded_filename),
                    created_at=created_at,
                    end_time=end_time,
                    duration=duration,
                    detected_objects=", ".join(set(detected_names)),
                )
                session.add(new_video)
                session.commit()

                
            else:
                print("감지 없음 → 영상 삭제")
                if os.path.exists(recorded_filename):
                    os.remove(recorded_filename)

            print("다음 인터벌로 이동...\n")


    response = Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
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


@streaming.route("/videos", methods=["GET"])
@login_required
def video_storage():
    user_id = current_user.id
    cameras = Camera.query.filter_by(user_id=user_id).all()

    # 기본 쿼리 설정
    query = Video.query.filter_by(user_id=user_id).order_by(Video.created_at.desc())

    # 검색어 처리 (쉼표 또는 공백으로 구분된 키워드)
    search_label = request.args.get("label", "").strip()
    if search_label:
        keywords = re.split(r'[,\s]+', search_label)  # 쉼표 또는 공백으로 분리
        filters = [Video.detected_objects.like(f"%{keyword}%") for keyword in keywords if keyword]
        if filters:
            query = query.filter(*filters)  # AND 조건으로 검색

    # 날짜 필터
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")

    if start_date_str or end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None

            now = datetime.now()

            # 메시지 먼저 띄우기 위한 체크
            if (start_date and start_date > now) or (end_date and end_date > now):
                flash("현재보다 미래로 설정할 수 없습니다.", "warning")

            # 시작일 > 종료일 검사
            if start_date and end_date and start_date > end_date:
                flash("시작일은 종료일보다 빠를 수 없습니다.", "warning")
            else:
                # 미래 날짜 제한은 메시지 출력 후 진행
                if start_date and start_date > now:
                    start_date = None
                if end_date and end_date > now:
                    end_date = now

                # 실제 필터
                if start_date:
                    query = query.filter(Video.end_time >= start_date)
                if end_date:
                    end_of_day = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
                    query = query.filter(Video.created_at <= end_of_day)

        except ValueError:
            flash("날짜 형식이 잘못되었습니다.", "danger")

    # 페이지네이션 처리
    page = request.args.get("page", 1, type=int)
    per_page = 3  # 한 페이지에 표시할 비디오 개수
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 비디오 객체에 detected_objects_list 속성 추가
    for video in pagination.items:
        if video.detected_objects:
            video.detected_objects_list = re.split(r'[,\s]+', video.detected_objects.strip())
        else:
            video.detected_objects_list = []

    return render_template(
        "server/videos.html",
        videos=pagination.items,
        cameras=cameras,
        pagination=pagination,
        search_label=search_label,
        form=DeleteForm()
    )


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


@streaming.route("/videos/delete", methods=["POST"])
@login_required
def delete_videos():
    user_id = current_user.id
    selected_videos = request.form.getlist("selected_videos")
    if not selected_videos:
        flash("삭제할 동영상을 선택해주세요.", "warning")
        return redirect(url_for("streaming.video_storage"))

    try:
        for filename in selected_videos:
            video = Video.query.filter_by(user_id=user_id, filename=filename).first()
            if video:
                file_path = os.path.join(VIDEO_STORAGE_PATH, video.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(video)
        db.session.commit()
        flash("선택한 동영상을 삭제했습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"동영상 삭제 중 오류가 발생했습니다: {e}", "danger")
        logging.error(f"Error deleting videos: {e}")

    return redirect(url_for("streaming.video_storage"))
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

    # YOLO 모델 초기화
    try:
        ncnn_model = YOLO(".\yolo11\yolo11n_ncnn_model")
        print("YOLO 모델 로드 성공")
    except Exception as e:
        print(f"YOLO 모델 로드 실패: {str(e)}")
        return f"모델 로드 실패: {str(e)}"

    colors = np.random.uniform(0, 255, size=(len(ncnn_model.names), 3))
    stream = VideoStream(stream_url)
    fourcc = cv.VideoWriter_fourcc(*'avc1')

    # 녹화 관련 변수 초기화
    is_recording = False
    video_writer = None
    last_detection_time = None
    recording_start_time = None
    target_class_indices = [0]  # 감지할 객체 클래스 (0번 인덱스만 해당 - 사람)
    detection_interval = 60  # 1분 단위 녹화 확인 간격 (초)
    last_check_time = time.time()
    objects_detected_this_interval = False
    object_disappeared_time = None
    recorded_filename = None

    if not os.path.exists(VIDEO_STORAGE_PATH):
        os.makedirs(VIDEO_STORAGE_PATH)
        print(f"비디오 저장 경로 생성: {VIDEO_STORAGE_PATH}")

    def generate_frames():
        nonlocal is_recording, video_writer, last_detection_time, recording_start_time, target_class_indices, last_check_time, objects_detected_this_interval, object_disappeared_time, recorded_filename

        current_interval_start_time = time.time()
        print("프레임 생성 시작 (YOLO with Person Blur)")

        while True:
            frame = stream.get_frame()
            if frame is None:
                print("프레임 읽기 실패 (YOLO)")
                continue

            img = frame.copy()
            results = ncnn_model(img)
            detected_in_frame = False

            # 현재 시간을 이미지에 추가
            now = datetime.now()
            current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            cv.putText(img, current_time_str, (img.shape[1] - 280, img.shape[0] - 20), cv.FONT_HERSHEY_DUPLEX, 0.7, (83, 115, 219), 2)

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].item()
                    cls = box.cls[0].item()
                    class_index = int(cls)

                    if class_index in target_class_indices and conf >= 0.40:
                        detected_in_frame = True
                        color = colors[class_index]
                        cv.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
                        cv.putText(img, f"{ncnn_model.names[class_index]} {conf:.2f}", (int(x1), int(y1) - 10), cv.FONT_HERSHEY_SIMPLEX, 0.8, color, 3)
                        print(f"객체 감지됨 (YOLO): {ncnn_model.names[class_index]}, 신뢰도: {conf:.2f}")

                        # 사람(class_index == 0) 감지 시 블러 처리
                        person_roi = img[int(y1):int(y2), int(x1):int(x2)]
                        if not person_roi.size == 0:
                            blurred_person = cv.GaussianBlur(person_roi, (BLUR_RADIUS, BLUR_RADIUS), 0)
                            img[int(y1):int(y2), int(x1):int(x2)] = blurred_person
                            print("사람 객체 블러 처리됨")

            current_time = time.time()
            if current_time - current_interval_start_time >= detection_interval:
                print(f"{detection_interval}초 경과, 객체 감지 여부 확인 (YOLO)")
                if not objects_detected_this_interval and not is_recording and video_writer is None:
                    print("1분 동안 객체 미감지, 시스템 초기화 준비 (YOLO)")
                    pass # 실제 초기화 로직 (변수 리셋 등) 필요
                    print("시스템 초기화 완료 (미감지) (YOLO)")
                objects_detected_this_interval = False
                current_interval_start_time = current_time

            if detected_in_frame:
                if not objects_detected_this_interval:
                    print("새로운 감지 간격 시작 및 객체 감지 (YOLO)")
                    objects_detected_this_interval = True
                    last_detection_time = now
                    if not is_recording:
                        print("녹화 시작 조건 충족 (YOLO)")
                        is_recording = True
                        recording_start_time = now
                        filename = f"{user_name}_{camera_id}_{now.strftime('%Y%m%d_%H%M%S')}.mp4"
                        recorded_filename = os.path.join(VIDEO_STORAGE_PATH, filename)
                        video_writer = cv.VideoWriter(recorded_filename, fourcc, 20.0, (img.shape[1], img.shape[0]))
                        print(f"녹화 시작: {recorded_filename} (YOLO)")
                    object_disappeared_time = None
                else:
                    last_detection_time = now
                    if is_recording and object_disappeared_time is not None:
                        print("객체 재감지, 사라짐 타이머 초기화 (YOLO)")
                        object_disappeared_time = None # 객체 재감지 시 사라짐 타이머 초기화

            elif is_recording and object_disappeared_time is None:
                # 객체가 사라진 시점 기록
                object_disappeared_time = now
                print("객체 사라짐 감지, 10초 카운트 시작 (YOLO)")
            elif is_recording and object_disappeared_time is not None:
                # 객체 사라진 후 10초 경과 확인
                elapsed_since_disappeared = (now - object_disappeared_time).total_seconds()
                print(f"객체 사라짐 후 {elapsed_since_disappeared:.0f}초 경과 (YOLO)")
                # time.sleep(1)
                if elapsed_since_disappeared >= 10:
                    print("객체 사라진 후 10초 경과, 녹화 종료 및 저장 (YOLO)")
                    is_recording = False
                    video_writer.release()
                    video_writer = None
                    recording_end_time = now
                    print(f"녹화 종료 및 저장 완료: {recorded_filename} (YOLO)")
                    # 데이터베이스에 저장
                    detected_objects_names = [ncnn_model.names[int(res.boxes.cls[0].item())] for res in results if res.boxes and int(res.boxes.cls[0].item()) in target_class_indices]
                    new_video = Video(
                        user_id=user_id,
                        camera_id=camera_id,
                        filename=os.path.basename(recorded_filename),
                        created_at=recording_start_time,
                        end_time=recording_end_time,
                        duration=(recording_end_time - recording_start_time).total_seconds(),
                        detected_objects=", ".join(detected_objects_names),
                    )
                    session.add(new_video)
                    session.commit()
                    print(f"데이터베이스 저장 완료: {new_video.filename} (YOLO)")
                    recorded_filename = None # 초기화
                    object_disappeared_time = None # 초기화
                    objects_detected_this_interval = False # 다음 1분 간격 시작을 위해 초기화
            elif elapsed_since_disappeared < 10 and not detected_in_frame:
                # 10초 이내에 사라졌지만 아직 녹화 중
                pass
            elif not detected_in_frame and is_recording and object_disappeared_time is None:
                # 감지 안되고 녹화 중인데 사라짐 시간 기록 안됨 (초기 사라짐 후 바로 미감지)
                object_disappeared_time = now
                print("객체 사라짐 감지 (10초 이내) (YOLO)")
                time.sleep(10) # 10초 대기 후 녹화 종료 및 삭제
                is_recording = False
                if video_writer:
                    video_writer.release()
                    video_writer = None
                    print("객체 10초 이내 사라짐, 녹화 삭제 준비 (YOLO)")
                    if recorded_filename and os.path.exists(recorded_filename):
                        os.remove(recorded_filename)
                        print(f"녹화 삭제 완료: {recorded_filename} (YOLO)")
                    recorded_filename = None
                    object_disappeared_time = None
                    objects_detected_this_interval = False # 다음 1분 간격 시작을 위해 초기화
            else:
                print("녹화 중이 아닌데 객체 사라짐 감지됨 (무시) (YOLO)")


            if is_recording and video_writer is not None:
                video_writer.write(img)
            elif not is_recording and video_writer is not None:
                print("녹화 종료 (비정상?), VideoWriter 해제 (YOLO)")
                video_writer.release()
                video_writer = None
                recorded_filename = None
                object_disappeared_time = None
                objects_detected_this_interval = False

            _, buffer = cv.imencode('.jpg', img)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type:image/jpeg\r\n'
                   b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
                   b'\r\n' + frame_bytes + b'\r\n')
        print("프레임 생성 종료 (YOLO with Person Blur)")

    response = Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.call_on_close(stream.stop)
    print("YOLO 스트리밍 응답 반환 (with Person Blur)")
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

"""
기간 검색 -> 언제부터 언제까지 설정해서 시작 시간 and 종료 시간이 하나라도 포함되면 나타나게끔 
"""


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
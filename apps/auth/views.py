from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required   # type: ignore
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from apps.app import db
from apps.auth.forms import LoginForm, SignUpForm, UpdateForm, PasswordForm, DeviceForm, SingleDeviceForm
from apps.auth.models import User, Camera

auth = Blueprint(
      "auth",
      __name__,
      template_folder="templates",
)

@auth.route("/")
def index():
      return render_template("auth/index.html")

@auth.route("/signup", methods=["GET", "POST"])
def signup():
      # SignUpForm 인스턴스화
      form = SignUpForm()
      if form.validate_on_submit():
            # 생년월일 데이터 처리
            birth_date = form.birth_date.data
            try:
                  # 입력된 문자열을 datetime 객체로 변환
                  birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
            except ValueError:
                  # 유효하지 않은 날짜 처리
                  birth_date = None
            
            # 사용자 데이터 생성
            user = User(
                  user_name=form.user_name.data,
                  email=form.email.data,
                  password=form.password.data,
                  birth_date=birth_date,  # 변환된 생년월일 저장
                  phone_number=form.phone_number.data,
                  # device_id=form.device_id.data,
            )
            
            # 이메일 중복 체크
            if user.is_duplicate_email():
                  flash("지정 이메일 주소는 이미 등록되어 있습니다.")
                  return redirect(url_for("auth.signup"))
            
            # 사용자 정보 등록
            db.session.add(user)
            db.session.commit()

            # 사용자 정보를 세션에 저장
            login_user(user)
            
            # GET 파라미터에 next 키가 존재하고, 값이 없는 경우 사용자의 일람 페이지로 리다이렉트
            next_ = request.args.get("next")
            if next_ is None or not next_.startswith("/"):
                  # 회원가입 완료 시 리다이렉트될 곳 -> auth.index
                  next_ = url_for("streaming.home")
                  return redirect(next_)
      
      return render_template("auth/signup.html", form=form)

@auth.route("/login", methods=["GET", "POST"])
def login():
      form = LoginForm()
      if form.validate_on_submit():
            # 이메일 주소로 데이터베이스에 사용자가 있는지 검사
            user = User.query.filter_by(email=form.email.data).first()
            
            # 사용자가 존재하고 비밀번호가 일치하면 로그인 허가
            if user is not None and user.verify_password(form.password.data):
                  login_user(user)
                  return redirect(url_for("streaming.home"))
            
            # 로그인 실패 메시지 설정
            flash("메일 주소 또는 비밀번호가 일치하지 않습니다.")
            
      return render_template("auth/login.html", form=form)

@auth.route("/<user_id>")
@login_required
def info(user_id):
      form = UpdateForm()
      user = User.query.get(user_id)
      
      return render_template("auth/info.html", form=form, user=user)

@auth.route("/<user_id>/update", methods=["GET", "POST"])
@login_required
def update(user_id):
      form = UpdateForm()
      user = User.query.get(user_id)

      if form.validate_on_submit():  # 폼 제출 및 유효성 검증
            user.user_name = form.user_name.data
            user.phone_number = form.phone_number.data
            user.birth_date = form.birth_date.data or None
            
            db.session.commit()
            # 수정 후 info 페이지로 리다이렉트
            return redirect(url_for("auth.info", user_id=user.id))  # user.id로 user_id를 전달

      return render_template("auth/update.html", user=user, form=form)

@auth.route("/<user_id>/modify_pw", methods=["GET", "POST"])
@login_required
def modify_pw(user_id):
      form = PasswordForm()
      user = User.query.get(user_id)
      if not user:
            flash("해당 사용자를 찾을 수 없습니다.")
            return redirect(url_for("auth.info", user_id=user_id))  # 이 부분에서 user_id를 제대로 전달

      if form.validate_on_submit():  # 폼 제출 및 유효성 검증
            user.password = form.current_password.data
            
            # 현재 비밀번호 확인
            if not check_password_hash(user.password_hash, form.current_password.data):
                  flash("현재 비밀번호가 일치하지 않습니다.")
                  return render_template("auth/modify_pw.html", user=user, form=form)

            # 비밀번호 업데이트
            else:
                  user.password = form.new_password.data
                  user.password_hash = generate_password_hash(form.new_password.data)

                  db.session.commit()

        # 수정 후 info 페이지로 리다이렉트
            return redirect(url_for("auth.info", user_id=user.id))  # user.id로 user_id를 전달

      return render_template("auth/modify_pw.html", user=user, form=form)

@auth.route("/users/<user_id>/register_device", methods=["GET", "POST"])
@login_required
def register_device(user_id):
    user = User.query.get(user_id)
    cameras = Camera.query.filter_by(user_id=user_id).all()
    form = DeviceForm(devices=[{'device_id': cam.device_id, 
                                'device_name':cam.device_name,
                                'ip_address_1': cam.ip_address.split('.')[0],
                                'ip_address_2': cam.ip_address.split('.')[1],
                                'ip_address_3': cam.ip_address.split('.')[2],
                                'ip_address_4': cam.ip_address.split('.')[3]} for cam in cameras])
    device_count = len(form.devices)  # 현재 장치 수 계산
    if "add_device" in request.form:
            form.devices.append_entry()
            return render_template("auth/register_device.html", form=form, user=user, device_count=device_count + 1)  # 폼 추가 후 페이지 다시 렌더링
    if "delete_device" in request.form:
            form.devices.pop_entry()
            return render_template("auth/register_device.html", form=form, user=user, device_count=device_count - 1)  # 폼 삭제 후 페이지 다시 렌더링

    if form.validate_on_submit():  # 폼 유효성 검증
      #   if "add_device" in request.form:
      #       form.devices.append_entry()
      #       return render_template("auth/register_device.html", form=form, user=user, device_count=device_count + 1)  # 폼 추가 후 페이지 다시 렌더링
      #   else:
      for device_form in form.devices:
            full_ip = device_form.get_full_ip()
            device_id = device_form.device_id.data
            device_name = device_form.device_name.data

            existing_device = Camera.query.filter_by(device_id=device_id).all()
            if existing_device and existing_device not in cameras:
                  flash(f"이미 등록된 일련번호({device_id})입니다.", "danger")
                  continue

            cam = Camera(device_id=device_id, user_id=user.id, ip_address=full_ip, device_name=device_name)
            if existing_device and existing_device in cameras:
                  existing_device.ip_address = full_ip
                  existing_device.device_id = device_id
                  existing_device.device_name = device_name
            else:
                  db.session.add(cam)

      db.session.commit()
      # flash("기기 등록이 완료되었습니다.", "success")
      return render_template("auth/register_device.html", form=form, user=user, device_count=device_count)
        
    else:
        if request.method == "POST":
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", "danger")

    return render_template("auth/register_device.html", form=form, user=user, device_count=device_count)

# 로그아웃 엔드포인트
@auth.route("/logout")
def logout():
      logout_user()
      return redirect(url_for("auth.login"))

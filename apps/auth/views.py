# apps/auth/views.py
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user, login_user, logout_user  # type: ignore
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

from apps.app import db
from apps.auth.forms import LoginForm, SignUpForm, UpdateForm, PasswordForm, DeviceForm, SingleDeviceForm
from apps.auth.models import Camera, User
from kakaotalk.auth.kakao_api import KakaoAPI

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
      
      return render_template("auth/signup.html", form=form, active_page='signup')

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
            
      return render_template("auth/login.html", form=form, active_page='login')

@auth.route("/<user_id>")
@login_required
def info(user_id):
      form = UpdateForm()
      user = User.query.get(user_id)
      
      return render_template("auth/info.html", form=form, user=user, active_page='info')

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
    user = User.query.get_or_404(user_id)
    cameras = Camera.query.filter_by(user_id=user_id).all()
    form = DeviceForm(devices=[{'device_id': cam.device_id,
                                     'device_name': cam.device_name,
                                     'ip_address_1': cam.ip_address.split('.')[0],
                                     'ip_address_2': cam.ip_address.split('.')[1],
                                     'ip_address_3': cam.ip_address.split('.')[2],
                                     'ip_address_4': cam.ip_address.split('.')[3],
                                     'camera_id': cam.camera_id} for cam in cameras])
    device_count = len(form.devices)

    if "add_device" in request.form:
        form.devices.append_entry()
        return render_template("auth/register_device.html", form=form, user=user, device_count=device_count + 1)
    if "delete_device" in request.form:
        if form.devices:
            form.devices.pop_entry()
        return render_template("auth/register_device.html", form=form, user=user, device_count=len(form.devices))

    if form.validate_on_submit():
        registered = False
        updated = False
        deleted = False
        submitted_camera_ids = set()
        for device_form in form.devices:
            full_ip = device_form.form.get_full_ip()
            device_id = device_form.form.device_id.data
            device_name = device_form.form.device_name.data
            camera_id = device_form.form.camera_id.data

            submitted_camera_ids.add(camera_id)

            existing_device = Camera.query.filter_by(camera_id=camera_id, user_id=user.id).first()

            if existing_device:
                was_updated = False
                if existing_device.ip_address != full_ip:
                    existing_device.ip_address = full_ip
                    was_updated = True
                if existing_device.device_name != device_name:
                    existing_device.device_name = device_name
                    was_updated = True
                if existing_device.device_id != device_id:
                    existing_device.device_id = device_id
                    was_updated = True
                if was_updated:
                    updated = True
            else:
                new_device = Camera(device_id=device_id, user_id=user.id, ip_address=full_ip, device_name=device_name)
                db.session.add(new_device)
                registered = True

        # 삭제된 기기 처리
        existing_camera_ids = {str(cam.camera_id) for cam in cameras}
        deleted_ids = existing_camera_ids - submitted_camera_ids

        for deleted_id_str in deleted_ids:
            if deleted_id_str.isdigit():
                camera_to_delete = Camera.query.get(int(deleted_id_str))
                if camera_to_delete and camera_to_delete.user_id == user.id:
                    db.session.delete(camera_to_delete)
                    deleted = True

        if registered is False and updated is False and deleted is False :
            flash("변경된 기기 정보가 없습니다.", "info")
        elif updated:
            db.session.commit()
            flash("기기 정보가 수정되었습니다.", "success")
        elif deleted:
            db.session.commit()
            flash("기기 정보가 삭제되었습니다.", "success")
        else:
            db.session.commit()
            flash("기기 정보가 등록되었습니다.", "success")

        return redirect(url_for('auth.register_device', user_id=user.id))

    else:
        if request.method == "POST":
            for field, errors in form.errors.items():
                for error in errors:
                    flash("")

    return render_template("auth/register_device.html", form=form, user=user, device_count=device_count)

@auth.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("로그아웃되었습니다.", "info")
    return redirect(url_for("auth.login"))
#-------------------------카카오톡---------------------------
@auth.route("/kakao/login")
def kakao_login():
    """카카오 로그인 페이지로 리다이렉트"""
    kakao_api = KakaoAPI()
    authorization_url = kakao_api.get_authorization_url()
    return redirect(authorization_url)

@auth.route("/kakao/callback")
def kakao_callback():
    """카카오 로그인 인증 후 콜백 처리"""
    kakao_api = KakaoAPI()
    code = request.args.get("code")
    if code:
        access_token = kakao_api.get_access_token(code)
        if access_token:
            user_info = kakao_api.get_user_info(access_token)
            if user_info:
                kakao_id = user_info.get('id')
                kakao_email = user_info.get('kakao_account', {}).get('email')
                kakao_nickname = user_info.get('properties', {}).get('nickname')

                if kakao_id:
                    user = User.query.filter_by(kakao_user_id=kakao_id).first()
                    if user:
                        # 기존 카카오 계정으로 가입된 사용자
                        login_user(user, remember=False)  # 자동 로그인 방지
                        flash(f"{user.nickname or user.user_name or '카카오톡'}님, 카카오 계정으로 로그인되었습니다.", "success")
                        return redirect(url_for("streaming.home"))
                    else:
                        # 새로운 카카오 계정 사용자: 회원가입 처리
                        new_user = User(
                            kakao_user_id=kakao_id,  # 카카오 고유 ID 저장
                            email=kakao_email if kakao_email else '',
                            password=None,  # 소셜 로그인은 비밀번호 없음
                            nickname=kakao_nickname,  # 필요하다면 닉네임 저장
                            social_platform='kakao',  # 소셜 로그인 플랫폼 정보 저장
                            user_name=str(kakao_id)  # 필요하다면 user_name에 임시로 카카오 id 저장 (선택 사항)
                        )
                        db.session.add(new_user)
                        db.session.commit()
                        login_user(new_user, remember=False)  # 자동 로그인 방지
                        flash(f"{new_user.nickname or new_user.user_name or '카카오톡'}님, 카카오 계정으로 회원가입 및 로그인되었습니다.", "success")
                        return redirect(url_for("streaming.home"))
                else:
                    flash("카카오 로그인 실패: 사용자 정보를 가져오지 못했습니다.", "danger")
                    return redirect(url_for("auth.login"))
            else:
                flash("카카오 로그인 실패: Access Token은 유효하지만 사용자 정보가 없습니다.", "danger")
                return redirect(url_for("auth.login"))
        else:
            flash("카카오 로그인 실패: Access Token 발급 오류", "danger")
            return redirect(url_for("auth.login"))
    else:
        flash("카카오 로그인 실패: 인가 코드 없음", "danger")
        return redirect(url_for("auth.login"))

@auth.route("/kakao/unlink", methods=["POST"])
@login_required
def kakao_unlink():
    """카카오 계정 연결 해제 처리"""
    user = current_user
    if user.social_platform == 'kakao':  # 카카오 계정으로 로그인한 사용자만 연결 해제 가능
        kakao_api = KakaoAPI()
        access_token = getattr(user, 'kakao_access_token', None)

        if access_token:
            unlink_result = kakao_api.kakao_logout(access_token)  # kakao_api의 연결 해제 함수 사용
            print(f"카카오 연결 해제 결과: {unlink_result}")
            if unlink_result.get('id') == user.kakao_user_id:
                user.kakao_access_token = None  # Access Token 삭제
                user.social_platform = None  # 소셜 플랫폼 정보 삭제
                user.kakao_user_id = None # 카카오 User ID 삭제
                db.session.commit()
                flash("카카오 계정 연결이 해제되었습니다.", "success")
            else:
                flash("카카오 계정 연결 해제에 실패했습니다.", "danger")
        else:
            flash("카카오 Access Token이 없습니다.", "warning")
    else:
        flash("카카오 계정으로 로그인한 사용자가 아닙니다.", "warning")
    return redirect(url_for("auth.info", user_id=user.id)) # 예시: 사용자 정보 페이지로 리다이렉트

# 고객지원 엔드포인트
@auth.route("/support")
def support():
     return render_template("auth/support.html", active_page='support')

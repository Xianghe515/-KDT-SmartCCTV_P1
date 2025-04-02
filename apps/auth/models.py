# 날짜 작업을 위해서 사용.
from datetime import datetime, timezone

from flask_login import UserMixin  # type:ignore
# password_hash 처리를 위한 모듈 import
from werkzeug.security import check_password_hash, generate_password_hash

# apps.app 모듈에서 db import
from apps.app import db, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "Users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary Key
    # user_id = db.Column(db.String(50), nullable=False, unique=True, index=True)
    password_hash= db.Column(db.String(255), nullable=False)
    user_name = db.Column(db.String(100), nullable=False, index=True)
    birth_date = db.Column(db.Date)
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    phone_number = db.Column(db.String(15))
    # device_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User {self.id}>"
    
    # 비밀번호를 설정하기 위한 프로퍼티
    @property
    def password(self):
        raise AttributeError("읽어 들일 수 없음")

    # 비밀번호 설정을 위한 setter
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # 비밀번호 체크
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # 이메일 주소 중복 체크
    def is_duplicate_email(self):
        duplicate_user = User.query.filter_by(email=self.email).first()
        return duplicate_user is not None and duplicate_user.id != self.id
    
    # 로그인하고 있는 사용자 정보 취득
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # # backref를 이용하여 relation 정보를 설정
    # user_images = db.relationship("UserImage", backref="user")

# Videos 모델
class Video(db.Model):
    __tablename__ = "Videos"

    video_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id", ondelete="CASCADE"))
    camera_id = db.Column(db.Integer, db.ForeignKey("Cameras.camera_id", ondelete="CASCADE"))
    filename = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.String(50))
    detected_objects = db.Column(db.String(50))
    

    def __repr__(self):
        return f"<Video {self.video_id}>"

# Logs 모델
class Log(db.Model):
    __tablename__ = "Logs"

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    action = db.Column(db.String(255))
    action_time = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Log {self.log_id}>"
    
class Camera(db.Model):
    __tablename__ = "Cameras"

    camera_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id", ondelete="CASCADE"))
    device_id = db.Column(db.String(255), nullable=False)
    device_name = db.Column(db.String(255))
    ip_address = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    def is_duplicate_device_id(self):
        duplicateDeviceId = Camera.query.filter_by(device_id=self.device_id).first()
        return duplicateDeviceId is not None and duplicateDeviceId.device_id != self.device_id
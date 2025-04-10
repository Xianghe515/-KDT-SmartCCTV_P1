from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from apps.app import db, login_manager
class User(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    password_hash = db.Column(db.String(255), nullable=True)
    user_name = db.Column(db.String(100), nullable=False, index=True)
    birth_date = db.Column(db.Date)
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    phone_number = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    nickname = db.Column(db.String(100))
    social_platform = db.Column(db.String(20))
    kakao_access_token = db.Column(db.String(255))
    kakao_user_id = db.Column(db.BigInteger, unique=True, index=True)

    def __repr__(self):
        return f"<User {self.id}>"

    @property
    def password(self):
        raise AttributeError("읽어 들일 수 없음")

    @password.setter
    def password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)    
        else:
            self.password_hash = None

    def verify_password(self, password):
        if self.password_hash and password:
            return check_password_hash(self.password_hash, password)
        return False

    def is_duplicate_email(self):
        duplicate_user = User.query.filter_by(email=self.email).first()
        return duplicate_user is not None and duplicate_user.id != self.id

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

class Video(db.Model):
    __tablename__ = "Videos"
    video_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id", ondelete="CASCADE"))
    camera_id = db.Column(db.Integer, db.ForeignKey("Cameras.camera_id", ondelete="CASCADE"))
    filename = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.String(50))
    detected_objects = db.Column(db.String(255))

    def __repr__(self):
        return f"<Video {self.video_id}>"

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
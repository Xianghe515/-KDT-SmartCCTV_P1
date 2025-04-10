from flask import Flask, current_app
from flask_login import LoginManager  # type:ignore
from flask_migrate import Migrate  # type:ignore
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect  # type:ignore
import logging
from apps.config import config
from datetime import datetime

# 로그 비활성화
log = logging.getLogger("werkzeug")
#log.disabled = True

# Flask 확장 초기화
db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = ""

def create_app(config_key="local"):  # 기본값을 "local"로 변경
    app = Flask(__name__, static_folder="server/static")

    # 앱 구성 설정
    app.config.from_object(config[config_key])

    # MySQL 연결 URI 명시적으로 설정 (기존 설정을 덮어씀)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://knockx2:knockx2@localhost/knockx2'

    app.config['SECRET_KEY'] = app.config.get('SECRET_KEY') or 'your_default_secret_key'
    # --- 카카오 REST API 키 및 Redirect URI 설정 ---
    app.config['KAKAO_REST_API_KEY'] = config[config_key].KAKAO_REST_API_KEY
    app.config['KAKAO_REDIRECT_URI'] = config[config_key].KAKAO_REDIRECT_URI
    # ------------------------------

    # Flask 확장 초기화
    csrf.init_app(app)
    db.init_app(app)
    Migrate(app, db)

    # login_manager를 애플리케이션과 연계
    login_manager.init_app(app)

    # 블루프린트 등록
    from apps.server import views as server_views
    app.register_blueprint(server_views.streaming, url_prefix="/knockx2")

    from apps.auth import views as auth_views
    app.register_blueprint(auth_views.auth, url_prefix="/auth")

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    return app

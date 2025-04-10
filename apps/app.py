from flask import Flask, current_app
from flask_login import LoginManager  # type:ignore
from flask_migrate import Migrate  # type:ignore
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect  # type:ignore
import logging
from apps.config import config


log = logging.getLogger("werkzeug")
log.disabled = True

# Flask 확장 초기화
db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = ""

def create_app(config_key):
    app = Flask(__name__, static_folder="server/static")
    
    # 앱 구성 설정
    app.config.from_object(config[config_key])
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://knockx2:knockx2@localhost/knockx2'
    
    # Flask 확장 초기화
    csrf.init_app(app)
    db.init_app(app)
    Migrate(app, db)
    
    # login_manager를 애플리케이션과 연계
    login_manager.init_app(app)  # 여기서 초기화를 활성화

    app.app_context().push()
    # 블루프린트 등록
    from apps.server import views as server_views
    app.register_blueprint(server_views.streaming, url_prefix="/knockx2")
    
    from apps.auth import views as auth_views
    app.register_blueprint(auth_views.auth, url_prefix="/auth")

    
    return app

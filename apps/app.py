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
    # app.config['SQLALCHEMY_DATABASE_URI'] = config[config_key].SQLALCHEMY_DATABASE_URI
    app.config['SECRET_KEY'] = app.config.get('SECRET_KEY')
    # --- 카카오 REST API 키 및 Redirect URI 설정 ---
    app.config['KAKAO_REST_API_KEY'] = config[config_key].KAKAO_REST_API_KEY
    app.config['KAKAO_REDIRECT_URI'] = config[config_key].KAKAO_REDIRECT_URI
    # ------------------------------

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
    
    
    #-----------------카카오 메시지 전송 함수 등록--------------------
    import requests

    def send_kakao_message(message):
        kakao_token = app.config.get('KAKAO_ACCESS_TOKEN')
        if not kakao_token:
            print("카카오 Access Token이 설정되지 않았습니다.")
            return False

        headers = {
            'Authorization': f'Bearer {kakao_token}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        data = {
            # 'template_id': 12345, # 실제 템플릿 ID로 변경 (또는 text 사용)
            # 'template_args': {
            #     'message': message
            # }
            # 텍스트 메시지 전송
            'object_type': 'text',
            'text': message,
            # 필요하다면 링크 추가
            # 'link': {
            #     'web_url': 'http://your-app.com/',
            #     'mobile_web_url': 'http://your-app.com/'
            # }
        }
        # url = 'https://kapi.kakao.com/v2/api/talk/memo/send' # 메시지 템플릿 API
        url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send' # 텍스트 메시지 API

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status() # 실패 시 HTTPError 발생
            print("카카오톡 메시지 전송 성공:", response.json())
            return True
        except requests.exceptions.RequestException as e:
            print("카카오톡 메시지 전송 실패:", e)
            if response is not None:
                print("응답 내용:", response.text)
            return False

    app.send_kakao_message = send_kakao_message
#--------------------------------------------------------------------
    
    return app

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
        print(f"Loaded Token: {kakao_token}")  # 1. 토큰 로드 확인

        if not kakao_token:
            print("카카오 Access Token이 설정되지 않았습니다.")  # 2. 토큰 없음 확인
            return False

        headers = {
            'Authorization': f'Bearer {kakao_token}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        data = {
            'object_type': 'text',
            'text': message,
        }
        url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'

        try:
            print(f"카카오톡 메시지 전송 시도 (URL: {url}, Data: {data})")  # 3. API 호출 시도 로그
            response = requests.post(url, headers=headers, data=data)
            print(f"카카오톡 API 응답 상태 코드: {response.status_code}")  # 4. 응답 상태 코드 확인
            response.raise_for_status()
            print("카카오톡 메시지 전송 성공:", response.json())  # 5. 성공 응답 확인
            return True
        except requests.exceptions.RequestException as e:
            print(f"카카오톡 메시지 전송 실패 (RequestException): {e}")  # 6. RequestException 발생
            if response is not None:
                print("응답 내용:", response.text)  # 7. 응답 내용 확인
            return False
        except Exception as e:
            print(f"카카오톡 메시지 전송 실패 (Unexpected Error): {e}")  # 8. 예상치 못한 오류 발생
            return False

    app.send_kakao_message = send_kakao_message
#--------------------------------------------------------------------
    
    return app

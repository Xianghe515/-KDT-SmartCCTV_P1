from pathlib import Path

baseDir = Path(__file__).parent

# BaseConfig 클래스 작성
class BaseConfig:
    SECRET_KEY = "dVmWZSOfLUdq4Hs0n1E1"
    WTF_CSRF_SECRET_KEY = "dVmWZSOfLUdq4Hs0n1E2"
    KAKAO_REST_API_KEY = '7d85993f53075a334012da8b7b2cfdc0'
    KAKAO_REDIRECT_URI = 'http://localhost:5000/auth/kakao/callback' # 개발 환경에 맞게 수정

# BaseConfig 클래스를 상속하여 LocalConfig 클래스를 작성
class LocalConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{baseDir / 'local.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SQLALCHEMY_ECHO=True
    # KAKAO_REST_API_KEY = '7d85993f53075a334012da8b7b2cfdc0'
    # KAKAO_REDIRECT_URI = 'http://localhost:5000/auth/kakao/callback' # 개발 환경에 맞게 수정
      
# BaseConfig 클래스를 상속하여 TestingConfig 클래스를 작성
class TestingConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{baseDir / 'testing.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    WTF_CSRF_ENABLED = False

# 실제 상황
class DeployConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{baseDir / 'deploy.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS=False

# config 사전 매핑 작업
config = {
    "testing": TestingConfig,
    "local": LocalConfig,
    "deploy": DeployConfig
}
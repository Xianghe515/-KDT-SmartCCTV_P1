from pathlib import Path

baseDir = Path(__file__).parent

# BaseConfig 클래스 작성
class BaseConfig:
      SECRET_KEY = "dVmWZSOfLUdq4Hs0n1E1"
      WTF_CSRF_SECRET_KEY = "dVmWZSOfLUdq4Hs0n1E2"

# BaseConfig 클래스를 상속하여 LocalConfig 클래스를 작성
class LocalConfig(BaseConfig):
      SQLALCHEMY_DATABASE_URI=f"sqlite:///{baseDir / 'local.sqlite'}"
      SQLALCHEMY_TRACK_MODIFICATIONS=False
      SQLALCHEMY_ECHO=True
      
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
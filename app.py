from flask import Flask

from server.views import streaming

app = Flask(__name__, static_folder="server/static", template_folder="server/templates")
app.register_blueprint(streaming, url_prefix="/knockx2")      # 블루프린트 등록

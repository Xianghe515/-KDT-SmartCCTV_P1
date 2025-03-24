import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import cv2 as cv

# 영상정보를 보여줄 웹 페이지
PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""


# 스트리밍 핸들러 클래스
class StreamingHandler(server.BaseHTTPRequestHandler):

    camera = Picamera2()
    config = camera.create_preview_configuration(
        main={"format": "XRGB8888", "size": (640, 480)},
        # colour_space=libcamera.ColorSpace.Rec2020(),
    )
    camera.configure(config)
    camera.start()

    # GET인 경우 동작작
    def do_GET(self):
        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif self.path == "/index.html":
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Age", 0)
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type", "multipart/x-mixed-replace; boundary=FRAME"
            )
            self.end_headers()
            try:
                while True:
                    frame = self.camera.capture_buffer()
                    frame = cv.imdecode(frame, cv.IMREAD_COLOR)
                    # print(frame, frame.shape, type(frame))
                    ret, buffer = cv.imencode(".jpg", frame)
                    frame = buffer.tobytes()
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except Exception as e:
                logging.warning(
                    "Removed streaming client %s: %s", self.client_address, str(e)
                )
        else:
            self.send_error(404)
            self.end_headers()

    # POST로 요청이 들어온 경우 동작
    def do_POST(self):
        print("POST 요청을 받았습니다.")


# 스트리밍 서버 클래스 선언
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


try:
    # address에 호스트(ip)와 포트 정보를 생성
    address = ("", 8000)
    # StreamingServer에 위의 address와 StreamingHandler 클래스를 인자로 넘겨 서버 생성
    server = StreamingServer(address, StreamingHandler)
    print("Ctrl + c 입력시 서버 종료")
    # 서버를 시작
    server.serve_forever()

# Ctrl+C로 서버 종료시 예외처리
except KeyboardInterrupt:
    print("서버를 종료합니다.")
    # 서버 종료시 예외처리
    server.shutdown()
# finally:
# picam2 중지
# picam2.stop_recording()

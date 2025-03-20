#!/usr/bin/python3

# Mostly copied from https://picamera.readthedocs.io/en/release-1.13/recipes2.html
# Run this script, then point a web browser at http:<this-ip-address>:8000
# Note: needs simplejpeg to be installed (pip3 install simplejpeg).

# 이와 같은 방식으로 opencv를 이용한 이유는 직접적인 카메라의 접근이 어려운 환경에서 opencv에서 Remote Camera를 이용하여 접근하는 방법을 
# 이용하여 opencv를 이용하는 방법을 구현하기 위해서 작업 함.

import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

PAGE = """
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</tml>
"""

# 스트리밍 출력 클래스
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# 스트리밍 핸들러 클래스
class StreamingHandler(server.BaseHTTPRequestHandler):
    # GET인 경우 동작작
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')       # 영상 데이터 - boundary로 구분
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()
    # POST로 요청이 들어온 경우 동작
    def do_POST(self):
        print('Request Post.')

# 스트리밍 서버 클래스 선언
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# picamera2를 이용한 영상 접속 설정
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
# JpegEncoder()를 이용한 영상 출력 설정(jpeg 방식으로 인코딩)
# FileOutput()을 이용한 영상 출력 설정(파일로 출력)
# output은 스트리밍 출력 클래스의 인스턴스
picam2.start_recording(JpegEncoder(), FileOutput(output))

try:
    # address에 호스트(ip)와 포트 정보를 생성
    address = ('', 8000)
    # StreamingServer에 위의 address와 StreamingHandler 클래스를 인자로 넘겨 서버 생성
    server = StreamingServer(address, StreamingHandler)
    print("Ctrl + c - stop server")
    # 서버를 시작
    server.serve_forever()
    
# Ctrl+C로 서버 종료시 예외처리
except KeyboardInterrupt:
    print('stop server.')
    # 서버 종료시 예외처리
    server.shutdown()
finally:
    # picam2 중지
    picam2.stop_recording()
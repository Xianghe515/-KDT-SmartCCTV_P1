import logging
import socketserver
from http import server
import cv2 as cv
import sys

PAGE = """
<html>
<head>
<title>MJPEG Streaming Demo</title>
</head>
<body>
<h1>MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""

# 스트리밍 핸들러 클래스
class StreamingHandler(server.BaseHTTPRequestHandler):
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
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        print('프레임 획득 실패')
                        break

                    # 프레임 리사이즈

                    # 프레임을 JPEG 형식으로 인코딩
                    success, encoded_frame = cv.imencode('.jpg', frame)
                    if not success:
                        print('이미지 인코딩 실패')
                        continue

                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(encoded_frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning('Streaming client disconnected: %s', str(e))
        else:
            self.send_error(404)
            self.end_headers()

# 스트리밍 서버 클래스
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# 웹캠 연결
cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)


if not cap.isOpened():
    sys.exit('카메라 연결 실패')

try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    print("Ctrl + c - stop server")
    server.serve_forever()
# Ctrl+C로 서버 종료시 예외처리
except KeyboardInterrupt:
    print('stop server.')
    # 서버 종료시 예외처리
    server.shutdown()
finally:
    cap.release()
    cv.destroyAllWindows()

import logging
import socketserver
from http import server
import cv2 as cv
import sys

cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
if not cap.isOpened():
    sys.exit('카메라 연결 실패')

class StreamingHandler(server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        print('프레임 획득 실패')
                        break
                    success, encoded_frame = cv.imencode('.jpg', frame)
                    if not success:
                        print('이미지 인코딩 실패')
                        continue

                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(encoded_frame)))
                    self.end_headers()
                    self.wfile.write(encoded_frame.tobytes())
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning('Streaming client disconnected: %s', str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

try:
    address=('', 8000)
    server = StreamingServer(address, StreamingHandler)
    print("Ctrl + c - stop server")
    server.serve_forever()
except KeyboardInterrupt:
    print('stop server')
    server.shutdown()
finally:
    cap.release()
    cv.destroyAllWindows()
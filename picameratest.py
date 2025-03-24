from picamera2 import Picamera2, Preview
picam2 = Picamera2()
config = picam2.create_preview_configuration({"format": "MJPEG"})
picam2.configure(config)
picam2.start_preview(Preview.QT)
picam2.start()
jpeg_buffer = picam2.capture_buffer()
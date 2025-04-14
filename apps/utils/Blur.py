from ultralytics import YOLO
import cv2 as cv
import numpy as np
import cv2 as cv


class Blur:
    @staticmethod
    def apply_blur_to_video(input_path, output_path):
        try:
            model = YOLO("./yolo11/yolo11n_ncnn_model")
            print("YOLO 모델 로드 성공")
        except Exception as e:
            print(f"YOLO 모델 로드 실패: {str(e)}")
            return False

        cap = cv.VideoCapture(input_path)
        if not cap.isOpened():
            print("영상 열기 실패")
            return False

        width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv.CAP_PROP_FPS)

        fourcc = cv.VideoWriter_fourcc(*'mp4v')
        out = cv.VideoWriter(output_path, fourcc, fps, (width, height))

        colors = np.random.uniform(0, 255, size=(len(model.names), 3))
        target_class_indices = [0]
        BLUR_RADIUS = 31

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].item()
                    cls = box.cls[0].item()
                    class_index = int(cls)

                    if class_index in target_class_indices and conf >= 0.4:
                        roi = frame[int(y1):int(y2), int(x1):int(x2)]
                        if roi.size != 0:
                            blurred = cv.GaussianBlur(roi, (BLUR_RADIUS, BLUR_RADIUS), 0)
                            frame[int(y1):int(y2), int(x1):int(x2)] = blurred

            out.write(frame)

        cap.release()
        out.release()
        print(f"블러 처리 완료: {output_path}")
        return True

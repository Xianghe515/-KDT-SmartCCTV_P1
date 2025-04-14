from ultralytics import YOLO

# Load a COCO-pretrained YOLO11n model
model = YOLO("yolo11n.pt")
model.export(format="ncnn")
ncnn_model=YOLO("./yolo1n_ncnn_model")
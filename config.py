# Camera config
CAMERA_IP1 = "10.25.78.240"
CAMERA_IP="192.168.8.12"
USERNAME = "admin"
PASSWORD = "@dmin123"
RTSP_URL = f"rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554/Streaming/Channels/101/"
USE_GSTREAMER = False

# YOLO Model
# MODEL_PATH = "C:/Users/azmat.ali/PPE_detection_YOLO/YOLO-Weights/ppe.pt"
MODEL_PATH="c:/interdata/COMIPLE/connect/yolov8n.pt"
# MODEL_PATH="C:/interdata/Models/New_folder/runs/detect/train7/weights/best.pt"
# Reconnection settings
RECONNECT_INITIAL_DELAY = 1.0
RECONNECT_MAX_DELAY = 8.0
READ_TIMEOUT = 5.0

# JPEG quality
JPEG_QUALITY = 80

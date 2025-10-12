import time
import threading
import cv2
from config import REQUIRED_CLASSES, ALERT_COOLDOWN_SEC
from models.yolo_model import model
from controllers.camera_controller import frame_lock, latest_raw, adaptive_infer_interval

# === Locks and globals ===
alert_lock = threading.Lock()
stats_lock = threading.Lock()
running = True

latest_annotated = None
last_annotated_ts = 0.0
inference_fps = 0.0

alert_flag = False
last_alert_ts = 0.0

def yolo_worker():
    """Thread: Run YOLO inference on frames with adaptive interval."""
    global latest_raw, latest_annotated, last_annotated_ts, inference_fps
    global alert_flag, last_alert_ts

    ema_alpha = 0.1
    frame_counter = 0

    while running:
        interval, _ = adaptive_infer_interval()
        frame_counter = (frame_counter + 1) % interval

        with frame_lock:
            frame = None if latest_raw is None else latest_raw.copy()

        if frame is None:
            # time.sleep(0.01)
            continue

        if frame_counter != 0:
            # time.sleep(0.003)
            continue

        t0 = time.time()
        try:
            h, w = frame.shape[:2]
            scale = 720.0 / max(h, w)
            if scale < 1.0:
                frame_in = cv2.resize(frame, (int(w * scale), int(h * scale)))
            else:
                frame_in = frame

            # Run YOLO
            results = model(frame_in, imgsz=720, verbose=False)
            r = results[0]

            # Collect classes
            present = set()
            if r.boxes is not None and len(r.boxes) > 0:
                for b in r.boxes:
                    cls_id = int(b.cls)
                    label = r.names.get(cls_id, str(cls_id))
                    present.add(label)

            # Decide alert
            now = time.time()
            should_alert = REQUIRED_CLASSES.issubset(present)
            with alert_lock:
                if should_alert and (now - last_alert_ts) >= ALERT_COOLDOWN_SEC:
                    alert_flag = True
                    last_alert_ts = now
                else:
                    alert_flag = False

            # Annotated frame
            annotated = r.plot()
            if annotated.shape[0] != h or annotated.shape[1] != w:
                annotated = cv2.resize(annotated, (w, h))

            with frame_lock:
                latest_annotated = annotated
                last_annotated_ts = time.time()

            # FPS update
            dt = time.time() - t0
            if dt > 0:
                fps = 1.0 / dt
                inference_fps = (1 - ema_alpha) * inference_fps + ema_alpha * fps

        except Exception as e:
            print("Inference error:", e)
            # time.sleep(0.01)

def start_inference_thread():
    """Start YOLO inference thread."""
    t = threading.Thread(target=yolo_worker, daemon=True)
    t.start()

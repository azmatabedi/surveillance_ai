import time
import cv2
from controllers.camera_controller import frame_lock, latest_raw
from controllers.inference_controller import latest_annotated
from config import JPEG_QUALITY

served_fps = 0.0

def jpeg_bytes(image):
    """Convert frame to JPEG bytes."""
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    ok, buf = cv2.imencode(".jpg", image, encode_params)
    if not ok:
        ok, buf = cv2.imencode(".jpg", image)
    return buf.tobytes()

def stream_generator(src):
    """Stream frames as MJPEG to Flask route."""
    global served_fps
    ema_alpha = 0.1
    from controllers.camera_controller import ensure_threads
    ensure_threads(src)

    last_send = time.time()
    while True:
        with frame_lock:
            frame = latest_annotated if latest_annotated is not None else latest_raw

        if frame is None:
            # time.sleep(0.01)
            continue

        out = jpeg_bytes(frame)
        now = time.time()
        dt = now - last_send
        last_send = now
        if dt > 0:
            fps = 1.0 / dt
            served_fps = (1 - ema_alpha) * served_fps + ema_alpha * fps

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + out + b"\r\n")

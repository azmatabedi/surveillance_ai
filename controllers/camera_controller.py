import cv2
import time
import threading
import numpy as np
from queue import Queue, Empty
from config import RTSP_URL, MOTION_SENSITIVITY, DGIM_WINDOW
from controllers.dgim import DGIM
import cv2
import os
import datetime
# === Locks and globals ===
cap_lock = threading.Lock()
frame_lock = threading.Lock()

cap = None
running = False
latest_raw = None
capture_fps = 0.0
frame_queue = Queue(maxsize=3)

dgim = DGIM(DGIM_WINDOW)

cap = None
cap_lock = threading.Lock()

def open_capture(src="rtsp"):
    """Open camera capture (RTSP or webcam)."""
    global cap
    with cap_lock:
        if cap is not None:
            cap.release()
            cap = None
        
        if src == "rtsp":
            cap = cv2.VideoCapture(RTSP_URL)
        else:
            cap = cv2.VideoCapture(0)  # webcam
        
        if not cap.isOpened():
            print("❌ Failed to open camera source:", src)
            cap = None
        else:
            print("✅ Camera opened:", src)

def adaptive_infer_interval(min_interval=1, max_interval=12):
    """Adaptive interval based on motion density using DGIM."""
    motion_density = dgim.density(min(128, DGIM_WINDOW))
    interval = int(round(max_interval - (max_interval - min_interval) * motion_density))
    interval = max(min_interval, min(max_interval, interval))
    return interval, motion_density

def frame_grabber():
    """Thread: grab frames, compute motion, update DGIM, maintain FPS."""
    global latest_raw, capture_fps, running, cap
    ema_alpha = 0.1
    last_ts = time.time()
    prev_gray = None
    fail_count = 0
    max_failures = 20

    while running:
        with cap_lock:
            local_cap = cap

        if local_cap is None:
            # time.sleep(0.2)
            continue

        ok, frame = local_cap.read()
        now = time.time()

        if not ok or frame is None:
            fail_count += 1
            print(f"⚠️ Frame grab failed ({fail_count}/{max_failures})")
            # time.sleep(0.1)
            if fail_count >= max_failures:
                print("🔄 Camera disconnected. Reconnecting...")
                open_capture("rtsp")
                fail_count = 0
            continue
        else:
            fail_count = 0

        # FPS
        dt = now - last_ts
        last_ts = now
        if dt > 0:
            fps = 1.0 / dt
            capture_fps = (1 - ema_alpha) * capture_fps + ema_alpha * fps

        # Motion detection
        small = cv2.resize(frame, (160, 90))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if prev_gray is None:
            motion_bit = 0
        else:
            diff = cv2.absdiff(gray, prev_gray)
            motion_metric = float(np.mean(diff))
            motion_bit = 1 if motion_metric >= MOTION_SENSITIVITY else 0
        prev_gray = gray

        dgim.update(motion_bit)

        # Save latest raw frame
        with frame_lock:
            latest_raw = frame

        # Maintain frame queue
        if not frame_queue.full():
            frame_queue.put(frame.copy())
        else:
            try:
                frame_queue.get_nowait()
            except Empty:
                pass
            frame_queue.put(frame.copy())

def ensure_threads(src):
    """Ensure camera + grabber threads are running."""
    global running
    if running:
        return
    open_capture(src)
    running = True
    grabber_thread = threading.Thread(target=frame_grabber, daemon=True)
    grabber_thread.start()




# ... other imports ...


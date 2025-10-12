from flask import Flask, Response, render_template_string, jsonify
import cv2
import threading
import time
import traceback
from ultralytics import YOLO

# === CONFIG ===
CAMERA_IP ="192.168.8.12"#"192.168.8.12"# "10.25.78.240"
USERNAME = "admin"
PASSWORD = "@dmin123"
RTSP_URL = f"rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554/Streaming/Channels/101/"
RTSP2_URL = f"rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554/Streaming/Channels/101/"
MODEL_PATH = "C:/Users/azmat.ali/PPE_detection_YOLO/YOLO-Weights/ppe.pt"

# Optional: set to True if your OpenCV has GStreamer and you'd like lower-latency pipeline
USE_GSTREAMER = False

# Camera reconnect/backoff settings
RECONNECT_INITIAL_DELAY = 1.0   # seconds
RECONNECT_MAX_DELAY = 8.0       # seconds
READ_TIMEOUT = 5.0              # seconds without successful read -> force reconnect

# JPEG quality for streaming
JPEG_QUALITY = 80


class CameraThread:
    def __init__(self, src=RTSP_URL, use_gstreamer=USE_GSTREAMER):
        self.src = src
        self.use_gstreamer = use_gstreamer
        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        self.last_success_ts = 0.0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _open_capture(self):
        # If GStreamer desired, construct a pipeline (requires OpenCV with GStreamer)
        if self.use_gstreamer:
            gst = (f"rtspsrc location={self.src} latency=0 ! "
                   "rtpjitterbuffer ! rtph264depay ! h264parse ! avdec_h264 ! "
                   "videoconvert ! appsink")
            cap = cv2.VideoCapture(gst, cv2.CAP_GSTREAMER)
        else:
            # Use TCP transport to be slightly more robust
            cap = cv2.VideoCapture(f"{self.src}?rtsp_transport=tcp")
        return cap

    def _run(self):
        backoff = RECONNECT_INITIAL_DELAY
        while self.running:
            try:
                # Ensure capture is opened
                if self.cap is None or not self.cap.isOpened():
                    print(f"[CameraThread] Opening capture: {self.src}")
                    if self.cap is not None:
                        try:
                            self.cap.release()
                        except Exception:
                            pass
                        self.cap = None

                    self.cap = self._open_capture()
                    open_ok = (self.cap is not None and self.cap.isOpened())
                    if not open_ok:
                        print(f"[CameraThread] Failed to open capture. Backoff {backoff}s")
                        # time.sleep(backoff)
                        backoff = min(backoff * 2, RECONNECT_MAX_DELAY)
                        continue
                    else:
                        print("[CameraThread] Capture opened")
                        backoff = RECONNECT_INITIAL_DELAY

                # Read loop
                ret, frame = self.cap.read()
                now = time.time()
                if not ret or frame is None:
                    elapsed_since_success = now - self.last_success_ts if self.last_success_ts else None
                    print("[CameraThread] Frame read failed. Retrying...")
                    # time.sleep(0.1)
                    if (self.last_success_ts == 0.0) or (
                        elapsed_since_success is not None and elapsed_since_success > READ_TIMEOUT
                    ):
                        print("[CameraThread] Too long without valid frames, reconnecting...")
                        try:
                            self.cap.release()
                        except Exception:
                            pass
                        self.cap = None
                        # time.sleep(backoff)
                        backoff = min(backoff * 2, RECONNECT_MAX_DELAY)
                    continue

                # Successful read
                with self.lock:
                    self.frame = frame.copy()
                self.last_success_ts = now

                # time.sleep(0.005)

            except Exception as ex:
                print("[CameraThread] Exception in camera thread:", ex)
                traceback.print_exc()
                try:
                    if self.cap is not None:
                        self.cap.release()
                except Exception:
                    pass
                self.cap = None
                # time.sleep(backoff)
                backoff = min(backoff * 2, RECONNECT_MAX_DELAY)

        # cleanup on stop
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        print("[CameraThread] Exited")

    def get_frame(self):
        with self.lock:
            if self.frame is None:
                print("do not get the frame")
                return None
            return self.frame.copy()

    def stop(self):
        self.running = False
        self._thread.join(timeout=2.0)

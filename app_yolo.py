from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
from detection.yolo_detector import run_yolo_on_frame  # put your code in yolo_module.py

app = Flask(__name__)

@app.route("/")
def home():
    return {"status": "YOLO Server Running 🚀"}

@app.route("/predict/frame", methods=["POST"])
def predict_frame():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        npimg = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        annotated, stats = run_yolo_on_frame(frame)

        # ✅ Encode annotated frame back to base64 so frontend can render it
        _, buffer = cv2.imencode(".jpg", annotated)
        encoded_frame = base64.b64encode(buffer).decode("utf-8")

        response = {
            "stats": {
                "person_count": stats.get("person_count"),
                "violations": stats.get("violations"),
                "images": stats.get("images"),
                "global_alert": stats.get("global_alert"),
            },
            "frame": encoded_frame  # frontend can display this image
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)

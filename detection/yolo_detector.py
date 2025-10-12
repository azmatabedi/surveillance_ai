import cv2
import traceback
from ultralytics import YOLO
from config import MODEL_PATH
import numpy as np

# ✅ Define the classes you want to detect
ALLOWED_CLASSES = ["person"]

print("Loading YOLO model from:", MODEL_PATH)
model = YOLO(MODEL_PATH)

# === Define Restricted Polygon (quadrilateral area) ===
RESTRICTED_POLYGON = np.array([
    [500, 900],     # top-left
    [1000, 900],    # top-right
    [1000, 1300],   # bottom-right
    [500, 1300]     # bottom-left
], np.int32)

IOU_THRESHOLD = 0.01  # 🚨 adjust as needed


def draw_restricted_area(frame):
    """Always highlight the restricted polygon area (light overlay)."""
    overlay = frame.copy()
    cv2.fillPoly(overlay, [RESTRICTED_POLYGON], (0, 0, 255))  # red fill
    cv2.polylines(overlay, [RESTRICTED_POLYGON], isClosed=True,
                  color=(255, 255, 0), thickness=3)
    return cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)


def polygon_area(polygon: np.ndarray) -> float:
    """Compute polygon area using contourArea."""
    return cv2.contourArea(polygon)


def compute_iou(bbox, polygon):
    """
    Compute IOU between bbox (x1,y1,x2,y2) and polygon.
    """
    x1, y1, x2, y2 = bbox
    # bbox polygon
    bbox_poly = np.array([
        [x1, y1],
        [x2, y1],
        [x2, y2],
        [x1, y2]
    ], np.int32)

    # intersection polygon
    retval, inter_pts = cv2.intersectConvexConvex(
        bbox_poly.astype(np.float32),
        polygon.astype(np.float32)
    )

    if inter_pts is None or retval <= 0:
        return 0.0

    inter_area = cv2.contourArea(inter_pts)
    if inter_area <= 0:
        return 0.0

    # union = sum - intersection
    bbox_area = polygon_area(bbox_poly)
    poly_area = polygon_area(polygon)
    union = bbox_area + poly_area - inter_area

    return inter_area / union if union > 0 else 0.0


def run_yolo_on_frame(frame):
    """
    Runs YOLO on frame and returns:
    - annotated frame (for video feed)
    - stats dict: {person_count, violations: [list of violators]}
    """
    try:
        results = model(frame, imgsz=640, verbose=False)
        r = results[0]
        annotated = frame.copy()
        violations = []
        person_count = 0

        # Always draw restricted area on frame
        annotated = draw_restricted_area(annotated)

        for box in getattr(r, "boxes", []):
            try:
                cls = int(box.cls if not hasattr(box.cls, "__len__") else box.cls[0])
                conf = float(box.conf if not hasattr(box.conf, "__len__") else box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                label = r.names.get(cls, str(cls))
                if label not in ALLOWED_CLASSES:
                    continue  

                person_count += 1
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                # ✅ IOU check with restricted polygon
                iou = compute_iou((x1, y1, x2, y2), RESTRICTED_POLYGON)
                inside = iou >= IOU_THRESHOLD

                # Draw bounding box + center
                color = (0, 0, 255) if inside else (0, 255, 0)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.circle(annotated, (cx, cy), 5, color, -1)
                # if inside is True :
                if iou>=0.010:
                    violations.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": round(conf, 2),
                        "iou": iou*100,
                        "center": [cx, cy],
                        "alert": inside   # 🚨 True if inside, False otherwise
                    })

            except Exception:
                continue

        # stats = {
        #     "person_count": person_count,
        #     "violations": len(violations) ,
        #     "images":violations,
        #     # "Objects":violations,
        #     "global_alert": any(v["alert"] for v in violations), # 🚨 overall alert flag
        #     "frame":annotated
        # }
        stats = {
            "person_count": person_count,
            "violations": len(violations) if len(violations) > 0 else 0,
            "images": violations if len(violations) > 0 else [],
            "global_alert": any(v["alert"] for v in violations) if len(violations) > 0 else False,
            "frame": annotated
        }


        # print(stats.get("violations"))
        return annotated, stats

    except Exception as e:
        print("[run_yolo_on_frame] Error:", e)
        traceback.print_exc()
        return frame, {"person_count": 0, "violations": [], "global_alert": False}
# Assuming you've loaded a smaller model like yolov8n.pt
# model = YOLO("yolov8n.pt")
# Assuming you've loaded a smaller model like yolov8n.pt
# model = YOLO("yolov8n.pt")

# def run_yolo_on_frame(frame, frame_number):
#     """
#     Runs YOLO on frame with CPU optimizations.
#     """
#     if frame_number % 3 != 0:
#         return frame, {"person_count": 0, "violations": 0, "global_alert": False}

#     try:
#         results = model(frame, imgsz=416, verbose=False)
#         r = results[0]
        
#         annotated = frame.copy()
#         violations_list = []
#         person_count = 0

#         annotated = draw_restricted_area(annotated)

#         for box in getattr(r, "boxes", []):
#             try:
#                 # This is the line that was missing. It unpacks the coordinates.
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])

#                 label = r.names.get(int(box.cls), str(int(box.cls)))
#                 if label not in ALLOWED_CLASSES:
#                     continue 
                
#                 person_count += 1
#                 cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

#                 iou = compute_iou((x1, y1, x2, y2), RESTRICTED_POLYGON)
#                 inside = iou >= IOU_THRESHOLD

#                 if iou >= 0.010:
#                     violations_list.append({
#                         "bbox": [x1, y1, x2, y2],
#                         "confidence": round(float(box.conf), 2),
#                         "iou": iou * 100,
#                         "center": [cx, cy],
#                         "alert": inside
#                     })
                
#             except Exception as e:
#                 print(f"Error processing a bounding box: {e}")
#                 continue

#         stats = {
#             "person_count": person_count,
#             "violations": len(violations_list),
#             "global_alert": any(v["alert"] for v in violations_list)
#         }

#         return annotated, stats

#     except Exception as e:
#         print(f"Error processing frame: {e}")
#         return frame, {"person_count": 0, "violations": 0, "global_alert": False}
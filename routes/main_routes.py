# from flask import Blueprint, render_template, Response, jsonify
# import json
# from detection.yolo_detector import run_yolo_on_frame
# from utils.helpers import *
# import time
# import threading
# from config import READ_TIMEOUT
import sys
import os
BASE_DIR_PATH = os.getcwd()
import requests

sys.path.append(BASE_DIR_PATH)
from  utils.helpers import *
from flask import Flask, render_template_string, url_for


# def create_routes(camera_thread):
#     bp = Blueprint("main", __name__)

#     bp.config['MYSQL_HOST'] = '10.25.81.228'
#     bp.config['MYSQL_USER'] = 'root'
#     bp.config['MYSQL_PASSWORD'] = 'Azm123at@1'  # Enter your MySql password 
#     bp.config['MYSQL_DB'] = 'surveillance'


#     latest_stats = {"person_count": 0, "violations": 0,"global_alert":False}

#     def generate_frames():
#         nonlocal latest_stats
#         while True:
#             frame = camera_thread.get_frame()
#             if frame is None:
#                 continue

#             annotated, stats = run_yolo_on_frame(frame)  # stats should return dict: {"person_count": x, "violations": [...]}
#             latest_stats = stats  # keep most recent stats

#             jpg = encode_jpeg(annotated)
#             # jpg = encode_jpeg(frame)
#             if not jpg:
#                 continue
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')

#     @bp.route("/")
#     def index():
#         return render_template("index.html")

#     @bp.route("/video_feed")
#     def video_feed():
#         return Response(generate_frames(),
#                         mimetype="multipart/x-mixed-replace; boundary=frame")

#     @bp.route("/health")
#     def health():
#         connected = False
#         last = camera_thread.last_success_ts
#         if last and (time.time() - last) < (READ_TIMEOUT + 2.0):
#             connected = True
#         return jsonify({"status": "running",
#                         "camera_connected": connected,
#                         "last_frame_ts": last})

#     # NEW ENDPOINT: Get latest person count
#     @bp.route("/person_count")
#     def person_count():
#         return jsonify({"person_count": latest_stats.get("person_count", 0)})

#     # NEW ENDPOINT: Get violations (who entered restricted area)
#     @bp.route("/violations")
#     def violations():
#         return jsonify({"violations": latest_stats.get("violations", 0)})
    
#     @bp.route("/global_alert")
#     def global_alert():
#         return jsonify({"global_alert": latest_stats.get("global_alert", 0)})
    

#     @bp.route('/Objects')
#     def objects():
#         return jsonify({"Objects":latest_stats.get('Objects',0)})
    

#     alert_flag = False
#     alert_lock = threading.Lock()

#     @bp.route("/alert")
#     def alert():
#         def gen():
#             # Simple SSE: emits "ALERT" once per event, else "OK"
#             prev_sent_alert = False
#             while True:
#                 with alert_lock:
#                     flag = alert_flag

#                 # ✅ Safe access: if "violations" missing, use []
#                 violations = latest_stats.get("violations", [])
#                 person_count = latest_stats.get("person_count", 0)
#                 # print(type(violations))
#                 if violations > 0:
#                     data = {"status": 'ALERT', "violations": violations, "person_count": person_count}
#                     prev_sent_alert = True
#                 else:
#                     data = {"status": 'OK', "violations": violations, "person_count": person_count}
#                     prev_sent_alert = False
#                 # if violations > 0:
#                 #     yield 'data: ALERT\n\n'
#                 #     prev_sent_alert = True
#                 # else:
#                 #     yield 'data: OK\n\n'
#                 #     prev_sent_alert = False
#                 yield f"data: {json.dumps(data)}\n\n"

#                 time.sleep(0.7)

#         return Response(gen(), mimetype="text/event-stream")
#     @bp.route('/login', methods=['GET', 'POST'])
#     def login():
#         msg = ''
#         if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
#             username = request.form['username']
#             password = request.form['password']
#             cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#             cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
#             account = cursor.fetchone()
#             if account:
#                 session['loggedin'] = True
#                 session['id'] = '12'#account['id']
#                 session['username'] ='Azmat' #account['username']
#                 return render_template('index.html', msg='Logged in successfully!')
#             else:
#                 msg = 'Incorrect username/password!'

#     return bp
# --------------------------------------------------------------
# main_routes.py
# --------------------------------------------------------------
# --------------------------------------------------------------
# routes/main_routes.py
# --------------------------------------------------------------
from flask import (
    Blueprint,
    current_app,
    render_template,
    Response,
    jsonify,
    request,
    session,
)
import json
import time
import threading

# Your own modules
from detection.yolo_detector import run_yolo_on_frame
from utils.helpers import *
from config import READ_TIMEOUT,CAMERA_IP


# ----------------------------------------------------------------
# Blueprint factory
# ----------------------------------------------------------------
def create_routes(camera_thread):
    engine = get_engine()
    """Return a Blueprint that contains all routes for the web UI."""
    bp = Blueprint("main", __name__)

    # --------------------------------------------------------------
    # **DO NOT** try to set bp.config here – the app holds the config.
    # --------------------------------------------------------------

    # ----------------------------------------------------------------
    # Shared mutable state (updated by the generator thread)
    # ----------------------------------------------------------------
    latest_stats = {
        "person_count": 0,
        "violations": 0,      # list of violation descriptions
        "global_alert": False,
        "Objects": [],         # whatever you use for generic objects
    }

    # ----------------------------------------------------------------
    # Helper: infinite MJPEG generator
    # ----------------------------------------------------------------
    def generate_frames():
        nonlocal latest_stats
        frame_number = 0  # Initialize the frame counter
        
        while True:
            frame = camera_thread.get_frame()
            if frame is None:
                continue
            
            # Pass the frame_number to your processing function
            # annotated, stats = run_yolo_on_frame(frame, frame_number)
            # annotated, stats = run_yolo_on_frame(frame)
            # latest_stats = stats
            
            jpg = encode_jpeg(frame)
            if not jpg:
                continue
                
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
            )
            
            frame_number += 1  # Increment the counter for the next frame


    # PREDICTION_SERVER = "http://10.25.81.228:5003/predict/frame"

    # def generate_frames():
    #     global latest_stats
    #     frame_number = 0  

    #     while True:
    #         frame = camera_thread.get_frame()
    #         if frame is None:
    #             continue

    #         # Convert frame to JPEG for sending
    #         _, buffer = cv2.imencode(".jpg", frame)
    #         files = {"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")}

    #         try:
    #             # 🔥 Send frame to prediction server
    #             response = requests.post(PREDICTION_SERVER, files=files, timeout=5)
    #             if response.status_code != 200:
    #                 continue

    #             data = response.json()
    #             latest_stats = data["stats"]

    #             # Decode annotated frame from base64
    #             annotated_bytes = base64.b64decode(data["frame"])
    #             annotated = cv2.imdecode(np.frombuffer(annotated_bytes, np.uint8), cv2.IMREAD_COLOR)

    #             # Convert annotated frame to JPEG for streaming
    #             _, jpg = cv2.imencode(".jpg", annotated)
    #             if not jpg:
    #                 continue

    #             yield (
    #                 b"--frame\r\n"
    #                 b"Content-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
    #             )

    #         except Exception as e:
    #             print("[generate_frames] Error:", e)
    #             continue

    #         frame_number += 1

    # ----------------------------------------------------------------
    # Routes
    # ----------------------------------------------------------------
    @bp.route("/")
    def index():
        return render_template("index.html")

    @bp.route("/video_feed")
    def video_feed():
        """Stream the MJPEG video."""
        return Response(
            generate_frames(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    @bp.route("/health")
    def health():
        """Simple health‑check endpoint used by uptime monitors."""
        connected = False
        last = getattr(camera_thread, "last_success_ts", None)
        if last and (time.time() - last) < (READ_TIMEOUT + 2.0):
            connected = True

        return jsonify(
            {
                "status": "running",
                "camera_connected": connected,
                "last_frame_ts": last,
            }
        )

    # ----------------------------------------------------------------
    # Stats endpoints
    # ----------------------------------------------------------------
    @bp.route("/person_count")
    def person_count():
        return jsonify({"person_count": latest_stats.get("person_count", 0)})

    @bp.route("/violations")
    def violations():
        return jsonify({"violations": latest_stats.get("violations", [])})

    @bp.route("/global_alert")
    def global_alert():
        return jsonify({"global_alert": latest_stats.get("global_alert", False)})

    @bp.route("/Objects")
    def objects():
        return jsonify({"Objects": latest_stats.get("images", [])})

    # ----------------------------------------------------------------
    # Server‑Sent Events (SSE) for alert streaming
    # ----------------------------------------------------------------
    alert_lock = threading.Lock()
    alert_flag = False

    @bp.route("/alert")
    def alert():
        """SSE endpoint that pushes a JSON payload every ~0.7 s."""

        def event_stream():
            while True:
                with alert_lock:
                    flag = alert_flag   # (currently unused, kept for future)

                violations = latest_stats.get("violations", 0)
                person_cnt = latest_stats.get("person_count", 0)
                status = "ALERT" if violations else "OK"
                # if(int(violations[0]) > 0 ):
                frame = latest_stats.get("frame")
                
                if int(violations) >0:
                    print(BASE_DIR_PATH)
                    save_alert_to_db(engine,CAMERA_IP,save_frame_to_file(BASE_DIR_PATH,frame,CAMERA_IP))
                payload = {
                    "status": status,
                    "violations": violations,
                    "person_count": person_cnt,
                }
                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(0.7)

        return Response(event_stream(), mimetype="text/event-stream")

    # ----------------------------------------------------------------
    # Simple login endpoint (demo only – never store plain passwords!)
    # ----------------------------------------------------------------
        # from flask import Blueprint, render_template, request, session
 # Import the 'text' function

# Assuming your get_engine function is in a file named `database.py`
# from .database import get_engine 
    
    # def list_files():
    #         files = os.listdir("./alerts/10.25.78.240")  # current dir
    #         return jsonify(files)
    
    @bp.route("/list")
    def list_files():
        # image_folder = os.path.join(@bp..static_folder, "images")
        files = os.listdir("./static/alerts/10.25.78.240")

        # Build image URLs
        image_urls = [url_for('static', filename=f"alerts/10.25.78.240/{f}") for f in files]

        # Render simple HTML page with images
        html = """
        <h2>Available Images</h2>
        {% for img in images %}
        <div style="margin:10px;">
            <img src="{{ img }}" width="300"><br>
            <span>{{ img }}</span>
        </div>
        {% endfor %}
        """
        return render_template_string(html, images=image_urls)


    @bp.route("/login", methods=["GET", "POST"])
    def login():
        msg = ""
        account=None
        result=None
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            
            # Get the SQLAlchemy Engine object
            

            if not engine:
                msg = "Database connection failed."
                return render_template("login.html", msg=msg)

            try:
                # Connect to the database using the engine
                with engine.connect() as connection:
                    print("enginer")
                    # Use a parameterized query with SQLAlchemy's `text` object
                    query = text("SELECT username,password FROM tbl_users WHERE username = :user AND password = :pass")
                    result = connection.execute(query, {"user": username, "pass": password})
                    
                    # Fetch the single matching record
                    account = result.fetchone()
                    print(account)
                # print(account)

                # if account:
                    # session["loggedin"] = True
                    # password = account.password # Access columns by name
                    # username = account.username

                    return render_template("index.html")
                # else:
                #     msg = "Incorrect username/password!"
            
            except Exception as e:
                # Handle any potential database connection or query errors
                print(f"Database error: {e}")
                msg =f"An error occurred while trying to log in.{e}"

        # For GET request or failed POST
        return render_template("login.html", msg=msg)

    @bp.route("/login-form")
    def login_form():
            return render_template("login.html")

    # ----------------------------------------------------------------
    # Return the ready‑to‑register blueprint
    # ----------------------------------------------------------------
    
    return bp



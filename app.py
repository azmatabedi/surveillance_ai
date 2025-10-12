from flask import Flask
from routes.main_routes import create_routes
from camera.camera_thread import CameraThread
from config import RTSP_URL, USE_GSTREAMER
from utils.helpers import *
# Initialize Flask

app = Flask(__name__,static_folder='./static')



# app.config['MYSQL_CURSORCLASS'] = 'DictCursor' # Returns rows as dictionaries

# Initialize the MySQL extension
# mysql = MySQL(app)

# Create camera thread
#src=RTSP_URL, use_gstreamer=USE_GSTREAMER
camera_thread = CameraThread()
camera_thread._open_capture()
# Register routes, injecting dependencies
main_bp = create_routes(camera_thread)
app.register_blueprint(main_bp)

# @app.teardown_appcontext
# def shutdown_session(exception=None):
#     try:
#         camera_thread.stop()
#     except Exception:
#         pass

if __name__ == "__main__":
    
    app.run(host="0.0.0.0", port=5001, threaded=True, debug=True)
    
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import cv2
import os
import numpy as np
from werkzeug.utils import secure_filename

# Import video detection modules
from detect import VideoDetector
from routes import init_routes

app = Flask(__name__)
app.secret_key = 'simple-secret-key'
CORS(app)  # Enable CORS for video upload functionality

# Configuration - Facial Recognition
UPLOAD_FOLDER = 'faces'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ADMIN_USER = 'admin'
ADMIN_PASS = 'admin123'

# Configuration - Video Detection
VIDEO_UPLOAD_FOLDER = './uploads'
VIDEO_RESULTS_FOLDER = './runs/detect'
app.config['UPLOAD_FOLDER'] = VIDEO_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

os.makedirs(VIDEO_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_RESULTS_FOLDER, exist_ok=True)

# Load face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize YOLO detector for video processing
print("\n" + "="*60)
print("🚀 INITIALIZING VIDEO DETECTION SYSTEM")
print("="*60)
try:
    detector = VideoDetector(model_path='./models/yolo11n.pt')
    init_routes(app, detector)  # Add video detection API routes
    print("✓ Video detection routes initialized")
except Exception as e:
    print(f"⚠️  Warning: Video detection not initialized: {e}")
    print("   You can still use facial recognition features")
    detector = None

# ==================== FACIAL RECOGNITION ROUTES ====================

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['admin'] = True
            return redirect('/admin')
        return render_template('admin_login.html', error='Wrong credentials')
    
    return render_template('admin_login.html')

@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        return redirect('/admin_login')
    
    users = [f.replace('.jpg', '') for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.jpg')]
    return render_template('admin.html', users=users)

@app.route('/register_user', methods=['POST'])
def register_user():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        name = request.form.get('name', '').strip()
        if not name:
            return jsonify({'success': False, 'message': 'Name required'})
        
        file = request.files.get('image')
        if not file:
            return jsonify({'success': False, 'message': 'Image required'})
        
        # Save image
        filename = secure_filename(name) + '.jpg'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Check if face detected
        img = cv2.imread(filepath)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            os.remove(filepath)
            return jsonify({'success': False, 'message': 'No face detected!'})
        
        return jsonify({'success': True, 'message': f'User {name} registered!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_user', methods=['POST'])
def delete_user():
    if not session.get('admin'):
        return jsonify({'success': False})
    
    name = request.json.get('name')
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(name) + '.jpg')
    
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/login_face', methods=['POST'])
def login_face():
    try:
        file = request.files.get('image')
        if not file:
            return jsonify({'success': False, 'message': 'No image'})
        
        # Save temp file
        temp_path = 'temp_login.jpg'
        file.save(temp_path)
        
        # Load and detect face
        img = cv2.imread(temp_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            os.remove(temp_path)
            return jsonify({'success': False, 'message': 'No face detected'})
        
        # Get the face region
        (x, y, w, h) = faces[0]
        face_img = gray[y:y+h, x:x+w]
        face_img = cv2.resize(face_img, (100, 100))
        
        # Compare with registered faces
        best_match = None
        best_score = float('inf')
        
        for filename in os.listdir(UPLOAD_FOLDER):
            if not filename.endswith('.jpg'):
                continue
            
            registered_path = os.path.join(UPLOAD_FOLDER, filename)
            registered_img = cv2.imread(registered_path)
            registered_gray = cv2.cvtColor(registered_img, cv2.COLOR_BGR2GRAY)
            registered_faces = face_cascade.detectMultiScale(registered_gray, 1.1, 4)
            
            if len(registered_faces) > 0:
                (rx, ry, rw, rh) = registered_faces[0]
                registered_face = registered_gray[ry:ry+rh, rx:rx+rw]
                registered_face = cv2.resize(registered_face, (100, 100))
                
                # Calculate similarity using Mean Squared Error
                mse = np.sum((face_img.astype("float") - registered_face.astype("float")) ** 2)
                mse /= float(face_img.shape[0] * face_img.shape[1])
                
                if mse < best_score:
                    best_score = mse
                    best_match = filename.replace('.jpg', '')
        
        os.remove(temp_path)
        
        # If match is good enough (lower is better)
        if best_match and best_score < 1500:
            session['user'] = best_match
            return jsonify({'success': True, 'message': f'Welcome {best_match}!'})
        
        return jsonify({'success': False, 'message': 'Face not recognized'})
    
    except Exception as e:
        if os.path.exists('temp_login.jpg'):
            os.remove('temp_login.jpg')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/home')
def home():
    """Main dashboard - requires facial recognition login"""
    if 'user' not in session:
        return redirect('/')
    
    # Pass username to the dashboard
    username = session['user']
    return render_template('home.html', username=username)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ==================== ADDITIONAL ROUTES ====================

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok', 
        'message': 'Server is running',
        'video_detection': detector is not None
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("✅ SERVER READY")
    print("="*60)
    print(f"📍 Login Page: http://localhost:5000")
    print(f"📍 Admin Panel: http://localhost:5000/admin_login")
    print(f"📍 Dashboard: http://localhost:5000/home (after facial login)")
    print(f"📍 API Health: http://localhost:5000/api/health")
    print(f"\n📂 Face Images: {UPLOAD_FOLDER}")
    print(f"📂 Video Uploads: {VIDEO_UPLOAD_FOLDER}")
    print(f"📂 Detection Results: {VIDEO_RESULTS_FOLDER}")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
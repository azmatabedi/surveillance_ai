"""
routes.py - API Routes Module
Handles all Flask routes and endpoints
"""

from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
import shutil
from datetime import datetime
import threading


UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}
DETECTION_RESULTS_FOLDER = './runs/detect'

# Will be set by app.py
detector = None


def init_routes(app, video_detector):
    """
    Initialize routes with Flask app and detector instance
    
    Args:
        app: Flask application instance
        video_detector: VideoDetector instance from detect.py
    """
    global detector
    detector = video_detector
    
    # Create necessary directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DETECTION_RESULTS_FOLDER, exist_ok=True)
    
    
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    
    @app.route('/api/upload', methods=['POST'])
    def upload_files():
        """Handle folder upload with videos"""
        try:
            if 'files[]' not in request.files:
                return jsonify({'error': 'No files provided'}), 400
            
            files = request.files.getlist('files[]')
            folder_name = request.form.get('folder_name', 'uploaded_videos')
            
            # Create folder structure
            folder_path = os.path.join(UPLOAD_FOLDER, secure_filename(folder_name))
            os.makedirs(folder_path, exist_ok=True)
            
            uploaded_files = []
            
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(folder_path, filename)
                    file.save(file_path)
                    
                    uploaded_files.append({
                        'name': filename,
                        'path': file_path,
                        'size': os.path.getsize(file_path)
                    })
            
            folder_info = {
                'id': folder_name,
                'name': folder_name,
                'path': folder_path,
                'videos': uploaded_files,
                'uploadDate': datetime.now().isoformat(),
                'processed': False
            }
            
            print(f"✓ Uploaded folder: {folder_name} ({len(uploaded_files)} videos)")
            
            return jsonify({
                'success': True,
                'folder': folder_info
            }), 200
            
        except Exception as e:
            print(f"✗ Upload error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/detect', methods=['POST'])
    def run_detection():
        """Run YOLO detection on selected folders"""
        try:
            data = request.json
            folder_paths = data.get('folders', [])
            
            if not folder_paths:
                return jsonify({'error': 'No folders provided'}), 400
            
            # Get detection parameters (with defaults)
            vid_stride = data.get('vid_stride', 5)
            device = data.get('device', 'cpu')
            conf = data.get('conf', 0.25)
            
            print(f"\n🚀 Detection request received:")
            print(f"   Folders: {len(folder_paths)}")
            print(f"   Settings: vid_stride={vid_stride}, device={device}, conf={conf}")
            
            # Start detection in background thread
            detection_thread = threading.Thread(
                target=process_detection_async,
                args=(folder_paths, vid_stride, device, conf)
            )
            detection_thread.start()
            
            return jsonify({
                'success': True,
                'message': 'Detection started',
                'folders': len(folder_paths),
                'settings': {
                    'vid_stride': vid_stride,
                    'device': device,
                    'conf': conf
                }
            }), 200
            
        except Exception as e:
            print(f"✗ Detection error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    
    def process_detection_async(folder_paths, vid_stride, device, conf):
        """Process video detection asynchronously"""
        try:
            results = detector.detect_multiple_folders(
                folder_paths,
                output_dir=DETECTION_RESULTS_FOLDER,
                vid_stride=vid_stride,
                device=device,
                conf=conf
            )
            
            # Print summary
            summary = detector.get_detection_summary(results)
            print(f"\n📊 Detection Summary:")
            print(f"   Total videos: {summary['total_videos']}")
            print(f"   Successful: {summary['successful']}")
            print(f"   Failed: {summary['failed']}")
            
        except Exception as e:
            print(f"✗ Async detection error: {str(e)}")
    
    
    @app.route('/api/folders', methods=['GET'])
    def list_folders():
        """List all uploaded folders"""
        try:
            folders = []
            
            if os.path.exists(UPLOAD_FOLDER):
                for folder_name in os.listdir(UPLOAD_FOLDER):
                    folder_path = os.path.join(UPLOAD_FOLDER, folder_name)
                    
                    if os.path.isdir(folder_path):
                        video_files = [
                            f for f in os.listdir(folder_path)
                            if allowed_file(f)
                        ]
                        
                        folders.append({
                            'name': folder_name,
                            'path': folder_path,
                            'video_count': len(video_files),
                            'videos': video_files
                        })
            
            return jsonify({'folders': folders}), 200
            
        except Exception as e:
            print(f"✗ List folders error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/folder/<folder_name>', methods=['DELETE'])
    def delete_folder(folder_name):
        """Delete a folder and its contents"""
        try:
            folder_path = os.path.join(UPLOAD_FOLDER, secure_filename(folder_name))
            
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                print(f"✓ Deleted folder: {folder_name}")
                return jsonify({'success': True, 'message': 'Folder deleted'}), 200
            else:
                return jsonify({'error': 'Folder not found'}), 404
                
        except Exception as e:
            print(f"✗ Delete error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/results', methods=['GET'])
    def get_results():
        """Get detection results"""
        try:
            results = []
            
            if os.path.exists(DETECTION_RESULTS_FOLDER):
                for result_folder in os.listdir(DETECTION_RESULTS_FOLDER):
                    result_path = os.path.join(DETECTION_RESULTS_FOLDER, result_folder)
                    
                    if os.path.isdir(result_path):
                        files = os.listdir(result_path)
                        results.append({
                            'name': result_folder,
                            'path': result_path,
                            'files': files,
                            'file_count': len(files)
                        })
            
            return jsonify({'results': results}), 200
            
        except Exception as e:
            print(f"✗ Get results error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'upload_folder': UPLOAD_FOLDER,
            'results_folder': DETECTION_RESULTS_FOLDER,
            'detector_loaded': detector is not None
        }), 200
    
    
    print("✓ Routes initialized successfully")
"""
detect.py - YOLO Object Detection Module
Handles all video detection logic
"""

from ultralytics import YOLO
import os
import cv2
from pathlib import Path


class VideoDetector:
    def __init__(self, model_path='./models/yolo11n.pt'):
        """
        Initialize the YOLO detector
        
        Args:
            model_path: Path to YOLO model file
        """
        self.model = YOLO(model_path)
        print(f"✓ Model loaded: {model_path}")
    
    def detect_video(self, video_path, output_dir='./runs/detect', 
                     vid_stride=5, device='cpu', conf=0.25, save=True):
        """
        Run object detection on a single video
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save results
            vid_stride: Process every Nth frame
            device: 'cpu', 'cuda', or 'mps'
            conf: Confidence threshold
            save: Whether to save annotated video
            
        Returns:
            dict: Detection results and metadata
        """
        try:
            print(f"\n🎬 Processing: {os.path.basename(video_path)}")
            
            # Run YOLO detection
            results = self.model(
                video_path,
                save=save,
                vid_stride=vid_stride,
                device=device,
                conf=conf,
                project=output_dir,
                exist_ok=True
            )
            
            # Get video info
            video_info = self._get_video_info(video_path)
            
            print(f"✓ Completed: {os.path.basename(video_path)}")
            
            return {
                'status': 'success',
                'video_name': os.path.basename(video_path),
                'video_path': video_path,
                'video_info': video_info,
                'results': results
            }
            
        except Exception as e:
            print(f"✗ Error processing {video_path}: {str(e)}")
            return {
                'status': 'error',
                'video_name': os.path.basename(video_path),
                'error': str(e)
            }
    
    def detect_folder(self, folder_path, output_dir='./runs/detect',
                      vid_stride=5, device='cpu', conf=0.25):
        """
        Run detection on all videos in a folder
        
        Args:
            folder_path: Path to folder containing videos
            output_dir: Directory to save results
            vid_stride: Process every Nth frame
            device: 'cpu', 'cuda', or 'mps'
            conf: Confidence threshold
            
        Returns:
            list: Results for each video
        """
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        
        if not os.path.exists(folder_path):
            print(f"✗ Folder not found: {folder_path}")
            return []
        
        # Get all video files
        video_files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if os.path.splitext(f)[1].lower() in video_extensions
        ]
        
        if not video_files:
            print(f"✗ No video files found in: {folder_path}")
            return []
        
        print(f"\n📁 Processing folder: {os.path.basename(folder_path)}")
        print(f"📹 Found {len(video_files)} video(s)")
        
        results = []
        folder_name = os.path.basename(folder_path)
        folder_output_dir = os.path.join(output_dir, folder_name)
        
        for idx, video_path in enumerate(video_files, 1):
            print(f"\n[{idx}/{len(video_files)}]", end=" ")
            
            result = self.detect_video(
                video_path,
                output_dir=folder_output_dir,
                vid_stride=vid_stride,
                device=device,
                conf=conf
            )
            
            results.append(result)
        
        print(f"\n✅ Folder processing complete: {folder_name}")
        print(f"📂 Results saved to: {folder_output_dir}")
        
        return results
    
    def detect_multiple_folders(self, folder_paths, output_dir='./runs/detect',
                                vid_stride=5, device='cpu', conf=0.25):
        """
        Run detection on multiple folders
        
        Args:
            folder_paths: List of folder paths
            output_dir: Directory to save results
            vid_stride: Process every Nth frame
            device: 'cpu', 'cuda', or 'mps'
            conf: Confidence threshold
            
        Returns:
            dict: Results organized by folder
        """
        all_results = {}
        
        print(f"\n🚀 Starting batch detection on {len(folder_paths)} folder(s)")
        print(f"⚙️  Settings: vid_stride={vid_stride}, device={device}, conf={conf}")
        
        for idx, folder_path in enumerate(folder_paths, 1):
            print(f"\n{'='*60}")
            print(f"FOLDER {idx}/{len(folder_paths)}")
            print(f"{'='*60}")
            
            folder_name = os.path.basename(folder_path)
            results = self.detect_folder(
                folder_path,
                output_dir=output_dir,
                vid_stride=vid_stride,
                device=device,
                conf=conf
            )
            
            all_results[folder_name] = results
        
        print(f"\n{'='*60}")
        print("✅ BATCH DETECTION COMPLETE")
        print(f"{'='*60}")
        print(f"📊 Processed {len(folder_paths)} folder(s)")
        print(f"📂 All results saved to: {output_dir}")
        
        return all_results
    
    def _get_video_info(self, video_path):
        """Get video metadata"""
        try:
            cap = cv2.VideoCapture(video_path)
            info = {
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration_sec': int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))
            }
            cap.release()
            return info
        except:
            return {}
    
    def get_detection_summary(self, results):
        """
        Generate summary statistics from detection results
        
        Args:
            results: Detection results from detect_folder or detect_multiple_folders
            
        Returns:
            dict: Summary statistics
        """
        summary = {
            'total_videos': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        if isinstance(results, dict):
            # Multiple folders
            for folder_name, folder_results in results.items():
                for result in folder_results:
                    summary['total_videos'] += 1
                    if result['status'] == 'success':
                        summary['successful'] += 1
                    else:
                        summary['failed'] += 1
                        summary['errors'].append({
                            'video': result['video_name'],
                            'error': result.get('error', 'Unknown error')
                        })
        else:
            # Single folder
            for result in results:
                summary['total_videos'] += 1
                if result['status'] == 'success':
                    summary['successful'] += 1
                else:
                    summary['failed'] += 1
                    summary['errors'].append({
                        'video': result['video_name'],
                        'error': result.get('error', 'Unknown error')
                    })
        
        return summary


# Standalone usage example
if __name__ == "__main__":
    # Example 1: Detect single video
    detector = VideoDetector(model_path='./models/yolo11n.pt')
    
    # Single video detection
    # result = detector.detect_video('./uploads/video.mp4')
    
    # Example 2: Detect all videos in a folder
    # results = detector.detect_folder('./uploads/folder1')
    
    # Example 3: Detect multiple folders
    # folder_paths = ['./uploads/folder1', './uploads/folder2']
    # results = detector.detect_multiple_folders(folder_paths, device='cpu')
    
    # Example 4: Get summary
    # summary = detector.get_detection_summary(results)
    # print("\n📊 Detection Summary:")
    # print(f"Total videos: {summary['total_videos']}")
    # print(f"Successful: {summary['successful']}")
    # print(f"Failed: {summary['failed']}")
    
    print("✓ Detection module loaded successfully")
    print("Import this module in your app.py to use VideoDetector class")
#!/usr/bin/env python3
"""
Raspberry Pi Timelapse Controller - Main Application
A Flask web application for creating timelapse videos using the Raspberry Pi camera.
"""

import os
import threading
import time
import glob
import subprocess
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory

# Import our custom modules
from config import Config
from camera import Camera
from video_generator import create_video_opencv

# Constants
# Constants - Use system paths if available, otherwise local
if os.path.exists("/var/lib/timelapse"):
    IMAGES_DIR = "/var/lib/timelapse/images"
    VIDEOS_DIR = "/var/lib/timelapse/videos"
    USE_SYSTEM_PATHS = True
else:
    IMAGES_DIR = "static/images"
    VIDEOS_DIR = "static/videos"
    USE_SYSTEM_PATHS = False


class TimelapseApp:
    """Main timelapse application controller."""
    
    def __init__(self):
        """Initialize the timelapse application."""
        self.config = Config()
        self.camera = Camera()
        self.is_recording = False
        self.timelapse_thread = None
        self.scheduler_thread = None
        self.video_creation_lock = threading.Lock()
        
        # Ensure directories exist
        os.makedirs(IMAGES_DIR, exist_ok=True)
        os.makedirs(VIDEOS_DIR, exist_ok=True)
    
    def start_scheduler(self):
        """Start the background scheduler for daily video creation."""
        if self.scheduler_thread is None or not self.scheduler_thread.is_alive():
            self.scheduler_thread = threading.Thread(target=self._scheduler_worker)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            print("Background scheduler started")
    
    def start_timelapse(self):
        """Start continuous timelapse capture."""
        if self.is_recording:
            return {"status": "error", "message": "Timelapse already running"}
        
        # Initialize camera with current flip settings
        try:
            self.camera.initialize(
                hflip=self.config.get('hflip', False),
                vflip=self.config.get('vflip', False)
            )
        except Exception as e:
            return {"status": "error", "message": f"Camera initialization failed: {e}"}
        
        # Start capture thread
        self.is_recording = True
        self.timelapse_thread = threading.Thread(
            target=self._capture_worker,
            args=(self.config.get('interval', 5),)
        )
        self.timelapse_thread.daemon = True
        self.timelapse_thread.start()
        
        self.config.set('is_running', True)
        return {
            "status": "success", 
            "message": "Timelapse recording started"
        }
    
    def stop_timelapse(self):
        """Stop timelapse capture."""
        if not self.is_recording:
            return {"status": "error", "message": "No timelapse running"}
        
        self.is_recording = False
        self.config.set('is_running', False)
        
        # Optionally process the completed recording
        if self.config.get('auto_generate_video', True):
            # Start video generation in background to avoid blocking
            threading.Thread(
                target=self._process_recording_completion,
                daemon=True
            ).start()
        
        return {"status": "success", "message": "Timelapse stopped"}
    
    def capture_single_image(self):
        """Capture a single image manually."""
        try:
            if not self.camera.is_initialized():
                self.camera.initialize(
                    hflip=self.config.get('hflip', False),
                    vflip=self.config.get('vflip', False)
                )
            filename = self.camera.capture('manual')
            
            # Use appropriate URL based on installation type
            if USE_SYSTEM_PATHS:
                url = f'/media/images/{filename}'
            else:
                url = f'/static/images/{filename}'
                
            return {
                "status": "success",
                "filename": filename,
                "url": url
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def update_config(self, updates):
        """Update configuration with camera restart if needed."""
        old_hflip = self.config.get('hflip', False)
        old_vflip = self.config.get('vflip', False)
        
        # Update config with allowed fields only
        allowed_fields = [
            'interval', 'resolution', 'quality', 'auto_generate_video', 
            'auto_delete_images', 'video_fps', 'video_quality', 'video_method',
            'scheduled_video_creation', 'daily_video_time', 'hflip', 'vflip'
        ]
        
        config_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        self.config.update(config_updates)
        
        # Restart camera if flip settings changed
        new_hflip = self.config.get('hflip', False)
        new_vflip = self.config.get('vflip', False)
        
        if old_hflip != new_hflip or old_vflip != new_vflip:
            try:
                self.camera.restart_if_needed(new_hflip, new_vflip)
            except Exception as e:
                return {"status": "error", "message": f"Camera restart failed: {e}"}
        
        return {"status": "success", "config": self.config.data}
    
    def get_images_list(self):
        """Get list of captured images with metadata."""
        if not os.path.exists(IMAGES_DIR):
            return []
        
        images = []
        for filename in sorted(os.listdir(IMAGES_DIR), reverse=True):
            if filename.endswith('.jpg'):
                filepath = os.path.join(IMAGES_DIR, filename)
                try:
                    stat = os.stat(filepath)
                    # Use appropriate URL based on installation type
                    if USE_SYSTEM_PATHS:
                        url = f'/media/images/{filename}'
                    else:
                        url = f'/static/images/{filename}'
                    
                    images.append({
                        'filename': filename,
                        'url': url,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
                except OSError:
                    continue  # Skip files that can't be accessed
        
        return images
    
    def get_videos_list(self):
        """Get list of generated videos with metadata."""
        if not os.path.exists(VIDEOS_DIR):
            return []
        
        videos = []
        for filename in sorted(os.listdir(VIDEOS_DIR), reverse=True):
            if filename.endswith('.mp4'):
                filepath = os.path.join(VIDEOS_DIR, filename)
                try:
                    stat = os.stat(filepath)
                    # Use appropriate URL based on installation type
                    if USE_SYSTEM_PATHS:
                        url = f'/media/videos/{filename}'
                    else:
                        url = f'/static/videos/{filename}'
                        
                    videos.append({
                        'filename': filename,
                        'url': url,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
                except OSError:
                    continue  # Skip files that can't be accessed
        
        return videos
    
    def generate_video_from_all_images(self):
        """Generate video from all images."""
        # Check if video creation is already in progress
        if not self.video_creation_lock.acquire(blocking=False):
            return {
                "status": "error",
                "message": "Video creation already in progress. Please wait and try again."
            }
        
        try:
            success = self._create_video_from_all_images()
            
            if success:
                message = "Video generated successfully from all images"
                
                # Optionally delete images after manual video generation
                if self.config.get('auto_delete_images', True):
                    delete_result = self.delete_all_images()
                    if delete_result["status"] == "success":
                        message += " and images deleted"
                        print("Images automatically deleted after manual video generation")
                    else:
                        print(f"Warning: Video created but image deletion failed: {delete_result['message']}")
                else:
                    print("Images preserved after manual video generation")
                
                return {
                    "status": "success",
                    "message": message
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to generate video from all images"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            self.video_creation_lock.release()
    
    def delete_all_images(self):
        """Delete all timelapse images."""
        try:
            pattern = os.path.join(IMAGES_DIR, 'timelapse_*.jpg')
            deleted_count = 0
            
            for image_file in glob.glob(pattern):
                os.remove(image_file)
                deleted_count += 1
                
            print(f"Deleted {deleted_count} images")
            return {
                "status": "success",
                "message": f"Deleted {deleted_count} images"
            }
        except Exception as e:
            print(f"Error deleting images: {e}")
            return {"status": "error", "message": str(e)}
    
    def cleanup(self):
        """Clean up resources when shutting down."""
        self.is_recording = False
        self.camera.cleanup()
    
    # Private methods
    def _capture_worker(self, interval):
        """Worker thread for continuous image capture."""
        print("Starting timelapse recording")
        image_count = 0
        
        try:
            interval = float(interval)
        except (ValueError, TypeError):
            print("Invalid interval value, using 5.0 seconds")
            interval = 5.0
        
        while self.is_recording:
            try:
                filename = self.camera.capture('timelapse')
                image_count += 1
                print(f"Captured image {image_count}: {filename}")
                time.sleep(interval)
            except Exception as e:
                print(f"Error capturing image: {e}")
                time.sleep(interval)
        
        print(f"Timelapse recording completed with {image_count} images")
    
    def _scheduler_worker(self):
        """Background worker for daily video creation."""
        while True:
            try:
                if self.config.get('scheduled_video_creation', False):
                    self._check_daily_video_schedule()
            except Exception as e:
                print(f"Scheduler error: {e}")
            
            time.sleep(30)  # Check every 30 seconds
    
    def _check_daily_video_schedule(self):
        """Check if it's time to create daily video."""
        now = datetime.now()
        target_time = self.config.get('daily_video_time', '18:00')
        
        try:
            hour, minute = map(int, target_time.split(':'))
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Check if within 30 seconds of target time
            if abs((now - target).total_seconds()) <= 30:
                last_date = self.config.get('last_video_creation_date')
                today = now.strftime('%Y-%m-%d')
                
                if last_date != today:
                    if self.video_creation_lock.acquire(blocking=False):
                        try:
                            self.config.set('last_video_creation_date', today)
                            print(f"Creating daily video at {target_time}")
                            self._process_scheduled_video_creation()
                        finally:
                            self.video_creation_lock.release()
        except Exception as e:
            print(f"Error checking daily schedule: {e}")
    
    def _process_scheduled_video_creation(self):
        """Process scheduled video creation."""
        if not self.config.get('auto_generate_video', True):
            print("Auto video generation disabled. Skipping scheduled video creation.")
            return
        
        print("Scheduled video creation triggered. Creating video from all images...")
        
        try:
            success = self._create_video_from_all_images()
            
            if success:
                print("Scheduled video created successfully")
                
                # Optionally delete images
                if self.config.get('auto_delete_images', True):
                    result = self.delete_all_images()
                    print("Images deleted after scheduled video creation")
                else:
                    print("Images preserved after scheduled video creation")
            else:
                print("Failed to create scheduled video")
                
        except Exception as e:
            print(f"Error processing scheduled video creation: {e}")
    
    def _process_recording_completion(self):
        """Process recording completion: generate video and optionally delete images."""
        if not self.config.get('auto_generate_video', True):
            print("Auto video generation disabled. Recording completed.")
            return
        
        print("Recording completed. Generating video...")
        
        try:
            result = self.generate_video_from_all_images()
            
            if result["status"] == "success":
                print("Video generated successfully")
                
                # Optionally delete images
                if self.config.get('auto_delete_images', True):
                    delete_result = self.delete_all_images()
                    print("Images deleted after video generation")
                else:
                    print("Images preserved")
            else:
                print(f"Failed to generate video: {result['message']}")
                
        except Exception as e:
            print(f"Error processing recording completion: {e}")
    
    def _create_video_from_all_images(self):
        """Create a video from all timelapse images."""
        # Get all timelapse images
        pattern = os.path.join(IMAGES_DIR, 'timelapse_*.jpg')
        images = sorted(glob.glob(pattern))
        
        if not images:
            print("No images found for video creation")
            return False
        
        # Create a timestamp for the video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(VIDEOS_DIR, f"timelapse_{timestamp}.mp4")
        
        try:
            video_fps = self.config.get('video_fps', 30)
            video_quality = self.config.get('video_quality', 23)
            video_method = self.config.get('video_method', 'ffmpeg')
            
            # Get target resolution from config
            resolution_str = self.config.get('resolution', '1920x1080')
            width, height = map(int, resolution_str.split('x'))
            target_resolution = (width, height)
            
            if video_method == 'ffmpeg':
                # Use FFmpeg to create video from all images with scaling
                cmd = [
                    'ffmpeg',
                    '-y',  # Overwrite output file
                    '-framerate', str(video_fps),
                    '-pattern_type', 'glob',
                    '-i', pattern,
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', str(video_quality),
                    '-vf', f'scale={width}:{height}:flags=lanczos',
                    '-pix_fmt', 'yuv420p',
                    output_path
                ]
                
                print(f"Creating video with {len(images)} images at {video_fps} FPS using FFmpeg...")
                print(f"Scaling to {width}x{height}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"Video saved to: {output_path}")
                return True
                
            else:
                # Use OpenCV method with scaling
                return create_video_opencv(pattern, output_path, video_fps, video_quality, target_resolution)
                
        except Exception as e:
            print(f"Error creating video from all images: {e}")
            return False


# Create Flask app and timelapse app instance
app = Flask(__name__)
timelapse_app = TimelapseApp()

# Flask Routes
@app.route('/')
def index():
    """Main page."""
    return render_template('index.html', config=timelapse_app.config.data)

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    return jsonify(timelapse_app.config.data)

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration."""
    return jsonify(timelapse_app.update_config(request.json))

@app.route('/api/start', methods=['POST'])
def start_timelapse():
    """Start timelapse capture."""
    return jsonify(timelapse_app.start_timelapse())

@app.route('/api/stop', methods=['POST'])
def stop_timelapse():
    """Stop timelapse capture."""
    return jsonify(timelapse_app.stop_timelapse())

@app.route('/api/capture', methods=['POST'])
def capture_single():
    """Capture a single image."""
    return jsonify(timelapse_app.capture_single_image())

@app.route('/api/status')
def get_status():
    """Get current timelapse status."""
    return jsonify({
        "is_running": timelapse_app.config.get('is_running', False),
        "is_recording": timelapse_app.is_recording,
        "config": timelapse_app.config.data
    })

@app.route('/api/images')
def get_images():
    """Get list of captured images."""
    return jsonify(timelapse_app.get_images_list())

@app.route('/api/videos')
def get_videos():
    """Get list of generated videos."""
    return jsonify(timelapse_app.get_videos_list())

@app.route('/api/generate-video', methods=['POST'])
def generate_video_manual():
    """Manually generate video from all images."""
    return jsonify(timelapse_app.generate_video_from_all_images())

@app.route('/api/delete-images', methods=['POST'])
def delete_images_manual():
    """Manually delete all images."""
    return jsonify(timelapse_app.delete_all_images())

# Custom media serving routes for system installation
@app.route('/media/images/<filename>')
def serve_image(filename):
    """Serve images from system data directory when installed as service."""
    if USE_SYSTEM_PATHS:
        return send_from_directory(IMAGES_DIR, filename)
    else:
        # Fallback to regular static serving for development
        return send_from_directory('static/images', filename)

@app.route('/media/videos/<filename>')  
def serve_video(filename):
    """Serve videos from system data directory when installed as service."""
    if USE_SYSTEM_PATHS:
        return send_from_directory(VIDEOS_DIR, filename)
    else:
        # Fallback to regular static serving for development
        return send_from_directory('static/videos', filename)


if __name__ == '__main__':
    # Start the background scheduler
    timelapse_app.start_scheduler()
    print("Timelapse application started with background scheduler")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        timelapse_app.cleanup()
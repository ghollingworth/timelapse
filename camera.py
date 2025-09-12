#!/usr/bin/env python3
"""
Camera controller for timelapse application.
Handles camera initialization, configuration, and image capture.
"""

import os
from datetime import datetime
from typing import Optional
from picamera2 import Picamera2
from libcamera import Transform


class Camera:
    """Simple camera controller for Raspberry Pi camera."""
    
    def __init__(self):
        """Initialize camera controller."""
        self.camera: Optional[Picamera2] = None
        self._current_hflip = False
        self._current_vflip = False
    
    def initialize(self, hflip: bool = False, vflip: bool = False) -> None:
        """
        Initialize camera with flip settings.
        
        Args:
            hflip: Horizontal flip (mirror image)
            vflip: Vertical flip (upside down)
        """
        try:
            if self.camera is None:
                self.camera = Picamera2()
            else:
                self.camera.stop()
            
            # Create camera configuration with transform
            camera_config = self.camera.create_still_configuration(
                transform=Transform(vflip=vflip, hflip=hflip)
            )
            self.camera.configure(camera_config)
            self.camera.start()
            
            # Store current settings
            self._current_hflip = hflip
            self._current_vflip = vflip
            
            print(f"Camera initialized with hflip={hflip}, vflip={vflip}")
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera = None
            raise
    
    def capture(self, identifier: str = "single", images_dir: str = None):
        """
        Capture a single image.
        
        Args:
            identifier: Simple identifier for the capture type (e.g., "single", "timelapse")
            images_dir: Directory to save images
            
        Returns:
            Filename of captured image
            
        Raises:
            Exception: If camera is not initialized or capture fails
        """
        if self.camera is None:
            raise Exception("Camera not initialized")
        
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Use system path if available, otherwise local
        if images_dir is None:
            if os.path.exists("/var/lib/timelapse"):
                images_dir = "/var/lib/timelapse/images"
            else:
                images_dir = "static/images"
        # Ensure directory exists
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate filename with timestamp (no session ID)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds for uniqueness
        filename = f"timelapse_{timestamp}.jpg"
        filepath = os.path.join(images_dir, filename)
        
        try:
            # Capture image directly to file
            self.camera.capture_file(filepath)
            return filename
            
        except Exception as e:
            print(f"Error capturing image: {e}")
            raise
    
    def restart_if_needed(self, hflip: bool, vflip: bool) -> None:
        """
        Restart camera if flip settings have changed.
        
        Args:
            hflip: New horizontal flip setting
            vflip: New vertical flip setting
        """
        if (self.camera is not None and 
            (hflip != self._current_hflip or vflip != self._current_vflip)):
            
            print("Restarting camera due to flip settings change")
            try:
                self.camera.stop()
                self.camera.close()
                self.camera = None
                # Reinitialize with new settings
                self.initialize(hflip, vflip)
            except Exception as e:
                print(f"Error restarting camera: {e}")
                self.camera = None
                raise
    
    def is_initialized(self) -> bool:
        """Check if camera is initialized and ready."""
        return self.camera is not None
    
    def cleanup(self) -> None:
        """Clean up camera resources."""
        if self.camera is not None:
            try:
                self.camera.stop()
                self.camera.close()
                print("Camera cleaned up")
            except Exception as e:
                print(f"Error cleaning up camera: {e}")
            finally:
                self.camera = None
                self._current_hflip = False
                self._current_vflip = False

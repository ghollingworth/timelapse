# Raspberry Pi Timelapse Controller

A web-based timelapse camera controller for Raspberry Pi using the picamera2 library. This application provides a modern, responsive web interface to control timelapse settings, capture images, and create videos.

## Features

- **Three-Tab Web Interface**: Clean layout with Controls, Settings, and Media tabs
- **Real-time Media Gallery**: Auto-refreshing gallery showing captured images and videos
- **High-Quality Image Capture**: Images captured at camera sensor's native resolution
- **Configurable Video Output**: Videos encoded at your chosen resolution with high-quality scaling
- **Automatic Video Generation**: Create videos automatically when recording stops
- **Scheduled Daily Videos**: Optional daily video creation at specified times
- **Camera Orientation Controls**: Horizontal and vertical flip support
- **Session-Free Operation**: Simplified recording - only one timelapse at a time
- **Systemd Service**: Automatic startup at boot with proper service management

## Installation

### Prerequisites

- Raspberry Pi (3 or 4 recommended) 
- Raspberry Pi Camera Module (v1, v2, or v3)
- Raspberry Pi OS (Debian-based)

### Install from Debian Package

#### 1. Build the Package

Clone the repository and build the Debian package:

```bash
git clone https://github.com/ghollingworth/timelapse.git
cd timelapse
debuild -uc -us
```

This will create `timelapse-controller_1.0.0_all.deb` in the parent directory.

#### 2. Install the Package

```bash
sudo dpkg -i ../timelapse-controller_1.0.0_all.deb
sudo apt install -f  # Fix any missing dependencies
```

The installation will automatically:
- Create a `timelapse` system user
- Install application files to `/opt/timelapse/`
- Create data directories in `/var/lib/timelapse/`
- Enable and start the systemd service
- Make the web interface available at http://localhost:5000

## Usage

### Web Interface

After installation, access the web interface at:
```
http://localhost:5000
```
Or from another device on your network:
```
http://[raspberry-pi-ip]:5000
```

### Service Management

Control the timelapse service using standard systemctl commands:

```bash
# Check service status
systemctl status timelapse.service

# Start the service
sudo systemctl start timelapse.service

# Stop the service
sudo systemctl stop timelapse.service

# Restart the service
sudo systemctl restart timelapse.service

# View logs
journalctl -u timelapse -f

# Disable automatic startup
sudo systemctl disable timelapse.service
```

## Web Interface

The interface has three main tabs:

### 🎛️ Controls
- **Start/Stop Recording**: Begin and end timelapse capture
- **Single Shot**: Capture individual test images
- **Manual Video Generation**: Create videos from all captured images
- **Image Management**: Delete all captured images
- **Daily Schedule Status**: Monitor automatic daily video creation

### ⚙️ Settings
- **Capture Settings**: Interval between shots, image quality
- **Video Settings**: Output resolution, FPS, quality, generation method
- **Camera Orientation**: Horizontal and vertical flip controls
- **Automation**: Auto video generation and image deletion settings
- **Daily Videos**: Schedule automatic daily video creation

### 📁 Media
- **Images Tab**: View all captured images with auto-refresh
- **Videos Tab**: Play generated videos directly in browser
- **Auto-refresh**: Media updates automatically every 5 seconds when tab is active

## Configuration

Settings are stored in `/var/lib/timelapse/config/timelapse_config.json` and can be modified through the web interface.

### Key Settings

- **Interval**: Time between shots (1-3600 seconds)
- **Video Resolution**: 1920x1080 (Full HD), 1280x720 (HD), or 640x480 (VGA)
- **Auto Generate Video**: Automatically create video when recording stops
- **Auto Delete Images**: Remove images after video creation to save space
- **Video Method**: FFmpeg (recommended) or OpenCV for video creation
- **Daily Videos**: Create videos automatically at specified times

## File Locations

```
/opt/timelapse/                          # Application files
├── app.py                               # Main Flask application
├── camera.py                           # Camera control
├── config.py                           # Configuration management
├── video_generator.py                  # Video creation
├── templates/index.html                # Web interface
└── static/                             # Static web assets

/var/lib/timelapse/                     # Data directory
├── images/                             # Captured images
├── videos/                             # Generated videos  
└── config/timelapse_config.json       # Configuration file
```

## Uninstallation

```bash
# Remove package (keeps data)
sudo apt remove timelapse-controller

# Purge package (removes data after confirmation)
sudo apt purge timelapse-controller
```

## Development

For development or testing, you can run the application manually:

```bash
# Install dependencies
sudo apt install python3-flask python3-picamera2 python3-opencv ffmpeg

# Run directly
python3 app.py
```

The web interface will be available at http://localhost:5000

## License

MIT License - see debian/copyright for full license text.
# Raspberry Pi Timelapse Controller

A web-based timelapse camera controller for Raspberry Pi using the picamera2 library. This application provides a modern, responsive web interface to control timelapse settings, capture images, and view your media.

## Features

- **Web-based Control Interface**: Modern, responsive web UI accessible from any device on your network
- **Real-time Status Monitoring**: Live status updates showing if timelapse is running
- **High-Quality Image Capture**: Images are captured at the camera sensor's native resolution for maximum quality
- **Configurable Video Output**: Videos are encoded at your chosen resolution with high-quality scaling
- **Configurable Settings**: Adjust interval, video output resolution, quality, and video generation settings
- **Single Shot Capture**: Take individual photos for testing or manual capture
- **Media Gallery**: View all captured images and videos in an organized gallery
- **Session Management**: Track timelapse sessions with unique IDs
- **Automatic Video Generation**: Automatically create videos from captured images at the end of each session
- **Automatic Image Cleanup**: Optionally delete images after video generation to save storage space
- **Session Management Interface**: View and manage all timelapse sessions with manual video generation and cleanup options
- **Continuous Operation**: Always runs indefinitely for long-term unattended operation
- **Daily Video Creation**: Create videos at scheduled times (e.g., daily) while timelapse runs continuously
- **Automatic Directory Management**: Creates necessary folders for images and videos

## Requirements

- Raspberry Pi (3 or 4 recommended)
- Raspberry Pi Camera Module (v1, v2, or v3)
- Python 3.7+
- Internet connection for initial setup

## Installation

1. **Clone or download this repository**:
   ```bash
   git clone <repository-url>
   cd timelapse
   ```

2. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv ffmpeg
   ```

3. **Enable camera interface** (if not already done):
   ```bash
   sudo raspi-config
   # Navigate to Interface Options > Camera > Enable
   ```

4. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Access the web interface**:
   Open your web browser and navigate to:
   ```
   http://[raspberry-pi-ip]:5000
   ```
   Replace `[raspberry-pi-ip]` with your Raspberry Pi's IP address.

3. **Configure settings**:
   - Set the interval between shots (in seconds)
   - Set the total duration (in minutes)
   - Choose resolution, quality, ISO, exposure mode, and white balance
   - Click "Save Settings" to apply changes

4. **Start timelapse**:
   - Click the "Start" button to begin capturing
   - The status will show "Running" with a pulsing green indicator
   - Images will be saved to `static/images/` with timestamps

5. **Stop timelapse**:
   - Click the "Stop" button to halt capture
   - The timelapse will also stop automatically when the duration is reached

6. **View media**:
   - Use the "Images" and "Videos" tabs to view captured media
   - Click on images to open them in full size
   - Videos can be played directly in the browser

## Configuration

The application stores settings in `timelapse_config.json`. You can modify this file directly or use the web interface.

### Available Settings

- **interval**: Time between shots in seconds (1-3600)
- **resolution**: Video output resolution (1920x1080, 1280x720, 640x480)
- **quality**: JPEG quality percentage (1-100)
- **auto_generate_video**: Automatically generate video at end of session (true/false)
- **auto_delete_images**: Automatically delete images after video generation (true/false)
- **video_fps**: Frames per second for video generation (1-60)
- **video_quality**: Video quality for FFmpeg (lower is better, 18-28 recommended)
- **video_method**: Video generation method ('ffmpeg' or 'opencv')

### Image Capture vs Video Output

The application now captures images at the camera sensor's native resolution (typically higher than the configured resolution) for maximum image quality. When creating videos, the images are intelligently scaled to your configured video output resolution using high-quality scaling algorithms:

- **Image Capture**: Always uses the camera sensor's native resolution for best quality
- **Video Output**: Scales images to your configured resolution (1920x1080, 1280x720, or 640x480)
- **Scaling Method**: Uses Lanczos interpolation for high-quality downscaling
- **Benefits**: Better image quality, smaller video files, configurable output size

This approach gives you the best of both worlds: high-quality source images and appropriately sized video files.

## File Structure

```
timelapse/
├── app.py                 # Main Flask application
├── video_generator.py     # Video generation utilities
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── timelapse_config.json # Configuration file (auto-generated)
├── templates/
│   └── index.html        # Web interface template
└── static/
    ├── images/           # Captured images
    └── videos/           # Generated videos
```

## API Endpoints

The application provides a REST API for programmatic control:

- `GET /api/status` - Get current timelapse status
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `POST /api/start` - Start timelapse
- `POST /api/stop` - Stop timelapse
- `POST /api/capture`

## Advanced Usage

### Running as a System Service

The application includes a systemd service file for automatic startup at boot time. This is the recommended way to run the timelapse controller in production.

#### Installation

1. **Install the service using the provided script**:
   ```bash
   ./install_service.sh
   ```

   This script will:
   - Customize the service file for your user and directory
   - Install the service file to `/etc/systemd/system/`
   - Enable the service for automatic startup
   - Show you the service status

2. **Manual installation** (alternative method):
   ```bash
   # Copy the service file
   sudo cp timelapse.service /etc/systemd/system/
   
   # Edit the service file to match your setup
   sudo nano /etc/systemd/system/timelapse.service
   
   # Reload systemd and enable the service
   sudo systemctl daemon-reload
   sudo systemctl enable timelapse.service
   ```

#### Service Management

- **Check service status and get management commands**:
  ```bash
  ./service_status.sh
  ```

- **Start the service**:
  ```bash
  sudo systemctl start timelapse.service
  ```

- **Stop the service**:
  ```bash
  sudo systemctl stop timelapse.service
  ```

- **Check service status**:
  ```bash
  sudo systemctl status timelapse.service
  ```

- **View service logs**:
  ```bash
  sudo journalctl -u timelapse.service -f
  ```

- **Disable automatic startup**:
  ```bash
  sudo systemctl disable timelapse.service
  ```

#### Service Features

- **Automatic startup** at boot time
- **Automatic restart** if the application crashes
- **Proper logging** through systemd journal
- **Security hardening** with restricted permissions
- **Network dependency** - starts only after network is available

### Running Manually (Development)

For development or testing, you can still run the application manually:

```bash
python3 app.py
```
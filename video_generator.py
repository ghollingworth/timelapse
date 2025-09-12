#!/usr/bin/env python3
"""
Video Generator for Timelapse Images
Creates MP4 videos from captured timelapse images using OpenCV and FFmpeg.
"""

import os
import glob
import subprocess
import argparse
from datetime import datetime
import cv2
import numpy as np

def create_video_opencv(image_pattern, output_path, fps=30, quality=95, target_resolution=None):
    """
    Create video using OpenCV from image sequence.
    
    Args:
        image_pattern (str): Glob pattern for images (e.g., 'static/images/timelapse_*.jpg')
        output_path (str): Output video file path
        fps (int): Frames per second
        quality (int): Video quality (0-100)
        target_resolution (tuple): Target resolution (width, height) for video output
    """
    # Get sorted list of images
    images = sorted(glob.glob(image_pattern))
    
    if not images:
        print("No images found matching pattern:", image_pattern)
        return False
    
    # Read first image to get dimensions
    first_image = cv2.imread(images[0])
    if first_image is None:
        print("Error reading first image:", images[0])
        return False
    
    original_height, original_width, layers = first_image.shape
    
    # Determine output dimensions
    if target_resolution:
        width, height = target_resolution
        print(f"Scaling from {original_width}x{original_height} to {width}x{height}")
    else:
        height, width = original_height, original_width
        print(f"Using original resolution: {width}x{height}")
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print("Error creating video writer")
        return False
    
    print(f"Creating video with {len(images)} images at {fps} FPS...")
    
    # Process each image
    for i, image_path in enumerate(images):
        img = cv2.imread(image_path)
        if img is not None:
            # Scale image if target resolution is specified
            if target_resolution and (img.shape[1] != width or img.shape[0] != height):
                img = cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)
            
            out.write(img)
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(images)} images")
        else:
            print(f"Warning: Could not read image {image_path}")
    
    out.release()
    print(f"Video saved to: {output_path}")
    return True

def create_video_ffmpeg(image_pattern, output_path, fps=30, quality=23, target_resolution=None):
    """
    Create video using FFmpeg from image sequence.
    
    Args:
        image_pattern (str): Glob pattern for images (e.g., 'static/images/timelapse_*.jpg')
        output_path (str): Output video file path
        fps (int): Frames per second
        quality (int): Video quality (lower is better, 18-28 is good)
        target_resolution (tuple): Target resolution (width, height) for video output
    """
    # Get sorted list of images
    images = sorted(glob.glob(image_pattern))
    
    if not images:
        print("No images found matching pattern:", image_pattern)
        return False
    
    # Create FFmpeg command
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file
        '-framerate', str(fps),
        '-pattern_type', 'glob',
        '-i', image_pattern,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', str(quality),
        '-pix_fmt', 'yuv420p'
    ]
    
    # Add scaling if target resolution is specified
    if target_resolution:
        width, height = target_resolution
        cmd.extend(['-vf', f'scale={width}:{height}:flags=lanczos'])
        print(f"Scaling video to {width}x{height}")
    
    cmd.append(output_path)
    
    print(f"Creating video with {len(images)} images at {fps} FPS using FFmpeg...")
    print("Command:", ' '.join(cmd))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Video saved to: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        print(f"FFmpeg stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("FFmpeg not found. Please install FFmpeg first.")
        return False

def create_video_from_session(session_id, fps=30, method='ffmpeg', target_resolution=None):
    """
    Create video from a specific timelapse session.
    
    Args:
        session_id (str): Session ID to create video from
        fps (int): Frames per second
        method (str): 'ffmpeg' or 'opencv'
        target_resolution (tuple): Target resolution (width, height) for video output
    """
    image_pattern = f'static/images/timelapse_{session_id}_*.jpg'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'static/videos/timelapse_{session_id}_{timestamp}.mp4'
    
    # Ensure output directory exists
    os.makedirs('static/videos', exist_ok=True)
    
    if method == 'ffmpeg':
        return create_video_ffmpeg(image_pattern, output_path, fps, quality=23, target_resolution=target_resolution)
    else:
        return create_video_opencv(image_pattern, output_path, fps, quality=95, target_resolution=target_resolution)

def create_video_from_latest(fps=30, method='ffmpeg'):
    """
    Create video from the latest timelapse session.
    
    Args:
        fps (int): Frames per second
        method (str): 'ffmpeg' or 'opencv'
    """
    # Find all timelapse images
    images = glob.glob('static/images/timelapse_*.jpg')
    
    if not images:
        print("No timelapse images found")
        return False
    
    # Extract session IDs and find the latest
    session_ids = set()
    for image in images:
        parts = image.split('_')
        if len(parts) >= 3:
            session_ids.add(parts[1])
    
    if not session_ids:
        print("No valid session IDs found")
        return False
    
    latest_session = sorted(session_ids)[-1]
    print(f"Creating video from latest session: {latest_session}")
    
    return create_video_from_session(latest_session, fps, method)

def list_sessions():
    """List all available timelapse sessions."""
    images = glob.glob('static/images/timelapse_*.jpg')
    
    if not images:
        print("No timelapse images found")
        return
    
    session_info = {}
    
    for image in images:
        parts = image.split('_')
        if len(parts) >= 3:
            session_id = parts[1]
            if session_id not in session_info:
                session_info[session_id] = []
            session_info[session_id].append(image)
    
    print("Available timelapse sessions:")
    for session_id, images in sorted(session_info.items()):
        print(f"  Session {session_id}: {len(images)} images")

def main():
    parser = argparse.ArgumentParser(description='Create videos from timelapse images')
    parser.add_argument('--session', '-s', help='Session ID to create video from')
    parser.add_argument('--latest', '-l', action='store_true', help='Create video from latest session')
    parser.add_argument('--fps', '-f', type=int, default=30, help='Frames per second (default: 30)')
    parser.add_argument('--method', '-m', choices=['ffmpeg', 'opencv'], default='ffmpeg', 
                       help='Video creation method (default: ffmpeg)')
    parser.add_argument('--quality', '-q', type=int, default=23, help='Video quality (default: 23)')
    parser.add_argument('--list', action='store_true', help='List available sessions')
    parser.add_argument('--output', '-o', help='Output video file path')
    
    args = parser.parse_args()
    
    if args.list:
        list_sessions()
        return
    
    if args.session:
        if args.output:
            # Custom output path
            if args.method == 'ffmpeg':
                image_pattern = f'static/images/timelapse_{args.session}_*.jpg'
                create_video_ffmpeg(image_pattern, args.output, args.fps, args.quality)
            else:
                image_pattern = f'static/images/timelapse_{args.session}_*.jpg'
                create_video_opencv(image_pattern, args.output, args.fps, args.quality)
        else:
            # Default output path
            create_video_from_session(args.session, args.fps, args.method)
    elif args.latest:
        create_video_from_latest(args.fps, args.method)
    else:
        print("Please specify --session, --latest, or --list")
        parser.print_help()

if __name__ == '__main__':
    main() 
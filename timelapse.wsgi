#!/usr/bin/env python3
"""
WSGI entry point for Raspberry Pi Timelapse Controller
This file enables the Flask application to run under Apache with mod_wsgi.
"""

import sys
import os

# Add application directory to Python path
sys.path.insert(0, '/opt/timelapse')

# Set working directory for the application
os.chdir('/opt/timelapse')

# Import the Flask application
from app import app as application

# Ensure proper initialization for WSGI environment
if __name__ != '__main__':
    # When running under WSGI, we need to ensure the timelapse app is properly initialized
    from app import timelapse_app
    timelapse_app.start_scheduler()

# Make sure this works as a WSGI application
if __name__ == '__main__':
    application.run()

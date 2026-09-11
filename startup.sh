#!/bin/bash
set -e

# Update package lists
apt-get update

# Install unixODBC
apt-get install -y unixodbc-dev

# Pre-accept license for msodbcsql18
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install Python dependencies
pip install -r requirements.txt

# Use Azure-provided PORT (default to 8000 if not set)
PORT=${PORT:-8000}

# Start gunicorn on the correct port
gunicorn --bind=0.0.0.0:$PORT app:app

# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV YOLO_CONFIG_DIR=/app/config/ultralytics

# Install system dependencies including OpenCV requirements AND FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libv4l-0 \
    v4l-utils \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  

# Copy source code and data directory which contains models
COPY app.py .
COPY api/ api/
COPY config/ config/
COPY src/ src/
COPY data/ data/
COPY templates/ templates/

# Create runtime directories with proper permissions
# These will be used by the application during execution
RUN mkdir -p \
    /app/uploads/images \
    /app/uploads/videos \
    /app/runs/detect/track/images \
    /app/runs/detect/track/videos \
    && chmod -R 755 /app/uploads /app/runs

# Expose ports for Flask and debugger
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "300", "app:create_app()"]
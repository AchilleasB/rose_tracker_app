# Rose Tracker Application

A computer vision application for tracking and counting roses in images, videos, and real-time camera feeds using YOLOv11 and BoT-SORT tracking algorithm.

## Features

- Image tracking: Process and annotate images with rose detections
- Video tracking: Track roses in video files with frame-by-frame analysis
- Real-time tracking: Live rose tracking using webcam or camera feed
  - Supports browser-based camera access for remote deployment
  - Works with containerized environments like Docker
- Model retraining: Capability to retrain the model with new data
- Unique rose counting: Track and count unique roses across frames

## Prerequisites

- Python 3.8 or higher
- OpenCV
- Ultralytics YOLOv11
- Modern web browser with camera access capabilities (for browser-based tracking)

## Installation

### Option 1: Docker Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rose_tracker_app.git
cd rose_tracker_app
```

2. Build and Run the Docker image:
```bash
# Build
docker-compose --build

# Run
docker-compose up
```

3. Access the app at: http://localhost:5000

### Option 2: Local Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rose_tracker_app.git
cd rose_tracker_app
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

## Real-time Tracking Modes

The application supports two modes for real-time tracking:

### 1. Direct Camera Access (Local Development)

When running locally, the application can directly access your machine's camera using OpenCV. This mode is not suitable for containerized or server deployments.

### 2. Browser-based Camera Access (Remote/Docker Deployment)

For server or Docker deployments, the application uses browser-based camera access:
- The browser asks for permission to use the camera
- Camera frames are sent to the server for processing via secure HTTP requests
- Processed frames with tracking results are returned to the browser
- No direct camera access from the server is needed

This mode allows the application to run in environments where direct camera access is restricted or not possible.

## Project Structure

```
rose_tracker_app/
├── api/
│   └── controllers/         # API endpoints and request handling
│
├── config/
│   └── settings.py         # Application configuration
│
├── data/
│   └── best.pt            # Pre-trained YOLO model
│
├── src/
│   ├── models/            # Model-related code
│   ├── services/          # Core tracking services
│   └── utils/             # Utility functions
│
├── app.py                 # Main application entry point
├── docker-compose.yml     #  
├── Dockerfile            # Docker configuration
└── requirements.txt      # Python dependencies
```

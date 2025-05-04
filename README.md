# Rose Tracker Application

A computer vision application for tracking and counting roses in images, videos, and real-time camera feeds using YOLOv11 and BoT-SORT tracking algorithm.

## Features

- Image tracking: Process and annotate images with rose detections
- Video tracking: Track roses in video files with frame-by-frame analysis
- Real-time tracking: Live rose tracking using webcam or camera feed
- Model retraining: Capability to retrain the model with new data
- Unique rose counting: Track and count unique roses across frames

## Prerequisites

- Python 3.8 or higher
- OpenCV
- Ultralytics YOLOv11
- CUDA-capable GPU (recommended for real-time tracking)

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

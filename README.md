# Rose Tracker Application

A computer vision application for tracking and counting roses in images, videos, and real-time camera feeds using YOLOv11 and an improved IoU-based tracking algorithm.

## Features

- Image tracking: Process and annotate images with rose detections
- Video tracking: Track roses in video files with frame-by-frame analysis
- Real-time tracking: Live rose tracking using webcam or camera feed
  - Advanced IoU-based tracking for reliable rose identification
  - Real-time FPS display and performance monitoring
  - Unique rose counting with ID persistence
  - Modern, responsive UI with status indicators
  - Browser-based camera access for remote deployment
  - Works with containerized environments like Docker
- Model retraining: Capability to retrain the model with new data
- Unique rose counting: Track and count unique roses across frames with improved tracking algorithm

## Key Improvements

- **Enhanced Tracking Algorithm**: 
  - IoU-based tracking for more reliable rose identification
  - Active and inactive rose state management
  - Improved handling of occlusions and temporary disappearances
  - Configurable tracking timeouts for better accuracy

- **Real-time Performance**:
  - Live FPS counter showing processing speed
  - Visual feedback with rose IDs and bounding boxes
  - Status indicators for camera and tracking state
  - Error handling and user feedback

- **User Interface**:
  - Modern, responsive design
  - Real-time status updates
  - Visual feedback for tracking state
  - Error messages and loading indicators
  - Smooth animations and transitions

## Prerequisites

- Python 3.8 or higher
- OpenCV
- Ultralytics YOLOv11
- Modern web browser with camera access capabilities (for browser-based tracking)
- CUDA support recommended for better performance (optional)

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
docker-compose build

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

## Real-time Tracking Features

The application provides advanced real-time tracking capabilities:

### 1. Browser-based Camera Access

- Secure camera access through browser permissions
- Real-time frame processing with server-side detection
- Efficient frame transmission using base64 encoding
- Automatic error handling and recovery

### 2. Tracking Features

- **Rose Identification**:
  - Unique ID assignment for each detected rose
  - Persistent tracking across frames
  - Handling of temporary occlusions
  - Automatic cleanup of inactive roses

- **Performance Monitoring**:
  - Real-time FPS display
  - Processing status indicators
  - Error reporting and recovery
  - Resource usage optimization

- **User Interface**:
  - Live video feed with annotations
  - Rose count display
  - Processing FPS counter
  - Status indicators
  - Error messages
  - Loading states

## Project Structure

```
rose_tracker_app/
├── api/
│   └── controllers/         # API endpoints and request handling
│       ├── image_tracking_controller.py
│       ├── video_tracking_controller.py
│       ├── realtime_tracking_controller.py
│       └── model_retraining_controller.py
│
├── config/
│   ├── settings.py         # Application configuration
│   └── yolo_botsort.py     # Tracking algorithm configuration
│
├── data/
│   └── best.pt            # Pre-trained YOLO model
│
├── src/
│   ├── models/            # Model-related code
│   │   └── rose_tracker.py
│   ├── services/          # Core tracking services
│   │   ├── tracking_service/
│   │   │   ├── base_tracking_service.py
│   │   │   ├── image_tracking_service.py
│   │   │   ├── video_tracking_service.py
│   │   │   └── realtime_tracking_service.py
│   │   └── training_service/
│   │       └── model_training_service.py
│   └── utils/             # Utility functions
│       ├── file_handler.py
│       └── tracking_processor.py
│
├── templates/             # HTML templates
│   └── realtime_stream.html
│
├── app.py                # Main application entry point
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile.dev        # Development Docker configuration
└── requirements.txt      # Python dependencies
```

## Usage

1. **Starting the Application**:
   - Launch the application using Docker or local setup
   - Access the web interface at http://localhost:5000
   - Navigate to the real-time tracking page

2. **Real-time Tracking**:
   - Click "Start Camera" to begin tracking
   - Allow camera access when prompted
   - Monitor the live feed with rose detections
   - View real-time FPS and rose count
   - Click "Stop Camera" to end tracking

3. **Tracking Features**:
   - Each detected rose is assigned a unique ID
   - IDs persist across frames for consistent tracking
   - Inactive roses are automatically managed
   - Performance metrics are displayed in real-time

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

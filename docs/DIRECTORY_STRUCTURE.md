# Rose Tracker Application Directory Structure

This document outlines the directory structure of the Rose Tracker application and explains the purpose of each directory.

## Root Directory Structure

```
.
├── api/                    # API endpoints and route handlers
├── config/                 # Configuration files and settings
├── data/                   # Data storage and model files
├── docs/                   # Documentation files
├── runs/                   # Tracking outputs
├── src/                    # Source code and business logic
├── templates/              # HTML templates
├── uploads/                # Temporary upload storage
└── venv/                  # Python virtual environment
```

## Key Directories and Their Purposes

### 1. Data Storage (`data/`)
```
data/
├── models/            # Stored model weights and metadata
│   ├── best.pt       # Default model for inference
│   └── model_metadata.json  # Model version tracking
├── annotated_images/  # Training data and annotations
│   ├── images/       # Original and annotated images
│   ├── videos/       # Original and annotated video frames
│   └── annotations/  # YOLO format annotations
└── training_outputs/ # Training artifacts and logs
```
- `models/`: Stores all model weights and metadata
  - `best.pt`: The default model used for inference
  - `model_metadata.json`: Tracks model versions and metrics
- `annotated_images/`: Contains training data and YOLO format annotations
- `training_outputs/`: Training artifacts (cleaned after training)

### 2. Tracking Outputs (`runs/detect/`)
```
runs/
└── detect/
    └── track/
        ├── images/    # Annotated images from tracking
        ├── video/     # Annotated videos from tracking
        └── webcam/    # Webcam tracking outputs
```
- `track/images/`: Stores annotated images from image tracking
- `track/video/`: Stores annotated videos from video tracking
- `track/webcam/`: Stores outputs from real-time webcam tracking

### 3. Upload Storage (`uploads/`)
```
uploads/
├── images/          # Temporary storage for uploaded images
└── videos/          # Temporary storage for uploaded videos
```
- `images/`: Temporary storage for uploaded image files
- `videos/`: Temporary storage for uploaded video files

### 4. Source Code (`src/`)
```
src/
├── models/   
│   └── rose_tracker.py    
├── services/        # Business logic and services
│   ├── model_retrainer.py    # Model retraining service
│   └── tracking_service.py   # Video tracking service
├── utils/          # Utility functions and helpers
└── yolo_botsort/          # DOwnload and modify botsort threshold values
```
- `services/`: Implements business logic and core services
  - `model_retrainer.py`: Handles model retraining workflow
  - `tracking_service.py`: Manages video tracking operations
- `utils/`: Contains utility functions and helper methods

### 5. API Endpoints (`api/`)
```
api/
├── retrain_model.py     # Model retraining endpoints
├── tracking.py          # Video tracking endpoints
└── upload.py           # File upload endpoints
```
- Contains all API endpoints and route handlers
- Each file corresponds to a specific functionality

### 6. Configuration (`config/`)
```
config/
├── settings.py          # Application settings and paths
└── .env                # Environment variables (not tracked)
```
- Contains all configuration files
- Settings are loaded from environment variables with defaults

## File Flow

1. **Image/Video Upload**:
   - Files are temporarily stored in `uploads/`
   - Processed and annotated versions are saved in `runs/detect/track/`

2. **Model Training**:
   - Training data is stored in `data/annotated_images/`
   - Training outputs are temporarily stored in `data/training_outputs/`
   - Best model is saved to `data/models/` with metadata

3. **Tracking**:
   - Uses model from `data/models/` or `data/best.pt`
   - Outputs annotated files to `runs/detect/track/`

## Notes

- The `runs/detect/track/` directory is used exclusively for tracking outputs
- Training outputs are temporary and cleaned up after training
- Upload directory is for temporary storage of user-uploaded files
- All paths are configurable through environment variables in `config/settings.py`
- Model metadata is tracked in `data/models/model_metadata.json`
- Annotations are stored in YOLO format with corresponding image/video frames
- All necessary directories are created automatically by `Settings.validate()` 
import os
from pathlib import Path

class Settings:
    """
    Application settings and configuration.
    Contains all the necessary paths and configuration variables used throughout the application.
    """
    def __init__(self):
        # Base directories
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = os.path.join(self.BASE_DIR, 'data')
        self.MODELS_DIR = os.path.join(self.DATA_DIR, 'models')
        self.ANNOTATED_DATA_DIR = os.path.join(self.DATA_DIR, 'annotated_images')
        self.TRAINING_OUTPUT_DIR = os.path.join(self.DATA_DIR, 'training_outputs')
        
        # Model paths and configuration
        self.DEFAULT_MODEL = os.path.join(self.DATA_DIR, 'best.pt')
        self.MODEL_METADATA_FILE = os.path.join(self.MODELS_DIR, 'model_metadata.json')
        self.TRACKER_CONFIG_PATH = os.path.join(self.BASE_DIR, 'config', 'modified_botsort.yaml')
        self.BOTSORT_CONFIG_URL = "https://raw.githubusercontent.com/NirAharon/BoT-SORT/main/configs/botsort.yaml"
        
        # Tracking configuration
        self.TRACKING_CONFIDENCE = 0.8
        self.TRACKING_IOU = 0.6
            
        # Upload directories
        self.UPLOAD_IMAGES_DIR = os.path.join(self.BASE_DIR, 'uploads', 'images')
        self.UPLOAD_VIDEOS_DIR = os.path.join(self.BASE_DIR, 'uploads', 'videos')
        
        # Tracking output directories
        self.TRACKING_IMAGES_DIR = os.path.join(self.BASE_DIR, 'runs', 'detect', 'track', 'images')
        self.TRACKING_VIDEOS_DIR = os.path.join(self.BASE_DIR, 'runs', 'detect', 'track', 'videos')
        
        # Allowed file extensions
        self.ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}
        self.ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}
        
        # Create necessary directories
        self._create_directories()
    
    def _create_directories(self):
        """Create all necessary directories if they don't exist."""
        directories = [
            self.MODELS_DIR,
            self.ANNOTATED_DATA_DIR,
            self.TRAINING_OUTPUT_DIR,
            self.UPLOAD_IMAGES_DIR,
            self.UPLOAD_VIDEOS_DIR,
            self.TRACKING_IMAGES_DIR,
            self.TRACKING_VIDEOS_DIR,
            os.path.join(self.ANNOTATED_DATA_DIR, 'images'),
            os.path.join(self.ANNOTATED_DATA_DIR, 'annotations'),
            os.path.join(self.ANNOTATED_DATA_DIR, 'videos')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True) 
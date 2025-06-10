import os
from pathlib import Path
import torch
import logging

logger = logging.getLogger(__name__)

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
        self.TRAINING_OUTPUT_DIR = os.path.join(self.DATA_DIR, 'training_outputs')
        
        # Model paths and configuration
        self.DEFAULT_MODEL = os.path.join(self.DATA_DIR, 'best_small.pt')
        self.MODEL_METADATA_FILE = os.path.join(self.MODELS_DIR, 'model_metadata.json')
        self.TRACKER_CONFIG_PATH = os.path.join(self.BASE_DIR, 'config', 'modified_botsort.yaml')
        self.BOTSORT_CONFIG_URL = "https://raw.githubusercontent.com/NirAharon/BoT-SORT/main/configs/botsort.yaml"
        
        # Tracking configuration
        self.TRACKING_CONFIDENCE = 0.8
        self.TRACKING_IOU = 0.6
            
        # Upload directories
        self.UPLOADS_DIR = os.path.join(self.BASE_DIR, 'uploads')
        self.UPLOAD_IMAGES_DIR = os.path.join(self.UPLOADS_DIR, 'images')
        self.UPLOAD_VIDEOS_DIR = os.path.join(self.UPLOADS_DIR, 'videos')
        
        # Tracking output directories
        self.TRACKING_IMAGES_DIR = os.path.join(self.BASE_DIR, 'runs', 'detect', 'track', 'images')
        self.TRACKING_VIDEOS_DIR = os.path.join(self.BASE_DIR, 'runs', 'detect', 'track', 'videos')
        
        # Allowed file extensions
        self.ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}
        self.ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}
       
        # Device configuration (CPU or GPU)
        self.DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.DEVICE}")

        # Create necessary directories
        self._create_directories()
        
        # Verify model files exist
        self._verify_model_files()
    
    def _create_directories(self):
        """Create all necessary directories if they don't exist."""
        # Only create runtime directories, as data directory is included in container
        runtime_directories = [
            self.UPLOAD_IMAGES_DIR,
            self.UPLOAD_VIDEOS_DIR,
            self.TRACKING_IMAGES_DIR,
            self.TRACKING_VIDEOS_DIR
        ]
        
        for directory in runtime_directories:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Ensured directory exists: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {str(e)}")
                raise

    def _verify_model_files(self):
        """Verify that required model files exist."""
        required_files = [
            (self.DEFAULT_MODEL, "Default model"),
            (self.TRACKER_CONFIG_PATH, "Tracker config")
        ]
        
        for file_path, file_desc in required_files:
            if not os.path.exists(file_path):
                logger.error(f"{file_desc} not found at: {file_path}")
                raise FileNotFoundError(f"{file_desc} not found at: {file_path}")
            logger.info(f"Found {file_desc} at: {file_path}") 

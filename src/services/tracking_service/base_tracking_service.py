from abc import ABC, abstractmethod
import os
from ultralytics import YOLO
from src.models.rose_tracker import RoseTrackerModel
from src.utils.file_handler import FileHandler
from src.utils.tracking_processor import TrackingProcessor

class BaseTrackingService(ABC):
    """Base class for all tracking services"""
    
    def __init__(self):
        rose_tracker_model = RoseTrackerModel()
        self.model = YOLO(rose_tracker_model.model)
        self.tracker = rose_tracker_model.tracker
        self.conf = rose_tracker_model.conf
        self.iou = rose_tracker_model.iou
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        self.video_extensions = ['.mp4', '.avi', '.mov', '.mkv']

    # Ensure the directory exists
    def ensure_directory(self, path):
        """Ensure the directory exists"""
        os.makedirs(path, exist_ok=True)

    # Validate that the input source exists
    def validate_input_source(self, input_source):
        """Validate that the input source exists"""
        if not os.path.exists(input_source):
            raise FileNotFoundError(f"Input source not found: {input_source}")

    # Validate that the input source is a valid image file  
    def validate_image_source(self, input_source):
        """Validate that the input source is a valid image file"""
        self.validate_input_source(input_source)
        if not FileHandler.validate_extension(input_source, self.image_extensions):
            raise ValueError(f"Invalid image format. Supported formats: {', '.join(self.image_extensions)}")

    # Validate that the input source is a valid video file
    def validate_video_source(self, input_source):
        """Validate that the input source is a valid video file"""
        if not isinstance(input_source, int):  # Skip validation for webcam
            self.validate_input_source(input_source)
            if not FileHandler.validate_extension(input_source, self.video_extensions):
                raise ValueError(f"Invalid video format. Supported formats: {', '.join(self.video_extensions)}")

    # Generate the output path for the processed image
    def get_image_output_path(self, input_source, output_dir):
        """Generate output path based on input source"""
        filename = os.path.basename(input_source)
        return os.path.join(output_dir, filename)

    # Generate the output path for the processed video
    def get_video_output_path(self, input_source, output_path):
        """Generate the output path for the processed video."""
        if isinstance(input_source, int):
            return os.path.join(output_path, 'webcam_output.mp4')
        else:  # Video file
            return os.path.join(output_path, os.path.basename(input_source))

    # Read an image file using FileHandler
    def read_image(self, file_path):
        """Read an image file using FileHandler"""
        self.validate_image_source(file_path)
        return FileHandler.read_image(file_path)

    # Read a video file using FileHandler
    def read_video(self, file_path):
        """Read a video file using FileHandler"""
        self.validate_video_source(file_path)
        return FileHandler.read_video(file_path)

    # Save an image file using FileHandler
    def save_image(self, file_path, image):
        """Save an image file using FileHandler"""
        self.ensure_directory(os.path.dirname(file_path))
        FileHandler.save_image(file_path, image)

    # Save a video file using FileHandler
    def save_video(self, file_path, frames, fps):
        """Save a video file using FileHandler"""
        self.ensure_directory(os.path.dirname(file_path))
        FileHandler.save_video(file_path, frames, fps)

    # Get the number of roses from the tracking results
    def get_number_of_roses(self, all_results):
        """Count unique rose IDs from tracking results"""
        if all_results:
            number_of_roses = TrackingProcessor.count_unique_ids(all_results)
        else:
            print("No results to process.")
            number_of_roses = 0
        return number_of_roses 
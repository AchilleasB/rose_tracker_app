import os
import cv2
from typing import Union, List, Tuple

class FileHandler:
    """Utility class for file operations"""
    
    @staticmethod
    def read_image(file_path: str) -> Union[cv2.Mat, None]:
        """Read an image file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Failed to read image: {file_path}")
        return img

    @staticmethod
    def read_video(file_path: str) -> Tuple[cv2.VideoCapture, float, Tuple[int, int]]:
        """Read a video file and return capture object and properties"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
        
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {file_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        fps = fps if fps > 0 else 30
        
        # Get frame dimensions
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return cap, fps, (width, height)

    @staticmethod
    def save_image(file_path: str, image: cv2.Mat) -> None:
        """Save an image file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not cv2.imwrite(file_path, image):
            raise ValueError(f"Failed to save image: {file_path}")

    @staticmethod
    def save_video(file_path: str, frames: List[cv2.Mat], fps: float) -> None:
        """Save a video file"""
        if not frames:
            raise ValueError("No frames to save")
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        height, width = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(file_path, fourcc, fps, (width, height))
        
        for frame in frames:
            out.write(frame)
        out.release()

    @staticmethod
    def validate_extension(file_path: str, allowed_extensions: List[str]) -> bool:
        """Validate file extension"""
        return file_path.lower().endswith(tuple(allowed_extensions)) 
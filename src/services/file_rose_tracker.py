"""
Rose Tracker Service Module

This module provides a service for tracking roses in images and videos using YOLOv11 and a tracker.
It handles the initialization of the YOLO model and tracker, and provides methods for tracking roses in different input sources.
"""

import os
import cv2
from ultralytics import YOLO
from src.utils import count_unique_ids
from src.models.rose_tracker import RoseTrackerModel

class RoseTrackerService:
    """
    Service class for tracking roses in images and videos using YOLOv11 and a tracker.
    """
    def __init__(self):
        rose_tracker_model = RoseTrackerModel()
        self.model = YOLO(rose_tracker_model.model)
        self.tracker = rose_tracker_model.tracker
        self.conf = rose_tracker_model.conf
        self.iou = rose_tracker_model.iou

    def _track_image(self, input_source, output_path):
        """
        Tracks roses in an image file and saves the annotated image.

        """
        # # Ensure the input path exists
        if not os.path.exists(input_source):
            raise FileNotFoundError(f"Input image not found: {input_source}")
            
        # Read the image
        img = cv2.imread(input_source)
        if img is None:
            raise ValueError(f"Failed to read the image: {input_source}")
            
        # Process the image with YOLO
        results = self.model.track(
            source=img,
            tracker=self.tracker,
            conf=self.conf,
            iou=self.iou,
            persist=True)
        
        # Create annotated frame
        annotated_frame = results[0].plot()
        if annotated_frame is None:
            raise ValueError("Failed to annotate the image")
        
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Save the annotated image
        filename = os.path.basename(input_source)
        image_output = os.path.join(output_path, filename)
        cv2.imwrite(image_output, annotated_frame)

        # Get number of roses detected
        number_of_roses = self.get_number_of_roses(results)
        print(f"Image processed and saved: {image_output}")

        return image_output, number_of_roses

    def _track_video(self, input_source, output_path):
        """
        Tracks roses in a video file and saves the annotated video.
        """
        cap = cv2.VideoCapture(input_source)

        # Read first frame to get properties
        success, frame = cap.read()
        if not success:
            raise ValueError("Failed to read from video source.")
            return
        
        # Get video properties
        height, width = frame.shape[:2]
        fps = cap.get(cv2.CAP_PROP_FPS)
        fps = fps if fps > 0 else 30

        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        video_output = self.get_video_output_path(input_source, output_path)
        out = cv2.VideoWriter(video_output, fourcc, fps, (width, height))

        # Initialize the tracker
        all_results = []

        try:
            while success:
                results = self.model.track(
                    source=frame,
                    tracker=self.tracker,
                    conf=self.conf,
                    iou=self.iou,
                    persist=True
                )

                # Process results and save to video
                all_results.extend(results)
                annotated_frame = results[0].plot()
                out.write(annotated_frame)

                # Process the next frame until the end of the video
                success, frame = cap.read()
            
            number_of_roses = self.get_number_of_roses(all_results)
            
        except KeyboardInterrupt:
            print("\nTracking interrupted. Exiting gracefully.")
        finally:
            cap.release()
            out.release()

        print("Video processed and saved:", video_output, "Number of roses:", number_of_roses)
        return video_output, number_of_roses

    # Helper functions
    def get_number_of_roses(self, all_results):
        """
        Count unique rose IDs from tracking results
        """ 
        if all_results:
            number_of_roses = count_unique_ids(all_results)
        else:
            print("No results to process.")
            number_of_roses = 0
        return number_of_roses

    def get_video_output_path(self, input_source, output_path):
        """
        Generate the output path for the processed video.
        """
        if isinstance(input_source, int):
            return os.path.join(output_path, 'webcam_output.mp4')
        else:  # Video file
            return os.path.join(output_path, os.path.basename(input_source))
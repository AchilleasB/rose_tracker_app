"""
Real-time Rose Tracking Service

This module provides a service specifically for real-time rose tracking operations using a webcam.
It handles the streaming of frames, rose detection, and count management.
"""

import cv2
import time
from src.models.rose_tracker import RoseTrackerModel
from ultralytics import YOLO

class RealtimeTrackerService:
    """Service class for real-time rose tracking operations."""
    
    def __init__(self):
        """Initialize the real-time tracker with YOLO model and tracking parameters."""
        rose_tracker_model = RoseTrackerModel()
        self.model = YOLO(rose_tracker_model.model)
        self.tracker = rose_tracker_model.tracker
        self.conf = rose_tracker_model.conf
        self.iou = rose_tracker_model.iou
        
        # Count management
        self.latest_count = 0
        self.last_count_update = 0
        self.COUNT_UPDATE_INTERVAL = 10  # seconds
        self.tracked_roses = set()  # Store unique rose IDs
        self.current_frame_roses = set()  # Roses in current frame
        self.is_tracking = False
        self.cap = None

    def track_realtime(self, input_source=0):
        """Start real-time tracking and yield processed frames."""
        print("Initializing camera...")
        self.cap = cv2.VideoCapture(input_source)
        self.is_tracking = True
        
        if not self.cap.isOpened():
            print("Failed to open camera")
            return

        print("Camera initialized successfully")
        
        try:
            while self.cap.isOpened() and self.is_tracking:
                success, frame = self.cap.read()
                if not success:
                    print("Failed to read frame")
                    continue

                # Process frame through YOLO model with tracking
                try:
                    results = self.model.track(
                        source=frame,
                        tracker=self.tracker,
                        conf=self.conf,
                        iou=self.iou,
                        persist=True
                    )

                    # Update rose count tracking if results are valid
                    if results and len(results) > 0 and hasattr(results[0], 'boxes'):
                        self._track_detections(results[0].boxes)
                        annotated_frame = results[0].plot()
                    else:
                        annotated_frame = frame  # Use original frame if detection fails
                        print("No detection results for this frame")

                except Exception as e:
                    print(f"Warning: Detection error: {str(e)}")
                    annotated_frame = frame  # Use original frame if detection fails
                
                # Always yield a frame, whether it's annotated or original
                yield annotated_frame

            print("Tracking stopped")
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
        finally:
            self.stop_tracking()

    def stop_tracking(self):
        """Stop tracking and release resources."""
        print("Stopping tracking...")
        self.is_tracking = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        print("Camera resources released")

    def _track_detections(self, boxes):
        """Track rose detections and maintain cumulative count."""
        current_time = time.time()
        self.current_frame_roses.clear()
        
        # Process current frame detections
        if boxes and len(boxes) > 0:
            try:
                # Check if tracking IDs are available and valid
                if hasattr(boxes, 'id') and boxes.id is not None:
                    track_ids = boxes.id.cpu().numpy().tolist()
                    if track_ids:  # Ensure we have valid IDs
                        self.current_frame_roses.update(track_ids)
                        self.tracked_roses.update(track_ids)
                        print(f"Current frame roses: {len(self.current_frame_roses)}, Total unique roses: {len(self.tracked_roses)}")
            except Exception as e:
                print(f"Warning: Could not process tracking IDs: {str(e)}")
                # If tracking fails, we'll just count the detections
                detection_count = len(boxes)
                print(f"Falling back to detection count: {detection_count}")

        # Update count if interval has passed
        time_since_update = current_time - self.last_count_update
        if time_since_update >= self.COUNT_UPDATE_INTERVAL:
            self._update_count()

    def _update_count(self):
        """Update the latest count based on total unique roses tracked."""
        self.latest_count = len(self.tracked_roses)
        self.last_count_update = time.time()
        print(f"Total unique roses tracked: {self.latest_count} at {time.strftime('%H:%M:%S')}")

    def get_latest_count(self):
        """Get the latest rose count and timestamp."""
        return {
            "count": self.latest_count,
            "timestamp": self.last_count_update
        } 
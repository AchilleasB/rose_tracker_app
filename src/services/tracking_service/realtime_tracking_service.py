from src.services.tracking_service.base_tracking_service import BaseTrackingService
import cv2
import time
import numpy as np
from collections import defaultdict
import os
from config.settings import Settings

class RealtimeTrackingService(BaseTrackingService):
    """Service for real-time rose tracking operations."""
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.latest_count = 0
        self.last_count_update = 0
        self.COUNT_UPDATE_INTERVAL = 10  # seconds
        self.tracked_roses = set()  # Store unique rose IDs
        self.current_frame_roses = set()  # Roses in current frame
        self.is_tracking = False
        self.input_frame = None

        # FPS calculation
        self.last_inference_time = 0
        self.inference_fps = 0

    def stop_tracking(self):
        """Stop tracking and release resources."""
        print("Stopping tracking...")
        self.is_tracking = False
        print("Camera resources released")

    def get_latest_count(self):
        """Get the latest rose count and tracking information."""
        return {
            "count": self.latest_count,
            "timestamp": self.last_count_update,
            "fps": round(self.inference_fps, 2),
            "tracked_roses": getattr(self, '_last_tracked_roses', [])
        }
    

    ### IMPLEMENTATION WITH YOLO TRACKING

    def track_realtime(self, input_frame):
        """Process a single frame using YOLO's built-in tracking."""
        if input_frame is None:
            return None
            
        self.is_tracking = True
        
        try:
            # Update FPS
            self._update_fps()

            # Process frame through YOLO model with tracking
            results = self.model.track(
                source=input_frame,
                tracker=self.tracker,
                conf=self.conf,
                iou=self.iou,
                persist=True
            )

            if results and len(results) > 0 and hasattr(results[0], 'boxes'):
                # Process detections
                tracked_roses = self._process_detections(results[0].boxes)
                
                # Update counts
                self._update_counts(tracked_roses)
                
                # Get annotated frame and add overlays
                annotated_frame = results[0].plot()
                if annotated_frame is not None:
                    annotated_frame = self._add_overlays(annotated_frame)
                else:
                    annotated_frame = input_frame
                
            else:
                annotated_frame = input_frame
                self._update_counts([])
                
        except Exception as e:
            annotated_frame = input_frame
            self._update_counts([])
        
        return annotated_frame

    def _process_detections(self, boxes):
        """Process detection boxes and extract tracking information."""
        tracked_roses = []
        if boxes and len(boxes) > 0:
            for box in boxes:
                if hasattr(box, 'id') and box.id is not None:
                    track_id = int(box.id[0].cpu().numpy())
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    
                    tracked_roses.append({
                        'id': track_id,
                        'bbox': [x1, y1, x2, y2],
                        'confidence': confidence
                    })
                    
                    # Update tracking sets
                    self.current_frame_roses.add(track_id)
                    self.tracked_roses.add(track_id)
        return tracked_roses
    
    def _add_overlays(self, frame):
        """Add FPS and rose count overlays to the frame."""
        if frame is not None:
            # Add FPS counter
            cv2.putText(frame, f"FPS: {self.inference_fps:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Add rose count
            cv2.putText(frame, f"Roses: {self.latest_count}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return frame
    
    def _update_fps(self):
        """Update the FPS calculation."""
        current_time = time.time()
        if self.last_inference_time > 0:
            self.inference_fps = 1 / (current_time - self.last_inference_time)
        self.last_inference_time = current_time

    def _update_counts(self, tracked_roses):
        """Update rose counts and tracking information."""
        current_time = time.time()
        self.latest_count = len(self.tracked_roses)
        self.last_count_update = current_time
        self._last_tracked_roses = tracked_roses
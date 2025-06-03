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
        # Count management
        self.latest_count = 0
        self.last_count_update = 0
        self.COUNT_UPDATE_INTERVAL = 10  # seconds
        self.tracked_roses = set()  # Store unique rose IDs
        self.current_frame_roses = set()  # Roses in current frame
        self.is_tracking = False
        self.cap = None
        self.input_frame = None

        # FPS calculation
        self.last_inference_time = 0
        self.inference_fps = 0
        
        # # Rose tracking
        # self.next_rose_id = 1
        # self.active_roses = {}  # Dictionary to store active roses and their last seen position
        # self.inactive_roses = {}  # Dictionary to store recently inactive roses and their last known position
        # self.last_update_time = time.time()
        # self.ROSE_TIMEOUT = 2.0  # Time in seconds after which a rose is considered inactive
        # self.INACTIVE_TIMEOUT = 5.0  # Time in seconds after which an inactive rose is forgotten

    def compute_iou(self, box1, box2):
        """Compute IoU between two bounding boxes."""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = box1_area + box2_area - intersection
        
        return intersection / union if union > 0 else 0

    def update_rose_tracking(self, detections, iou_threshold=0.5):
        """Update rose tracking and assign IDs to new roses."""
        current_time = time.time()
        
        # Move inactive roses to inactive_roses dictionary
        for rose_id, data in list(self.active_roses.items()):
            if current_time - data['last_seen'] >= self.ROSE_TIMEOUT:
                self.inactive_roses[rose_id] = {
                    'bbox': data['bbox'],
                    'last_seen': data['last_seen']
                }
                del self.active_roses[rose_id]
        
        # Remove roses that have been inactive for too long
        self.inactive_roses = {rose_id: data for rose_id, data in self.inactive_roses.items() 
                             if current_time - data['last_seen'] < self.INACTIVE_TIMEOUT}
        
        # Sort detections by confidence score
        sorted_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        tracked_detections = []
        used = [False] * len(sorted_detections)
        
        # First, try to match with active roses
        for i, det in enumerate(sorted_detections):
            if used[i]:
                continue
                
            best_iou = 0
            best_rose_id = None
            
            # Find the best matching active rose
            for rose_id, rose_data in self.active_roses.items():
                iou = self.compute_iou(det['bbox'], rose_data['bbox'])
                if iou > iou_threshold and iou > best_iou:
                    best_iou = iou
                    best_rose_id = rose_id
            
            if best_rose_id is not None:
                # Update existing active rose
                det['rose_id'] = best_rose_id
                self.active_roses[best_rose_id] = {
                    'bbox': det['bbox'],
                    'last_seen': current_time
                }
                used[i] = True
                tracked_detections.append(det)
                continue
            
            # If no match with active roses, try matching with inactive roses
            for rose_id, rose_data in self.inactive_roses.items():
                iou = self.compute_iou(det['bbox'], rose_data['bbox'])
                if iou > iou_threshold and iou > best_iou:
                    best_iou = iou
                    best_rose_id = rose_id
            
            if best_rose_id is not None:
                # Reactivate inactive rose
                det['rose_id'] = best_rose_id
                self.active_roses[best_rose_id] = {
                    'bbox': det['bbox'],
                    'last_seen': current_time
                }
                del self.inactive_roses[best_rose_id]
                used[i] = True
                tracked_detections.append(det)
        
        # Assign new IDs to unmatched detections
        for i, det in enumerate(sorted_detections):
            if not used[i]:
                det['rose_id'] = self.next_rose_id
                self.active_roses[self.next_rose_id] = {
                    'bbox': det['bbox'],
                    'last_seen': current_time
                }
                self.next_rose_id += 1
                tracked_detections.append(det)
        
        self.last_update_time = current_time
        return tracked_detections

    def process_single_frame(self, frame):
        """Process a single frame through the tracking model"""
        if frame is None:
            print("Received None frame")
            return frame
            
        try:
            # Calculate inference FPS
            current_time = time.time()
            if self.last_inference_time > 0:
                self.inference_fps = 1 / (current_time - self.last_inference_time)
            self.last_inference_time = current_time

            # Perform inference
            results = self.model(frame, verbose=False)[0]
            
            # Process results
            detections = []
            for box in results.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                # Only include detections with confidence >= 40%
                if confidence >= 0.4:
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = results.names[class_id]
                    
                    detections.append({
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': confidence,
                        'class': class_name
                    })
            
            # Update rose tracking and get tracked detections
            tracked_detections = self.update_rose_tracking(detections)
            
            # Draw detections on frame
            for det in tracked_detections:
                x1, y1, x2, y2 = map(int, det['bbox'])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Rose {det['rose_id']}", (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Add FPS counter
            cv2.putText(frame, f"FPS: {self.inference_fps:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Update count
            self.latest_count = len(self.active_roses) + len(self.inactive_roses)
            self.last_count_update = current_time

        except Exception as e:
            print(f"Warning: Detection error: {str(e)}")
        
        return frame

    def stop_tracking(self):
        """Stop tracking and release resources."""
        print("Stopping tracking...")
        self.is_tracking = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
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
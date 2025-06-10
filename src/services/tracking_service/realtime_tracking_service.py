import base64
from src.services.tracking_service.base_tracking_service import BaseTrackingService
import cv2
import time
import numpy as np
from collections import defaultdict
import os
from config.settings import Settings
import uuid
import logging

logger = logging.getLogger(__name__)

class RealtimeTrackingService(BaseTrackingService):
    """Service for real-time rose tracking operations."""
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.active_sessions = {}  # Store active tracking sessions
        self.COUNT_UPDATE_INTERVAL = 2.0  # Update count every 2 seconds
        self.is_tracking = False
        self.input_frame = None
        self.inference_fps = 0.0  # Initialize FPS
        self.last_inference_time = 0.0  # Initialize last inference time
        
        # Persistent tracking data across all sessions
        self.persistent_data = {
            'total_unique_roses': set(),  # All unique roses ever seen
            'session_history': [],  # List of completed sessions
            'last_session_id': None,  # Track the last active session
            'next_session_number': 1,  # Track the next session number
            'cumulative_unique_roses': 0  # Running total of unique roses across all sessions
        }

    def start_session(self):
        """Initialize a new tracking session"""
        try:
            session_id = str(uuid.uuid4())
            session_number = self.persistent_data['next_session_number']
            
            self.active_sessions[session_id] = {
                'start_time': time.time(),
                'last_update': time.time(),
                'last_count_update': time.time(),
                'display_count': 0,  # Smoothed count for display
                'frame_counts': [],  # Store recent frame counts for smoothing
                'session_unique_roses': set(),  # Unique roses in this session
                'frame_count': 0,
                'session_number': session_number
            }
            
            # Increment the next session number
            self.persistent_data['next_session_number'] += 1
            self.persistent_data['last_session_id'] = session_id
            logger.info(f"Started new session: {session_id} (Session #{session_number})")
            
            return session_id
        except Exception as e:
            logger.error(f"Failed to start session: {str(e)}")
            raise RuntimeError(f"Failed to start session: {str(e)}")

    def stop_session(self, session_id):
        """End a tracking session and return final statistics"""
        if session_id not in self.active_sessions:
            logger.warning(f"Attempted to stop invalid session: {session_id}")
            raise ValueError("Invalid session ID")
            
        session = self.active_sessions[session_id]
        duration = time.time() - session['start_time']
        
        # Get session unique roses count
        session_unique_count = len(session['session_unique_roses'])
        
        # Update persistent data
        self.persistent_data['total_unique_roses'].update(session['session_unique_roses'])
        # Update cumulative count
        self.persistent_data['cumulative_unique_roses'] += session_unique_count
        
        session_stats = {
            "session_number": session['session_number'],
            "session_unique_roses": session_unique_count,
            "total_unique_roses": self.persistent_data['cumulative_unique_roses'],  # Use cumulative count
            "duration": duration,
            "average_fps": session['frame_count'] / duration if duration > 0 else 0,
            "total_frames_processed": session['frame_count']
        }
        
        # Store session history
        self.persistent_data['session_history'].append({
            'session_id': session_id,
            'stats': session_stats,
            'end_time': time.time()
        })
        
        # Stop tracking and cleanup
        self.stop_tracking()
        del self.active_sessions[session_id]
        logger.info(f"Stopped session: {session_id} (Session #{session['session_number']})")
        
        return session_stats

    def get_session_stats(self, session_id):
        """Get current statistics for a specific session"""
        if session_id not in self.active_sessions:
            raise ValueError("Invalid session ID")
            
        session = self.active_sessions[session_id]
        session_unique_count = len(session['session_unique_roses'])
        
        return {
            "session_number": session['session_number'],
            "session_unique_roses": session_unique_count,
            "total_unique_roses": self.persistent_data['cumulative_unique_roses'] + session_unique_count,  # Include current session in total
            "duration": time.time() - session['start_time'],
            "average_fps": session['frame_count'] / (time.time() - session['start_time']) if (time.time() - session['start_time']) > 0 else 0,
            "total_frames_processed": session['frame_count']
        }

    def _decode_image(self, image_data):
        """Helper method to decode base64 image data"""
        if not image_data:
            raise ValueError("No image data received")

        if ',' in image_data:
            image_data = image_data.split(',')[1]
            
        try:
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("Failed to decode image")
            return frame
        except Exception as e:
            raise ValueError(f"Invalid image data: {str(e)}")
        
    def process_frame(self, session_id, frame):
        """Process a single frame for a given session"""
        if session_id not in self.active_sessions:
            logger.warning(f"Invalid session ID used in process_frame: {session_id}")
            raise ValueError("Invalid session ID")
            
        if frame is None:
            logger.error(f"No frame data received for session: {session_id}")
            raise ValueError("No frame data received")
            
        session = self.active_sessions[session_id]
        current_time = time.time()
        
        # Update FPS calculation
        if self.last_inference_time > 0:
            self.inference_fps = 1 / (current_time - self.last_inference_time)
        self.last_inference_time = current_time
        
        # Process frame through YOLO model with tracking
        results = self.model.track(
            source=frame,
            tracker=self.tracker,
            conf=self.conf,
            iou=self.iou,
            persist=True
        )
        
        if not results or len(results) == 0 or not hasattr(results[0], 'boxes'):
            return {
                'frame': frame,
                'count': session['display_count'],
                'session_unique': len(session['session_unique_roses']),
                'total_unique': len(self.persistent_data['total_unique_roses']),
                'current_in_frame': 0,
                'fps': self.inference_fps,
                'tracked_roses': [],
                'count_updated': False,
                'session_number': session['session_number']
            }
            
        # Process detections
        tracked_roses = self._process_detections(results[0].boxes)
        current_count = len(tracked_roses)
        
        # Update session statistics
        session['frame_count'] += 1
        
        # Track unique roses in this session and globally
        for rose in tracked_roses:
            if 'id' in rose:
                session['session_unique_roses'].add(rose['id'])
                self.persistent_data['total_unique_roses'].add(rose['id'])
        
        # Update frame counts for smoothing
        session['frame_counts'].append(current_count)
        if len(session['frame_counts']) > 10:  # Keep last 10 frames
            session['frame_counts'].pop(0)
        
        # Update display count at regular intervals
        should_update_count = (current_time - session['last_count_update']) >= self.COUNT_UPDATE_INTERVAL
        if should_update_count:
            # Calculate smoothed count (average of recent frames)
            if session['frame_counts']:
                smoothed_count = int(sum(session['frame_counts']) / len(session['frame_counts']))
                session['display_count'] = smoothed_count
            session['last_count_update'] = current_time
        
        session['last_update'] = current_time
        
        # Get frame with bounding boxes but without text overlays
        annotated_frame = results[0].plot()
        if annotated_frame is None:
            annotated_frame = frame
            
        logger.debug(f"Processed frame for session: {session_id} (Session #{session['session_number']}) | Frame count: {session['frame_count']}")
        return {
            'frame': annotated_frame,
            'count': session['display_count'],
            'session_unique': len(session['session_unique_roses']),
            'total_unique': len(self.persistent_data['total_unique_roses']),
            'current_in_frame': current_count,
            'fps': self.inference_fps,
            'tracked_roses': tracked_roses,
            'count_updated': should_update_count,
            'session_number': session['session_number']
        }

    def _process_detections(self, boxes):
        """Process detection boxes and extract tracking information"""
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
        
        return tracked_roses

    def stop_tracking(self):
        """Stop tracking and release resources."""
        print("Stopping tracking...")
        self.is_tracking = False
        print("Camera resources released")

    def _update_fps(self):
        """Update the FPS calculation."""
        current_time = time.time()
        if hasattr(self, 'last_inference_time') and self.last_inference_time > 0:
            self.inference_fps = 1 / (current_time - self.last_inference_time)
        self.last_inference_time = current_time

    def get_total_unique_roses(self):
        """Get the total count of unique roses across all sessions"""
        return self.persistent_data['cumulative_unique_roses']

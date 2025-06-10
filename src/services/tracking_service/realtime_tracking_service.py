import base64
from src.services.tracking_service.base_tracking_service import BaseTrackingService
from src.services.redis_service import RedisService
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
    """Service for real-time rose tracking operations with optional Redis-based shared storage."""
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        
        # Redis configuration from settings
        self.use_redis = self.settings.USE_REDIS
        self.redis_host = self.settings.REDIS_HOST
        self.redis_port = self.settings.REDIS_PORT
        self.redis_db = self.settings.REDIS_DB
        self.redis_password = self.settings.REDIS_PASSWORD
        self.redis_ttl = self.settings.REDIS_SESSION_TTL
        
        # Initialize Redis service if enabled
        self.redis_service = None
        if self.use_redis:
            try:
                self.redis_service = RedisService(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db,
                    password=self.redis_password
                )
                logger.info(f"Redis service initialized successfully at {self.redis_host}:{self.redis_port}")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis service: {str(e)}. Falling back to in-memory storage.")
                self.use_redis = False
                self.redis_service = None
        
        self.COUNT_UPDATE_INTERVAL = 2.0  # Update count every 2 seconds
        self.is_tracking = False
        self.input_frame = None
        self.inference_fps = 0.0  # Initialize FPS
        self.last_inference_time = 0.0  # Initialize last inference time
        
        # Initialize storage (Redis or in-memory)
        self.active_sessions = {}  # Fallback for in-memory storage
        self._load_persistent_data()

    def _load_persistent_data(self):
        """Load persistent data from Redis or initialize defaults."""
        if self.use_redis and self.redis_service:
            try:
                logger.info(f"[REDIS] Loading persistent data from Redis at {self.redis_host}:{self.redis_port}")
                persistent_data = self.redis_service.get_persistent_data()
                if persistent_data is None:
                    # Initialize default persistent data structure
                    self.persistent_data = {
                        'session_history': [],
                        'last_session_id': None,
                        'next_session_number': 1,
                        'cumulative_session_count': 0
                    }
                    # Save to Redis
                    success = self.redis_service.set_persistent_data(self.persistent_data)
                    if success:
                        logger.info(f"[REDIS] Initialized new persistent data in Redis: {self.persistent_data}")
                    else:
                        logger.error("[REDIS] Failed to save initial persistent data to Redis")
                else:
                    self.persistent_data = persistent_data
                    logger.info(f"[REDIS] Loaded persistent data from Redis: cumulative_count={self.persistent_data.get('cumulative_session_count', 0)}, next_session={self.persistent_data.get('next_session_number', 1)}")
            except Exception as e:
                logger.error(f"Failed to load persistent data from Redis: {str(e)}")
                self._init_default_persistent_data()
        else:
            logger.info("[REDIS] Redis disabled, using in-memory storage")
            self._init_default_persistent_data()

    def _init_default_persistent_data(self):
        """Initialize default persistent data structure."""
        self.persistent_data = {
            'session_history': [],
            'last_session_id': None,
            'next_session_number': 1,
            'cumulative_session_count': 0
        }
        logger.info("Using in-memory persistent data storage")

    def start_session(self):
        """Initialize a new tracking session with Redis or in-memory storage"""
        try:
            session_id = str(uuid.uuid4())
            
            # Get next session number
            if self.use_redis and self.redis_service:
                session_number = self.redis_service.increment_session_number()
                logger.info(f"[REDIS] Got session number {session_number} from Redis")
            else:
                session_number = self.persistent_data['next_session_number']
                self.persistent_data['next_session_number'] += 1
            
            session_data = {
                'start_time': time.time(),
                'last_update': time.time(),
                'last_count_update': time.time(),
                'display_count': 0,  # Smoothed count for display
                'frame_counts': [],  # Store recent frame counts for smoothing
                'session_unique_roses': set(),  # Track unique roses in this session
                'frame_count': 0,
                'session_number': session_number
            }
            
            # Store session
            if self.use_redis and self.redis_service:
                if not self.redis_service.set_session(session_id, session_data, self.redis_ttl):
                    raise RuntimeError("Failed to store session in Redis")
                # Update persistent data
                self.persistent_data['last_session_id'] = session_id
                self.redis_service.set_last_session_id(session_id)
                logger.info(f"[REDIS] Session {session_id} stored successfully in Redis")
            else:
                # Store in memory
                self.active_sessions[session_id] = session_data
                self.persistent_data['last_session_id'] = session_id
            
            logger.info(f"Started new session: {session_id} (Session #{session_number})")
            return session_id
        except Exception as e:
            logger.error(f"Failed to start session: {str(e)}")
            raise RuntimeError(f"Failed to start session: {str(e)}")

    def stop_session(self, session_id):
        """End a tracking session and return final statistics"""
        try:
            # Get session data
            if self.use_redis and self.redis_service:
                session_data = self.redis_service.get_session(session_id)
                if session_data is None:
                    logger.warning(f"Attempted to stop invalid session: {session_id}")
                    raise ValueError("Invalid session ID")
            else:
                if session_id not in self.active_sessions:
                    logger.warning(f"Attempted to stop invalid session: {session_id}")
                    raise ValueError("Invalid session ID")
                session_data = self.active_sessions[session_id]
            
            duration = time.time() - session_data['start_time']
            
            # Get session unique roses count
            session_unique_count = len(session_data.get('session_unique_roses', set()))

            # --- Update cumulative before building stats ---
            if self.use_redis and self.redis_service:
                current_persistent = self.redis_service.get_persistent_data()
                if current_persistent:
                    new_cumulative = current_persistent['cumulative_session_count'] + session_unique_count
                    current_persistent['cumulative_session_count'] = new_cumulative
                    self.redis_service.set_persistent_data(current_persistent)
                    self.persistent_data = current_persistent
                else:
                    new_cumulative = session_unique_count
            else:
                new_cumulative = self.persistent_data['cumulative_session_count'] + session_unique_count
                self.persistent_data['cumulative_session_count'] = new_cumulative
            # --- END FIX ---
            
            # Calculate session statistics
            session_stats = {
                "session_number": session_data['session_number'],
                "session_unique_roses": session_unique_count,
                "total_unique_roses": new_cumulative,
                "duration": duration,
                "average_fps": session_data['frame_count'] / duration if duration > 0 else 0,
                "total_frames_processed": session_data['frame_count']
            }
            
            # Store session history
            session_history_entry = {
                'session_id': session_id,
                'stats': session_stats,
                'end_time': time.time()
            }
            
            if self.use_redis and self.redis_service:
                # Update persistent data in Redis (already updated cumulative above)
                current_persistent = self.redis_service.get_persistent_data()
                if current_persistent:
                    current_persistent['session_history'].append(session_history_entry)
                    self.redis_service.set_persistent_data(current_persistent)
                    self.persistent_data = current_persistent
                # Delete session from Redis
                self.redis_service.delete_session(session_id)
            else:
                # Update in-memory data (already updated cumulative above)
                self.persistent_data['session_history'].append(session_history_entry)
                # Remove from active sessions
                del self.active_sessions[session_id]
            
            # Stop tracking and cleanup
            self.stop_tracking()
            logger.info(f"Stopped session: {session_id} (Session #{session_data['session_number']})")
            
            return session_stats
        except Exception as e:
            logger.error(f"Failed to stop session {session_id}: {str(e)}")
            raise RuntimeError(f"Failed to stop session: {str(e)}")

    def get_session_stats(self, session_id):
        """Get current statistics for a specific session"""
        try:
            # Get session data
            if self.use_redis and self.redis_service:
                session_data = self.redis_service.get_session(session_id)
                if session_data is None:
                    logger.warning(f"[REDIS] Session {session_id} not found in Redis")
                    raise ValueError("Invalid session ID")
            else:
                if session_id not in self.active_sessions:
                    logger.warning(f"Invalid session ID used in get_session_stats: {session_id}")
                    raise ValueError("Invalid session ID")
                session_data = self.active_sessions[session_id]
            
            duration = time.time() - session_data['start_time']
            session_unique_count = len(session_data.get('session_unique_roses', set()))
            current_cumulative = self.persistent_data.get('cumulative_session_count', 0)
            
            logger.debug(f"[REDIS] Session {session_id} stats: unique={session_unique_count}, cumulative={current_cumulative}, total={current_cumulative + session_unique_count}")
            
            return {
                "session_number": session_data['session_number'],
                "session_unique_roses": session_unique_count,
                "total_unique_roses": current_cumulative + session_unique_count,
                "duration": duration,
                "average_fps": session_data['frame_count'] / duration if duration > 0 else 0,
                "total_frames_processed": session_data['frame_count']
            }
        except Exception as e:
            logger.error(f"Failed to get session stats for {session_id}: {str(e)}")
            raise RuntimeError(f"Failed to get session stats: {str(e)}")

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
        try:
            # Get session data
            if self.use_redis and self.redis_service:
                session_data = self.redis_service.get_session(session_id)
                if session_data is None:
                    logger.warning(f"[REDIS] Session {session_id} not found in Redis during frame processing")
                    raise ValueError("Invalid session ID")
            else:
                if session_id not in self.active_sessions:
                    logger.warning(f"Invalid session ID used in process_frame: {session_id}")
                    raise ValueError("Invalid session ID")
                session_data = self.active_sessions[session_id]
            
            if frame is None:
                logger.error(f"No frame data received for session: {session_id}")
                raise ValueError("No frame data received")
            
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
                session_unique_count = len(session_data.get('session_unique_roses', set()))
                current_cumulative = self.persistent_data.get('cumulative_session_count', 0)
                return {
                    'frame': frame,
                    'count': session_data['display_count'],
                    'session_unique': session_unique_count,
                    'total_unique': current_cumulative + session_unique_count,
                    'current_in_frame': 0,
                    'fps': self.inference_fps,
                    'tracked_roses': [],
                    'count_updated': False,
                    'session_number': session_data['session_number']
                }
            
            # Process detections
            tracked_roses = self._process_detections(results[0].boxes)
            current_count = len(tracked_roses)
            
            # Update session statistics
            session_data['frame_count'] += 1
            
            # Track unique roses in this session
            session_unique_roses = session_data.get('session_unique_roses', set())
            previous_unique_count = len(session_unique_roses)
            for rose in tracked_roses:
                if 'id' in rose:
                    session_unique_roses.add(rose['id'])
            session_data['session_unique_roses'] = session_unique_roses
            session_unique_count = len(session_unique_roses)
            
            # Log if new unique roses were detected
            if session_unique_count > previous_unique_count:
                new_roses = session_unique_count - previous_unique_count
                logger.debug(f"[REDIS] Session {session_id}: Detected {new_roses} new unique roses (total in session: {session_unique_count})")
            
            # Update frame counts for smoothing
            frame_counts = session_data.get('frame_counts', [])
            frame_counts.append(current_count)
            if len(frame_counts) > 10:  # Keep last 10 frames
                frame_counts.pop(0)
            session_data['frame_counts'] = frame_counts
            
            # Update display count at regular intervals
            should_update_count = (current_time - session_data['last_count_update']) >= self.COUNT_UPDATE_INTERVAL
            if should_update_count:
                # Calculate smoothed count (average of recent frames)
                if frame_counts:
                    smoothed_count = int(sum(frame_counts) / len(frame_counts))
                    session_data['display_count'] = smoothed_count
                session_data['last_count_update'] = current_time
            
            session_data['last_update'] = current_time
            
            # Update session storage
            if self.use_redis and self.redis_service:
                if not self.redis_service.set_session(session_id, session_data, self.redis_ttl):
                    logger.warning(f"[REDIS] Failed to update session {session_id} in Redis")
                else:
                    logger.debug(f"[REDIS] Updated session {session_id} in Redis")
            else:
                # Update in-memory session
                self.active_sessions[session_id] = session_data
            
            # Get frame with bounding boxes but without text overlays
            annotated_frame = results[0].plot()
            if annotated_frame is None:
                annotated_frame = frame
            
            current_cumulative = self.persistent_data.get('cumulative_session_count', 0)
            logger.debug(f"[REDIS] Session {session_id} (Session #{session_data['session_number']}) | Frame count: {session_data['frame_count']}, Session unique: {session_unique_count}, Total: {current_cumulative + session_unique_count}")
            
            return {
                'frame': annotated_frame,
                'count': session_data['display_count'],
                'session_unique': session_unique_count,
                'total_unique': current_cumulative + session_unique_count,
                'current_in_frame': current_count,
                'fps': self.inference_fps,
                'tracked_roses': tracked_roses,
                'count_updated': should_update_count,
                'session_number': session_data['session_number']
            }
        except Exception as e:
            logger.error(f"Failed to process frame for session {session_id}: {str(e)}")
            raise RuntimeError(f"Frame processing failed: {str(e)}")

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
        try:
            if self.use_redis and self.redis_service:
                persistent_data = self.redis_service.get_persistent_data()
                if persistent_data:
                    return persistent_data.get('cumulative_session_count', 0)
            return self.persistent_data.get('cumulative_session_count', 0)
        except Exception as e:
            logger.error(f"Failed to get total unique roses: {str(e)}")
            return 0

    def get_session_history(self):
        """Get session history"""
        try:
            if self.use_redis and self.redis_service:
                persistent_data = self.redis_service.get_persistent_data()
                if persistent_data:
                    return persistent_data.get('session_history', [])
            return self.persistent_data.get('session_history', [])
        except Exception as e:
            logger.error(f"Failed to get session history: {str(e)}")
            return []

    def get_last_session_id(self):
        """Get the last active session ID"""
        try:
            if self.use_redis and self.redis_service:
                return self.redis_service.get_last_session_id()
            return self.persistent_data.get('last_session_id')
        except Exception as e:
            logger.error(f"Failed to get last session ID: {str(e)}")
            return None

    def close(self):
        """Close Redis connection and cleanup resources."""
        try:
            if self.redis_service:
                self.redis_service.close()
            logger.info("RealtimeTrackingService closed successfully")
        except Exception as e:
            logger.error(f"Error closing RealtimeTrackingService: {str(e)}")

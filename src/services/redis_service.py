import redis
import json
import pickle
import logging
from typing import Dict, Any, Optional, Set
import time
import uuid

logger = logging.getLogger(__name__)

class RedisService:
    """Service for managing shared state across multiple workers using Redis."""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,  # Keep binary data for pickle
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise RuntimeError(f"Redis connection failed: {str(e)}")
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data to bytes for Redis storage."""
        try:
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            raise
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from bytes."""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization error: {str(e)}")
            raise
    
    def set_session(self, session_id: str, session_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Store session data in Redis with TTL."""
        try:
            key = f"session:{session_id}"
            # Convert set to list for serialization
            minimal_session = {
                'start_time': session_data.get('start_time'),
                'last_update': session_data.get('last_update'),
                'last_count_update': session_data.get('last_count_update'),
                'display_count': session_data.get('display_count', 0),
                'frame_counts': session_data.get('frame_counts', []),
                'session_unique_roses': list(session_data.get('session_unique_roses', set())),  # Convert set to list
                'frame_count': session_data.get('frame_count', 0),
                'session_number': session_data.get('session_number', 1)
            }
            serialized_data = self._serialize(minimal_session)
            result = self.redis_client.setex(key, ttl, serialized_data)
            logger.debug(f"[REDIS] Set session {session_id} with TTL {ttl}s: {result}")
            return result
        except Exception as e:
            logger.error(f"[REDIS] Failed to set session {session_id}: {str(e)}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from Redis."""
        try:
            key = f"session:{session_id}"
            data = self.redis_client.get(key)
            if data is None:
                logger.debug(f"[REDIS] Session {session_id} not found in Redis")
                return None
            session_data = self._deserialize(data)
            # Convert list back to set for session_unique_roses
            if 'session_unique_roses' in session_data and isinstance(session_data['session_unique_roses'], list):
                session_data['session_unique_roses'] = set(session_data['session_unique_roses'])
            logger.debug(f"[REDIS] Retrieved session {session_id} from Redis")
            return session_data
        except Exception as e:
            logger.error(f"[REDIS] Failed to get session {session_id}: {str(e)}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session data from Redis."""
        try:
            key = f"session:{session_id}"
            result = bool(self.redis_client.delete(key))
            logger.debug(f"[REDIS] Deleted session {session_id}: {result}")
            return result
        except Exception as e:
            logger.error(f"[REDIS] Failed to delete session {session_id}: {str(e)}")
            return False
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists in Redis."""
        try:
            key = f"session:{session_id}"
            result = bool(self.redis_client.exists(key))
            logger.debug(f"[REDIS] Session {session_id} exists: {result}")
            return result
        except Exception as e:
            logger.error(f"[REDIS] Failed to check session {session_id}: {str(e)}")
            return False
    
    def set_persistent_data(self, data: Dict[str, Any]) -> bool:
        """Store persistent data in Redis."""
        try:
            key = "persistent_data"
            # Only keep the new structure
            minimal_data = {
                'session_history': data.get('session_history', []),
                'last_session_id': data.get('last_session_id', None),
                'next_session_number': data.get('next_session_number', 1),
                'cumulative_session_count': data.get('cumulative_session_count', 0)
            }
            serialized_data = self._serialize(minimal_data)
            result = bool(self.redis_client.set(key, serialized_data))
            logger.debug(f"[REDIS] Set persistent data: cumulative_count={minimal_data['cumulative_session_count']}, next_session={minimal_data['next_session_number']}")
            return result
        except Exception as e:
            logger.error(f"[REDIS] Failed to set persistent data: {str(e)}")
            return False
    
    def get_persistent_data(self) -> Optional[Dict[str, Any]]:
        """Retrieve persistent data from Redis."""
        try:
            key = "persistent_data"
            data = self.redis_client.get(key)
            if data is None:
                logger.debug(f"[REDIS] Persistent data not found in Redis, returning defaults")
                # Return default persistent data structure
                return {
                    'session_history': [],
                    'last_session_id': None,
                    'next_session_number': 1,
                    'cumulative_session_count': 0
                }
            persistent_data = self._deserialize(data)
            logger.debug(f"[REDIS] Retrieved persistent data: cumulative_count={persistent_data.get('cumulative_session_count', 0)}, next_session={persistent_data.get('next_session_number', 1)}")
            return persistent_data
        except Exception as e:
            logger.error(f"[REDIS] Failed to get persistent data: {str(e)}")
            return None
    
    def update_persistent_data(self, updates: Dict[str, Any]) -> bool:
        """Update persistent data atomically."""
        try:
            current_data = self.get_persistent_data()
            if current_data is None:
                return False
            
            # Update with new data
            for key, value in updates.items():
                if key == 'total_unique_roses' and isinstance(value, set):
                    # Merge sets for unique roses
                    current_data[key].update(value)
                elif key == 'session_history' and isinstance(value, list):
                    # Append to session history
                    current_data[key].extend(value)
                else:
                    current_data[key] = value
            
            return self.set_persistent_data(current_data)
        except Exception as e:
            logger.error(f"Failed to update persistent data: {str(e)}")
            return False
    
    def increment_session_number(self) -> int:
        """Atomically increment and return next session number."""
        try:
            key = "next_session_number"
            result = self.redis_client.incr(key)
            logger.debug(f"[REDIS] Incremented session number: {result}")
            return result
        except Exception as e:
            logger.error(f"[REDIS] Failed to increment session number: {str(e)}")
            return 1
    
    def set_last_session_id(self, session_id: str) -> bool:
        """Set the last active session ID."""
        try:
            key = "last_session_id"
            result = bool(self.redis_client.set(key, session_id))
            logger.debug(f"[REDIS] Set last session ID: {session_id}")
            return result
        except Exception as e:
            logger.error(f"[REDIS] Failed to set last session ID: {str(e)}")
            return False
    
    def get_last_session_id(self) -> Optional[str]:
        """Get the last active session ID."""
        try:
            key = "last_session_id"
            result = self.redis_client.get(key)
            logger.debug(f"[REDIS] Retrieved last session ID: {result}")
            return result
        except Exception as e:
            logger.error(f"[REDIS] Failed to get last session ID: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            result = self.redis_client.ping()
            logger.debug(f"[REDIS] Health check: {result}")
            return result
        except Exception as e:
            logger.error(f"[REDIS] Health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close Redis connection."""
        try:
            self.redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}") 
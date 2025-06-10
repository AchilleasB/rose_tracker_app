from flask import Blueprint, jsonify
from config.settings import Settings
import logging

logger = logging.getLogger(__name__)

class HealthController:
    def __init__(self):
        self.blueprint = Blueprint('health', __name__)
        self._register_routes()

    def _register_routes(self):
        self.blueprint.route('/health', methods=['GET'])(self.health_check)

    def health_check(self):
        """Health check endpoint to verify application health and optional Redis connectivity."""
        try:
            settings = Settings()
            
            if settings.USE_REDIS:
                # Test Redis connection when enabled
                try:
                    from src.services.redis_service import RedisService
                    redis_service = RedisService(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=settings.REDIS_DB,
                        password=settings.REDIS_PASSWORD
                    )
                    
                    redis_healthy = redis_service.health_check()
                    redis_service.close()
                    
                    if redis_healthy:
                        return jsonify({
                            "status": "healthy",
                            "redis": "connected",
                            "state_management": "redis",
                            "message": "Application is running normally with Redis"
                        }), 200
                    else:
                        return jsonify({
                            "status": "unhealthy",
                            "redis": "disconnected",
                            "state_management": "redis",
                            "message": "Redis connection failed"
                        }), 503
                        
                except Exception as e:
                    return jsonify({
                        "status": "unhealthy",
                        "redis": "error",
                        "state_management": "redis",
                        "message": f"Redis health check failed: {str(e)}"
                    }), 503
            else:
                # Redis not enabled, just return basic health
                return jsonify({
                    "status": "healthy",
                    "redis": "disabled",
                    "state_management": "in-memory",
                    "message": "Application is running normally (development mode)"
                }), 200
                
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "redis": "unknown",
                "state_management": "unknown",
                "message": f"Health check failed: {str(e)}"
            }), 503 
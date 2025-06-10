from datetime import datetime
from flask import Blueprint, Response, render_template, jsonify, request
import cv2
import numpy as np
from src.services import RealtimeTrackingService
from config.settings import Settings
import base64
from functools import wraps

class RealtimeTrackingController:
    def __init__(self):
        self.settings = Settings()
        self.blueprint = Blueprint('realtime_tracking', __name__)
        self.realtime_tracker_service = RealtimeTrackingService()
        self._register_routes()

    def _register_routes(self):
        self.blueprint.route("/track/realtime/stream", methods=["POST"])(self.realtime_stream)
        self.blueprint.route("/track/realtime/stop", methods=["POST"])(self.stop_stream)
        self.blueprint.route("/track/realtime/start", methods=["POST"])(self.start_stream)
        self.blueprint.route("/track/realtime", methods=["GET"])(self.realtime_view)
        self.blueprint.route("/track/realtime/session", methods=["GET"])(self.get_session_info)
        self.blueprint.route("/track/realtime/roses-count", methods=["GET"])(self.get_total_unique_roses)

    def _require_session(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            self = args[0]
            session_id = request.headers.get('X-Session-ID')
            if not session_id:
                return jsonify({
                    "status": "error",
                    "message": "Missing session ID"
                }), 400
            return f(*args, **kwargs)
        return decorated_function

    def start_stream(self):
        """Initialize a new tracking session"""
        try:
            session_id = self.realtime_tracker_service.start_session()
            return jsonify({
                "status": "success",
                "session_id": session_id,
                "message": "Tracking session started"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @_require_session
    def realtime_stream(self):
        """Process a single frame in the current tracking session"""
        try:
            session_id = request.headers.get('X-Session-ID')
            
            # Decode image data
            frame = self.realtime_tracker_service._decode_image(request.json.get('image', ''))
            
            # Process frame through service
            result = self.realtime_tracker_service.process_frame(session_id, frame)
            
            # Encode the processed frame
            success, buffer = cv2.imencode('.jpg', result['frame'])
            if not success:
                    return jsonify({"status": "error", "message": "Failed to encode output frame"}), 500
            
            processed_image = base64.b64encode(buffer).decode('utf-8')

            return jsonify({
                "status": "success",
                "image": f"data:image/jpeg;base64,{processed_image}",
                "count": result['count'],
                "session_unique": result['session_unique'],
                "total_unique": result['total_unique'],
                "current_in_frame": result['current_in_frame'],
                "fps": result['fps'],
                "tracked_roses": result['tracked_roses'],
                "count_updated": result['count_updated'],
                "session_number": result['session_number']
            })
                
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        except Exception as e:
            return jsonify({"status": "error", "message": f"Processing error: {str(e)}"}), 500

    @_require_session
    def stop_stream(self):
        """End the current tracking session"""
        try:
            session_id = request.headers.get('X-Session-ID')
            session_stats = self.realtime_tracker_service.stop_session(session_id)
            
            return jsonify({
                "status": "success",
                "message": "Stream stopped and session ended",
                "session_stats": session_stats
            })
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Failed to stop stream: {str(e)}"
            }), 500

    @_require_session
    def get_session_info(self):
        """Get current session statistics"""
        try:
            session_id = request.headers.get('X-Session-ID')
            session_stats = self.realtime_tracker_service.get_session_stats(session_id)
            
            return jsonify({
                "status": "success",
                "session_stats": session_stats
            })
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Failed to get session info: {str(e)}"
            }), 500

    def get_total_unique_roses(self):
        """Get the total count of unique roses across all sessions"""
        try:
            total_count = self.realtime_tracker_service.get_total_unique_roses()
            return jsonify({
                "status": "success",
                "total_unique_roses": total_count,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                "status": "error",  
                "message": f"Failed to get total roses count: {str(e)}"
            }), 500

    def realtime_view(self):
        """Render the realtime tracking view"""
        return render_template('realtime_stream.html')
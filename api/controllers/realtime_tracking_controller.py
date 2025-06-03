from flask import Blueprint, Response, render_template, jsonify, request
import cv2
import numpy as np
from src.services import RealtimeTrackingService
from config.settings import Settings
import base64
import os
import time

class RealtimeTrackingController:
    def __init__(self):
        self.settings = Settings()
        self.blueprint = Blueprint('realtime_tracking', __name__)
        self.realtime_tracker_service = RealtimeTrackingService()
        self._register_routes()

    def _register_routes(self):
        self.blueprint.route("/track/realtime/stream", methods=["POST"])(self.realtime_stream)
        self.blueprint.route("/track/realtime/stop", methods=["POST"])(self.stop_stream)
        self.blueprint.route("/track/realtime", methods=["GET"])(self.realtime_view)
        self.blueprint.route("/track/realtime/count", methods=["GET"])(self.get_latest_count)

    def realtime_stream(self):
        """Stream endpoint that provides the video feed using YOLO's built-in tracking"""
        try:
            # Get and validate the base64 encoded image
            image_data = request.json.get('image', '')
            if not image_data:
                return jsonify({"status": "error", "message": "No image data received"}), 400

            # Remove the data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
                
            # Decode the base64 image
            try:
                image_bytes = base64.b64decode(image_data)
                image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            except Exception as e:
                return jsonify({"status": "error", "message": "Invalid image data"}), 400
            
            if frame is None:
                return jsonify({"status": "error", "message": "Failed to decode image"}), 400

            # Process the frame using YOLO's tracking
            try:
                # Process the frame
                output_frame = self.realtime_tracker_service.track_realtime(frame)
                
                if output_frame is None:
                    return jsonify({"status": "error", "message": "Failed to process frame"}), 500
                
                # Encode the processed frame
                success, buffer = cv2.imencode('.jpg', output_frame)
                if not success:
                    return jsonify({"status": "error", "message": "Failed to encode output frame"}), 500
                    
                processed_image = base64.b64encode(buffer).decode('utf-8')
                
                # Get latest tracking info
                count_info = self.realtime_tracker_service.get_latest_count()
                
                return jsonify({
                    "status": "success",
                    "image": f"data:image/jpeg;base64,{processed_image}",
                    "count": count_info["count"],
                    "fps": count_info["fps"],
                    "tracked_roses": count_info.get("tracked_roses", [])
                })
                
            except Exception as e:
                return jsonify({"status": "error", "message": f"Processing error: {str(e)}"}), 500
                
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
        
        
    def stop_stream(self):
        """Stop the video stream and release resources"""
        try:
            self.realtime_tracker_service.stop_tracking()
            return jsonify({"status": "success", "message": "Stream stopped"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    def realtime_view(self):
        """Render the realtime tracking view"""
        return render_template('realtime_stream.html')

    def get_latest_count(self):
        """Get the latest rose count and FPS"""
        return jsonify(self.realtime_tracker_service.get_latest_count())
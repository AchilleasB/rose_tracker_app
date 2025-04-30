"""
Realtime Tracking Module

This module provides endpoints for real-time rose tracking using a webcam or video stream.
It handles video stream processing using the RealtimeTrackerService and returns
the processed video stream along with tracking metadata.
"""
from flask import Blueprint, Response, render_template, jsonify, request
import cv2
from src.services.realtime_rose_tracker import RealtimeTrackerService
from config.settings import Settings

settings = Settings()
realtime_tracking = Blueprint('realtime_tracking', __name__)
realtime_tracker_service = RealtimeTrackerService()

# Store the latest count
latest_count = 0
last_count_update = 0
COUNT_UPDATE_INTERVAL = 10  # seconds

@realtime_tracking.route("/track/realtime/stream", methods=["GET"])
def realtime_stream():
    """Stream endpoint that provides the video feed"""
    def generate_frames():
        print("Starting video stream...")
        try:
            for frame in realtime_tracker_service.track_realtime():
                if frame is None:
                    print("Received None frame from tracker")
                    continue
                
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    print("Failed to encode frame")
                    continue
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                
        except GeneratorExit:
            print("Client closed connection")
        except Exception as e:
            print(f"Error in stream_camera: {str(e)}")
            raise
    
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@realtime_tracking.route("/track/realtime/stop", methods=["POST"])
def stop_stream():
    """Stop the video stream and release resources"""
    try:
        realtime_tracker_service.stop_tracking()
        return jsonify({"status": "success", "message": "Stream stopped"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Serve the webcam view template (for testing)
# Triggers the stream from the frontend
@realtime_tracking.route("/track/realtime", methods=["GET"])
def realtime_view():
    """Test view with embedded video stream"""
    return render_template('realtime_stream.html')

@realtime_tracking.route("/track/realtime/count", methods=["GET"])
def get_latest_count():
    """Endpoint to get the latest rose count"""
    return jsonify(realtime_tracker_service.get_latest_count())

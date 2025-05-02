from flask import Blueprint, Response, render_template, jsonify
import cv2
from src.services import RealtimeTrackingService
from config.settings import Settings

class RealtimeTrackingController:
    def __init__(self):
        self.settings = Settings()
        self.blueprint = Blueprint('realtime_tracking', __name__)
        self.realtime_tracker_service = RealtimeTrackingService()
        self._register_routes()

    def _register_routes(self):
        self.blueprint.route("/track/realtime/stream", methods=["GET"])(self.realtime_stream)
        self.blueprint.route("/track/realtime/stop", methods=["POST"])(self.stop_stream)
        self.blueprint.route("/track/realtime", methods=["GET"])(self.realtime_view)
        self.blueprint.route("/track/realtime/count", methods=["GET"])(self.get_latest_count)

    def realtime_stream(self):
        """Stream endpoint that provides the video feed"""
        def generate_frames():
            print("Starting video stream...")
            try:
                for frame in self.realtime_tracker_service.track_realtime():
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

    def stop_stream(self):
        """Stop the video stream and release resources"""
        try:
            self.realtime_tracker_service.stop_tracking()
            return jsonify({"status": "success", "message": "Stream stopped"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    def realtime_view(self):
        """Test view with embedded video stream"""
        return render_template('realtime_stream.html')

    def get_latest_count(self):
        """Endpoint to get the latest rose count"""
        return jsonify(self.realtime_tracker_service.get_latest_count()) 
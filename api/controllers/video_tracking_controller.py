from flask import Blueprint, jsonify, request
import os
from src.services import VideoTrackingService
from config.settings import Settings

class VideoTrackingController:
    def __init__(self):
        self.settings = Settings()
        self.blueprint = Blueprint('video_tracking', __name__)
        self.rose_tracker_service = VideoTrackingService()
        self._register_routes()

    def _register_routes(self):
        self.blueprint.route("/track/video", methods=["POST"])(self.track_video)

    def track_video(self):
        try:
            video_upload_dir = self.settings.UPLOAD_VIDEOS_DIR
            os.makedirs(video_upload_dir, exist_ok=True)
            
            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded."}), 400

            file = request.files['file']
            if not file.filename.lower().endswith(tuple(self.settings.ALLOWED_VIDEO_EXTENSIONS)):
                return jsonify({"error": "Invalid video file format."}), 400

            filename = file.filename
            file_path = os.path.join(video_upload_dir, filename)
            file.save(file_path)

            output_path = self.settings.TRACKING_VIDEOS_DIR
            os.makedirs(output_path, exist_ok=True)

            video_output, number_of_roses = self.rose_tracker_service.track_video(
                input_source=file_path,
                output_path=output_path,
            )

            if os.path.exists(video_output):
                return jsonify({
                    "video_output": video_output,
                    "number_of_roses": number_of_roses
                })
            else:
                return jsonify({"error": "Annotated video not found."}), 404
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500 
from flask import Blueprint, jsonify, request, send_file
import os
from src.services import VideoTrackingService
from config.settings import Settings
import uuid

class VideoTrackingController:
    def __init__(self):
        self.settings = Settings()
        self.blueprint = Blueprint('video_tracking', __name__)
        self.rose_tracker_service = VideoTrackingService()
        self._register_routes()

    def _register_routes(self):
        self.blueprint.route("/track/video", methods=["POST"])(self.track_video)
        self.blueprint.route("/tracked-video/<file_id>", methods=["GET"])(self.get_tracked_video)

    def get_tracked_video(self, file_id):
        try:
            # Construct the path to the tracked video
            video_path = os.path.join(self.settings.TRACKING_VIDEOS_DIR, f"{file_id}.mp4")
            
            if not os.path.exists(video_path):
                return jsonify({"error": "Tracked video not found."}), 404
                
            return send_file(
                video_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name=f"tracked_{file_id}.mp4"
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def track_video(self):
        try:
            video_upload_dir = self.settings.UPLOAD_VIDEOS_DIR
            os.makedirs(video_upload_dir, exist_ok=True)
            
            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded."}), 400

            file = request.files['file']
            if not file.filename.lower().endswith(tuple(self.settings.ALLOWED_VIDEO_EXTENSIONS)):
                return jsonify({"error": "Invalid video file format."}), 400

            # Generate a unique file ID
            file_id = str(uuid.uuid4())
            filename = f"{file_id}.mp4"
            file_path = os.path.join(video_upload_dir, filename)
            file.save(file_path)

            output_path = self.settings.TRACKING_VIDEOS_DIR
            os.makedirs(output_path, exist_ok=True)

            video_output, number_of_roses = self.rose_tracker_service.track_video(
                input_source=file_path,
                output_path=output_path,
            )

            # Rename the output file to use the file_id
            final_output_path = os.path.join(output_path, f"{file_id}.mp4")
            if os.path.exists(video_output):
                os.rename(video_output, final_output_path)
                return jsonify({
                    "number_of_roses": number_of_roses,
                    "download_url": f"/tracked-video/{file_id}"
                })
            else:
                return jsonify({"error": "Annotated video not found."}), 404

        except Exception as e:
            return jsonify({"error": str(e)}), 500
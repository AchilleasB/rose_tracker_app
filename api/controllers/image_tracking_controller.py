from flask import Blueprint, request, jsonify
import os
from src.services import ImageTrackingService
from config.settings import Settings

class ImageTrackingController:
    def __init__(self):
        self.settings = Settings()
        self.blueprint = Blueprint('image_tracking', __name__)
        self.rose_tracker_service = ImageTrackingService()
        self._register_routes()

    def _register_routes(self):
        self.blueprint.route("/track/image", methods=["POST"])(self.track_image)

    def track_image(self):
        try:
            image_upload_dir = self.settings.UPLOAD_IMAGES_DIR
            os.makedirs(image_upload_dir, exist_ok=True)

            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded."}), 400

            file = request.files['file']
            if not file.filename.lower().endswith(tuple(self.settings.ALLOWED_IMAGE_EXTENSIONS)):
                return jsonify({"error": "Invalid image file format."}), 400

            filename = file.filename
            file_path = os.path.join(image_upload_dir, filename)
            file.save(file_path)

            output_path = self.settings.TRACKING_IMAGES_DIR
            os.makedirs(output_path, exist_ok=True)

            image_output, number_of_roses = self.rose_tracker_service.track_image(
                input_source=file_path,
                output_path=output_path,
            )

            if os.path.exists(image_output):
                return jsonify({
                    "image_output": image_output,
                    "number_of_roses": number_of_roses
                })
            else:
                return jsonify({"error": "Annotated image not found."}), 404

        except Exception as e:
            return jsonify({"error": str(e)}), 500 
from flask import Blueprint, request, jsonify, send_file
import os
from src.services import ImageTrackingService
from config.settings import Settings
import uuid

class ImageTrackingController:
    def __init__(self):
        self.settings = Settings()
        self.blueprint = Blueprint('image_tracking', __name__)
        self.rose_tracker_service = ImageTrackingService()
        self._register_routes()

    def _register_routes(self):
        self.blueprint.route("/track/image", methods=["POST"])(self.track_image)
        self.blueprint.route("/tracked-image/<file_id>", methods=["GET"])(self.get_tracked_image)

    def track_image(self):
        try:
            image_upload_dir = self.settings.UPLOAD_IMAGES_DIR
            os.makedirs(image_upload_dir, exist_ok=True)

            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded."}), 400

            file = request.files['file']
            if not file.filename.lower().endswith(tuple(self.settings.ALLOWED_IMAGE_EXTENSIONS)):
                return jsonify({"error": "Invalid image file format."}), 400

            # Generate a unique file ID
            file_id = str(uuid.uuid4())
            filename = f"{file_id}.jpg"
            file_path = os.path.join(image_upload_dir, filename)
            file.save(file_path)

            output_path = self.settings.TRACKING_IMAGES_DIR
            os.makedirs(output_path, exist_ok=True)

            image_output, number_of_roses = self.rose_tracker_service.track_image(
                input_source=file_path,
                output_path=output_path,
            )

            # Rename the output file to use the file_id
            final_output_path = os.path.join(output_path, f"{file_id}.jpg")
            if os.path.exists(image_output):
                os.rename(image_output, final_output_path)
                return jsonify({
                    # "file_id": file_id,
                    "number_of_roses": number_of_roses,
                    "download_url": f"/tracked-image/{file_id}"
                })
            else:
                return jsonify({"error": "Annotated image not found."}), 404

        except Exception as e:
            return jsonify({"error": str(e)}), 500 
        
    def get_tracked_image(self, file_id):
        try:
            # Construct the path to the tracked image
            image_path = os.path.join(self.settings.TRACKING_IMAGES_DIR, f"{file_id}.jpg")
            
            if not os.path.exists(image_path):
                return jsonify({"error": "Tracked image not found."}), 404
                
            return send_file(
                image_path,
                mimetype='image/jpeg',
                as_attachment=True,
                download_name=f"tracked_{file_id}.jpg"
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
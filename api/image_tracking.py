from flask import Blueprint, request, jsonify, send_file
from src.track_roses_advanced import track_roses_advanced
import os

image_tracking = Blueprint('image_tracking', __name__)
model = 'data/best.pt'
tracker_path = 'config/modified_botsort.yaml'

# POST endpoint for tracking roses in an image   
@image_tracking.route("/track/image", methods=["POST"])
def track_image():
    try:
        # Ensure the uploads/images directory exists
        image_upload_dir = os.path.join('uploads', 'images')
        os.makedirs(image_upload_dir, exist_ok=True)

        # Check if a file is uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded."}), 400

        # Save the uploaded image file
        file = request.files['file']
        filename = file.filename
        file_path = os.path.join(image_upload_dir, filename)
        file.save(file_path)

        # Define output path for annotated video
        output_path = 'runs/detect/track/images/'
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Track roses using an image file
        image_output, number_of_roses = track_roses_advanced(
            model_path = model,
            tracker_path = tracker_path,
            input_source=file_path,
            output_path = output_path,
            conf=0.7,
            iou=0.5
        )

        # Return the annotated image file with metadata in headers
        if os.path.exists(image_output):
            # Return the image file as a download and add metadata in headers
            # response = send_file(image_output, as_attachment=True)
            # response.headers['X-Number-Of-Roses'] = number_of_roses
            # return response
            
            # Return the image_output path and number of roses in JSON response
            return jsonify({
            "image_output": image_output,
            "number_of_roses": number_of_roses
        })
        else:
            return jsonify({"error": "Annotated image not found."}), 404
        
     # Catch unexpected errors and return message
    except Exception as e:
        return jsonify({"error": str(e)}), 500
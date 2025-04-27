"""
Image Tracking Module

This module provides endpoints for tracking roses in image files.
It handles image file uploads, processes them using the RoseTrackerService,
and returns the processed image along with tracking metadata.
"""

from flask import Blueprint, request, jsonify, send_file
import os
from src.services.rose_tracker import RoseTrackerService
from config.settings import settings

image_tracking = Blueprint('image_tracking', __name__)
rose_tracker_service = RoseTrackerService()

# POST endpoint for tracking roses in an image   
@image_tracking.route("/track/image", methods=["POST"])
def track_image():
    try:
        # Use settings for upload directory
        image_upload_dir = os.path.join(settings.UPLOAD_FOLDER, 'images')
        os.makedirs(image_upload_dir, exist_ok=True)

        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded."}), 400

        file = request.files['file']
        
        # Validate file extension
        if not file.filename.lower().endswith(tuple(settings.ALLOWED_IMAGE_EXTENSIONS)):
            return jsonify({"error": "Invalid image file format."}), 400

        # Save the uploaded image file
        filename = file.filename
        file_path = os.path.join(image_upload_dir, filename)
        file.save(file_path)

        # Define output path for annotated video
        output_path = os.path.join('runs', 'detect', 'track', 'images')
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Track roses using an image file
        image_output, number_of_roses = rose_tracker_service.track(
            input_source=file_path,
            output_path = output_path,
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
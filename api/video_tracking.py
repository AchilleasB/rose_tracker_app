"""
Video Tracking Module

This module provides endpoints for processing video files to detect and track roses.
It handles video file uploads, processes them using the RoseTrackerService,
and returns the processed video along with tracking metadata.
"""
from flask import Blueprint, jsonify, request, send_file
from src.services.file_rose_tracker import RoseTrackerService
import os
from config.settings import Settings

settings = Settings()
video_tracking = Blueprint('video_tracking', __name__)
rose_tracker_service = RoseTrackerService() 

# POST endpoint for tracking roses in a video file
@video_tracking.route("/track/video", methods=["POST"])
def track_video():
    try:
        # Use settings for upload directory
        video_upload_dir = settings.UPLOAD_VIDEOS_DIR
        os.makedirs(video_upload_dir, exist_ok=True)
        
        # Check if a file is uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded."}), 400

        file = request.files['file']
        # Validate file extension
        if not file.filename.lower().endswith(tuple(settings.ALLOWED_VIDEO_EXTENSIONS)):
            return jsonify({"error": "Invalid video file format."}), 400

        # Save the uploaded video file to uploads directory
        filename = file.filename
        file_path = os.path.join(video_upload_dir, filename)
        file.save(file_path)

        # Define output path for annotated video
        output_path = settings.TRACKING_VIDEOS_DIR
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Track roses using a video file
        video_output, number_of_roses = rose_tracker_service._track_video(
            input_source=file_path,
            output_path=output_path,
        )

        # Return the annotated video file with metadata in headers
        if os.path.exists(video_output):
            return jsonify({
                "video_output": video_output,
                "number_of_roses": number_of_roses
            })
        else:
            return jsonify({"error": "Annotated video not found."}), 404
                
    # Catch unexpected errors and return message
    except Exception as e:
        return jsonify({"error": str(e)}), 500

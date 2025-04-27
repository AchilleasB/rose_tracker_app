"""
Video Tracking Module

This module provides endpoints for processing video files to detect and track roses.
It handles video file uploads, processes them using the RoseTrackerService,
and returns the processed video along with tracking metadata.
"""
from flask import Blueprint, jsonify, request, send_file
from src.services.rose_tracker import RoseTrackerService
import os
from config.settings import settings

video_tracking = Blueprint('video_tracking', __name__)
rose_tracker_service = RoseTrackerService() 

# POST endpoint for tracking roses in a video file
@video_tracking.route("/track/video", methods=["POST"])
def track_video():
    try:
        # Use settings for upload directory
        video_upload_dir = os.path.join(settings.UPLOAD_FOLDER, 'videos')
        os.makedirs(video_upload_dir, exist_ok=True)

        # Check if a file is uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded."}), 400

        # Validate file extension
        file = request.files['file']
        if not file.filename.lower().endswith(tuple(settings.ALLOWED_VIDEO_EXTENSIONS)):
            return jsonify({"error": "Invalid video file format."}), 400

        # Save the uploaded video file
        filename = file.filename
        file_path = os.path.join(video_upload_dir, filename)
        file.save(file_path)

        # Define output path for annotated video
        output_path = os.path.join('runs', 'detect', 'track', 'video')
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Track roses using a video file
        video_output, number_of_roses = rose_tracker_service.track(
            input_source = file_path,
            output_path = output_path,
        )

        # Return the annotated video file with metadata in headers
        if os.path.exists(video_output):
            # Return the video file as a download and add metadata in headers
            # response = send_file(video_output, as_attachment=True)
            # response.headers['X-Number-Of-Roses'] = number_of_roses
            # return response
            
            # Return the video path and number of roses in JSON response
            return jsonify({
            "video_output": video_output,
            "number_of_roses": number_of_roses
        })
        else:
            return jsonify({"error": "Annotated video not found."}), 404
                
     # Catch unexpected errors and return message
    except Exception as e:
        return jsonify({"error": str(e)}), 500

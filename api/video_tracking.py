from flask import Blueprint, jsonify, request, send_file
from src.track_roses_advanced import track_roses_advanced
import os

video_tracking = Blueprint('video_tracking', __name__)
model = 'data/best.pt'
tracker_path = 'config/modified_botsort.yaml'

# POST endpoint for tracking roses in a video file
@video_tracking.route("/track/video", methods=["POST"])
def track_video():
    try:
        # Ensure the uploads/videos directory exists
        video_upload_dir = os.path.join('uploads', 'videos')
        os.makedirs(video_upload_dir, exist_ok=True)

        # Check if a file is uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded."}), 400

        # Save the uploaded video file
        file = request.files['file']
        filename = file.filename
        file_path = os.path.join(video_upload_dir, filename)
        file.save(file_path)

        # Define output path for annotated video
        output_path = 'runs/detect/track/video/'
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Track roses using a video file
        video_output, number_of_roses  = track_roses_advanced(
            model_path = model,
            tracker_path = tracker_path,
            input_source = file_path,
            output_path = output_path,
            conf=0.7,
            iou=0.5
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

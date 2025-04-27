import os
import threading
from flask import Blueprint, jsonify
from src.services.rose_tracker import RoseTrackerService

realtime_tracking = Blueprint('realtime_tracking', __name__)
rose_tracker_service = RoseTrackerService() 

is_recording = False  # Global flag to control recording
tracking_data = {"number_of_roses": 0}  # Shared data structure

# Endpoint to start real-time tracking
@realtime_tracking.route("/track/realtime/start", methods=["POST"])
def track_realtime():
    global is_recording
    if is_recording:
        return jsonify({"error": "Real-time tracking is already running."}), 400

    is_recording = True

    # Define output path for annotated video
    output_path = 'runs/detect/track/webcam/'
    # Ensure the output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    def run_tracking():
        global is_recording
        try:
            rose_tracker_service.track(
                input_source=0,  # Use webcam (0 for default camera)
                output_path=output_path,
                tracking_data=tracking_data,
                is_recording_flag=lambda: is_recording  # Pass the flag as a lambda function
            )
        finally:
            is_recording = False

    # Run tracking in a separate thread
    threading.Thread(target=run_tracking).start()
    return jsonify({"message": "Real-time tracking started. Check the webcam feed."}), 200


# Endpoint to stop real-time tracking
@realtime_tracking.route("/track/realtime/stop", methods=["POST"])
def stop_realtime():
    global is_recording
    if not is_recording:
        return jsonify({"error": "No real-time tracking is running."}), 400

    is_recording = False
    return jsonify({"message": "Real-time tracking stopped."}), 200

# Endpoint to get the current tracking data
@realtime_tracking.route("/track/realtime/data", methods=["GET"])
def get_realtime_data():
    return jsonify(tracking_data), 200
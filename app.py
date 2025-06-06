from datetime import timedelta
import os
from flask import Flask, jsonify
from flask_cors import CORS
from api.controllers import (
    ImageTrackingController,
    VideoTrackingController,
    RealtimeTrackingController,
    ModelTrainingController
)
from config.yolo_botsort import download_and_modify_botsort


def create_app():
    # Initialize the Flask application
    app = Flask(__name__)

    # download the yolo-botsort tracker and modify to suit the project use case    
    download_and_modify_botsort()

    # Configure CORS
    CORS(app)

    # Initialize controllers
    image_tracking_controller = ImageTrackingController()
    video_tracking_controller = VideoTrackingController()
    realtime_tracking_controller = RealtimeTrackingController()
    model_training_controller = ModelTrainingController()

    # Register Blueprints
    app.register_blueprint(image_tracking_controller.blueprint)
    app.register_blueprint(video_tracking_controller.blueprint)
    app.register_blueprint(realtime_tracking_controller.blueprint)
    app.register_blueprint(model_training_controller.blueprint)

    return app

# Entry point for running the application.
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
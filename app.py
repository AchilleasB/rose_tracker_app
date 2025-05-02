from datetime import timedelta
import os
from flask import Flask
from flask_cors import CORS # type: ignore
from api.controllers import (
    ImageTrackingController,
    VideoTrackingController,
    RealtimeTrackingController,
    ModelRetrainingController
)
from config.yolo_botsort import download_and_modify_botsort
from config.database import db


def create_app():
    # Initialize the Flask application
    app = Flask(__name__)

    # download the yolo-botsort tracker and modify to suit the project use case    
    download_and_modify_botsort()

    # Initialize the database 
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///roses.db'
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # db.init_app(app)

    # Configure CORS
    CORS(app)

    # Initialize controllers
    image_tracking_controller = ImageTrackingController()
    video_tracking_controller = VideoTrackingController()
    realtime_tracking_controller = RealtimeTrackingController()
    model_retraining_controller = ModelRetrainingController()

    # Register Blueprints
    app.register_blueprint(image_tracking_controller.blueprint)
    app.register_blueprint(video_tracking_controller.blueprint)
    app.register_blueprint(realtime_tracking_controller.blueprint)
    app.register_blueprint(model_retraining_controller.blueprint)

    return app

# Entry point for running the application.
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
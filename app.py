from flask import Flask
from api.video_tracking import video_tracking
from api.image_tracking import image_tracking
from api.realtime_tracking import realtime_tracking
from src.yolo_botsort import download_and_modify_botsort
import os
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

    # Register Blueprints
    app.register_blueprint(video_tracking)
    app.register_blueprint(image_tracking)
    app.register_blueprint(realtime_tracking)

    # Ensure necessary directories exist
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('runs/detect/track', exist_ok=True)

    
    return app

# Entry point for running the application.
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from api.video_tracking import video_tracking
from api.image_tracking import image_tracking
from api.realtime_tracking import realtime_tracking
from config.settings import Settings
from api.retrain_model import retrain_bp
from src.yolo_botsort import download_and_modify_botsort
from config.database import db

settings = Settings()

def create_app():
    # Initialize the Flask application
    app = Flask(__name__)

    # download the yolo-botsort tracker and modify to suit the project use case    
    download_and_modify_botsort()

    # Configure the application
    # app.config['SECRET_KEY'] = settings.SECRET_KEY
    # app.config['DEBUG'] = settings.FLASK_DEBUG
    # app.config['JWT_SECRET_KEY'] = settings.JWT_SECRET_KEY
    # app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    # app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Initialize the database 
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///roses.db'
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # db.init_app(app)

    # Configure CORS
    CORS(app)

    # Register Blueprints
    app.register_blueprint(video_tracking)
    app.register_blueprint(image_tracking)
    app.register_blueprint(realtime_tracking)
    app.register_blueprint(retrain_bp)

    return app

# Entry point for running the application.
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=settings.FLASK_DEBUG)
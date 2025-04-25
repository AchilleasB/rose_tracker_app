from flask import Flask
from api.video_tracking import video_tracking
from api.image_tracking import image_tracking
from api.realtime_tracking import realtime_tracking
from src.yolo_botsort import download_and_modify_botsort
import os

# Initialize the Flask app and load your model
app = Flask(__name__)

# Register Blueprints
app.register_blueprint(video_tracking)
app.register_blueprint(image_tracking)
app.register_blueprint(realtime_tracking)

# Ensure necessary directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('runs/detect/track', exist_ok=True)

# download the yolo-botsort tracker and modify to suit the project use case
download_and_modify_botsort()

app.run(debug=True)
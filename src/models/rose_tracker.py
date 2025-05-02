import os
from config.settings import Settings # type: ignore


class RoseTrackerModel:
    """
    A class to represent the Rose Tracker model.
    It uses YOLOv11 for object detection and a modified version of the BoT-SORT algorithm for tracking.
    """
    settings = Settings()

    def __init__(self, model_path=None):
        # Default model is always data/best.pt
        self.model = self.settings.DEFAULT_MODEL
        self.tracker = self.settings.TRACKER_CONFIG_PATH
        self.conf = self.settings.TRACKING_CONFIDENCE
        self.iou = self.settings.TRACKING_IOU
        
        # If a specific model is requested, use it instead of default
        if model_path and os.path.exists(model_path):
            self.model = model_path

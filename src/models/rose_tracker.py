class RoseTrackerModel:
    """
    A class to represent the Rose Tracker model.
    It uses YOLOv11 for object detection and a modified version of the BoT-SORT algorithm for tracking.
    """

    def __init__(self, model_path='data/best.pt', tracker_config_path='config/modified_botsort.yaml', conf=0.7, iou=0.5):
        self.model = model_path
        self.tracker = tracker_config_path
        self.conf = conf
        self.iou = iou

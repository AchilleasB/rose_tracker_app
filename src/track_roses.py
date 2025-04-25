from ultralytics import YOLO
from src.utils import count_unique_ids

def track_roses(model_path, video_path, tracker_path, conf=0.7, iou=0.5):

    """
    High-level, Streamlined Tracking Function.
    Clean and compact code, Automatically saves the annotated video to disk (save=True).
    Processes frames in a streaming manner which is efficient for large videos (stream=True).
    Less control over frame-by-frame logic

    Tracks roses in a video file.

    :param model_path: Path to the custom trained YOLO model.
    :param video_path: Path to the video.
    :param tracker_path: Optional path to the custom tracker.
    :param conf: Confidence threshold for detection.
    :param iou: IOU threshold for tracking.
    """

    # Initialize the YOLO model with the best weights   	
    model = YOLO(model_path)

    # Track roses in the video using the specified tracker and parameters
    results = model.track(
        source=video_path,
        tracker=tracker_path,
        conf=conf,
        iou=iou,
        persist=True,
        stream=True,
        save=True
    )

    # Process the results and count unique IDs
    all_results = list(results)
    if all_results:
        number_of_roses = count_unique_ids(all_results)
        print(f"Roses tracked: {number_of_roses}")
    else:
        print("No results to process.")

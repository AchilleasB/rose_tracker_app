import os
from ultralytics import YOLO
from src.utils import count_unique_ids
import cv2

def track_roses_advanced(model_path, tracker_path, input_source, output_path, tracking_data=None, is_recording_flag=None, conf=0.7, iou=0.5):

    """
    Tracks roses in either a video file, webcam, or a single image.
    Full control over frame-by-frame logic.
    Easier to debug and modify for specific use cases.
    Transparent for debugging tracking logic.
    Can be less efficient for large videos if not optimized properly.

    :param model_path: Path to YOLO model (.pt file).
    :param input_source: Webcam index (int), or path to video/image file.
    :param tracker_path: Path to tracker config (e.g., modified_botsort.yaml).
    :param conf: Confidence threshold.
    :param iou: IOU threshold.
    """

    model = YOLO(model_path)

    # Check if input is an image based on file extension
    if isinstance(input_source, str) and input_source.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')):
        return track_image(model, tracker_path, input_source, output_path, conf, iou)       
    
    # Check if input is real-time (webcam) 
    if isinstance(input_source, int):
        return track_realtime(model, tracker_path, input_source, output_path, conf, iou, tracking_data, is_recording_flag)
    
    # Otherwise, assume it's a video file
    return track_video(model, tracker_path, input_source, output_path, conf, iou)
  

# Track functions
def track_realtime(model, tracker_path, input_source, output_path, conf, iou, tracking_data, is_recording_flag):
    """
    Tracks roses in real-time using a webcam.
    Updates shared data structure with live results.
    """
    cap = cv2.VideoCapture(input_source)
    video_output = os.path.join(output_path, 'webcam_output.mp4')
    out = cv2.VideoWriter(video_output, cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480)) 

    try:
        while is_recording_flag and is_recording_flag():
            success, frame = cap.read()
            if not success:
                break

            # Perform tracking on the current frame
            results = model.track(
                source=frame,
                tracker=tracker_path,
                conf=conf,
                iou=iou,
                persist=True
            )

            # Annotate the frame
            annotated_frame = results[0].plot()
            out.write(annotated_frame)

            # Update shared data structure
            if tracking_data is not None:
                tracking_data["number_of_roses"] = count_unique_ids(results)

    finally:
        cap.release()
        out.release()

    print("Real-time tracking stopped. Video saved:", video_output)
    return video_output, tracking_data["number_of_roses"]



def track_video(model, tracker_path, input_source, output_path, conf, iou): 
    cap = cv2.VideoCapture(input_source)

    # Read first frame to get properties
    success, frame = cap.read()
    if not success:
        print("Failed to read from video source.")
        return
    
    # Get video properties
    height, width = frame.shape[:2]
    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps > 0 else 30

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    video_output = get_video_output_path(input_source, output_path)
    out = cv2.VideoWriter(video_output, fourcc, fps, (width, height))

    # Initialize the tracker
    all_results = []

    try:
        while success:
            results = model.track(
                source=frame,
                tracker=tracker_path,
                conf=conf,
                iou=iou,
                persist=True
            )

            # Process results and save to video
            all_results.extend(results)
            annotated_frame = results[0].plot()
            out.write(annotated_frame)

            # Process the next frame until the end of the video
            success, frame = cap.read()
           
        number_of_roses = get_number_of_roses(all_results)
        
    except KeyboardInterrupt:
        print("\nTracking interrupted. Exiting gracefully.")
    finally:
        cap.release()
        out.release()

    print("Video processed and saved:", video_output, "Number of roses:", number_of_roses)
    return video_output, number_of_roses

def track_image(model, tracker_path, input_source, output_path, conf, iou):
    img = cv2.imread(input_source)
    if img is None:
        print("Failed to read the image.")
        return

    results = model.track(source=img, tracker=tracker_path, conf=conf, iou=iou, persist=True)
    annotated_frame = results[0].plot()
    if annotated_frame is None:
        print("Failed to annotate the image.")
        return
    
    filename = os.path.basename(input_source)
    image_output = os.path.join(output_path, filename)
    cv2.imwrite(image_output, annotated_frame)

    number_of_roses = get_number_of_roses(results)
    print("Image processed and saved:", image_output)
    return image_output, number_of_roses

# Helper functions

def get_number_of_roses(all_results):
    """
    Process the results and count unique IDs.
    """ 
    if all_results:
        number_of_roses = count_unique_ids(all_results)
        # print(f"Roses tracked: {number_of_roses}")
    else:
        print("No results to process.")
    return number_of_roses

def get_video_output_path(input_source, output_path):
    """Generate the output path for the processed video."""
    if isinstance(input_source, int):  # Real-time (webcam)
        return os.path.join(output_path, 'webcam_output.mp4')
    else:  # Video file
        return os.path.join(output_path, os.path.basename(input_source))
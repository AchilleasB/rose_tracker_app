# function to count unique IDs
import cv2
import platform

def count_unique_ids(results):
    """
    Count the unique IDs in the results (detected objects)
    """
    unique_ids = set()
    for r in results:
        if r.boxes.id is not None:
            ids = r.boxes.id.int().tolist()
            unique_ids.update(ids)
    # print(f"Total unique roses tracked: {len(unique_ids)}")
    return len(unique_ids)


def get_camera():
    """
    Get the first available camera with Windows-specific handling
    """	
    system = platform.system().lower()
    print(f"Detected system: {system}")

    if system == 'windows':
        # Try DirectShow first
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print("Successfully opened camera with DirectShow")
                return cap
            cap.release()
        
        # Try default backend
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print("Successfully opened camera with default backend")
                return cap
            cap.release()
    else:
        # For Linux/Mac
        for i in range(4):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"Successfully opened camera {i}")
                        return cap
                    cap.release()
            except Exception as e:
                print(f"Error accessing camera {i}: {str(e)}")
    
    print("Failed to open any camera")
    return None
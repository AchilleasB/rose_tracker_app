from src.services.tracking_service.base_tracking_service import BaseTrackingService
import os

class VideoTrackingService(BaseTrackingService):
    """Service for tracking roses in videos"""
    
    def track_video(self, input_source, output_path):
        """Tracks roses in a video file and saves the annotated video."""
        self.validate_video_source(input_source)
        cap, fps, (width, height) = self.read_video(input_source)
        
        output_file = self.get_video_output_path(input_source, output_path)
        
        all_results = []
        frames = []

        try:
            while True:
                success, frame = cap.read()
                if not success:
                    break
                
                results = self.model.track(
                    source=frame,
                    tracker=self.tracker,
                    conf=self.conf,
                    iou=self.iou,
                    persist=True
                )

                all_results.extend(results)
                annotated_frame = results[0].plot()
                if annotated_frame is not None:
                    frames.append(annotated_frame)
            
            self.save_video(output_file, frames, fps)
            number_of_roses = self.get_number_of_roses(all_results)
            
        except KeyboardInterrupt:
            print("\nTracking interrupted. Exiting gracefully.")
        finally:
            cap.release()

        print("Video processed and saved:", output_file, "Number of roses:", number_of_roses)
        return output_file, number_of_roses


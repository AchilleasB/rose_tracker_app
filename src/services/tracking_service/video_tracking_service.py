from src.services.tracking_service.base_tracking_service import BaseTrackingService
import os
import cv2
import subprocess
import logging

logger = logging.getLogger(__name__)

class VideoTrackingService(BaseTrackingService):
    """Service for tracking roses in videos with web-compatible output"""
    
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
            logger.info("\nTracking interrupted. Exiting gracefully.")
        finally:
            cap.release()

        logger.info(f"Video processed and saved: {output_file} Number of roses: {number_of_roses}")
        return output_file, number_of_roses
    
    def save_video(self, output_file, frames, fps):
        """Save video with web-compatible encoding using FFmpeg"""
        if not frames:
            logger.error("No frames to save")
            raise ValueError("No frames to save")
        
        height, width = frames[0].shape[:2]
        temp_file = output_file.replace('.mp4', '_temp.mp4')
        
        # Save temporary video with OpenCV
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_file, fourcc, fps, (width, height))
        
        if not out.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            temp_file = temp_file.replace('.mp4', '_temp.avi')
            out = cv2.VideoWriter(temp_file, fourcc, fps, (width, height))
            
            if not out.isOpened():
                logger.error("Could not open video writer")
                raise RuntimeError("Could not open video writer")
        
        for frame in frames:
            out.write(frame)
        
        out.release()
        
        # Convert to web-compatible format
        self._convert_to_web_format(temp_file, output_file, fps)
        
        return output_file
    
    def _convert_to_web_format(self, input_file, output_file, fps):
        """Convert video to web-compatible format using FFmpeg"""
        try:
            cmd = [
                'ffmpeg', 
                '-i', input_file,
                '-c:v', 'libx264',
                '-profile:v', 'baseline',
                '-level', '3.0',
                '-pix_fmt', 'yuv420p',
                '-crf', '28',
                '-preset', 'fast',
                '-movflags', '+faststart',
                '-r', str(int(fps)),
                '-y',
                output_file
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)
            
            # Clean up temporary file
            if os.path.exists(input_file):
                os.remove(input_file)
                
        except Exception as e:
            logger.error(f"FFmpeg conversion failed: {str(e)}")
            # Fallback: use original file if conversion fails
            self._handle_conversion_fallback(input_file, output_file)
    
    def _handle_conversion_fallback(self, input_file, output_file):
        """Handle FFmpeg conversion failure by using original file"""
        logger.warning(f"FFmpeg conversion failed, using original file: {input_file} -> {output_file}")
        if os.path.exists(input_file):
            import shutil
            shutil.copy2(input_file, output_file)
            os.remove(input_file)
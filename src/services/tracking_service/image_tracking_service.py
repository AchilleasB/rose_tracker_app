from src.services.tracking_service.base_tracking_service import BaseTrackingService
import os
import cv2
import logging

logger = logging.getLogger(__name__)

class ImageTrackingService(BaseTrackingService):
    """Service for tracking roses in images"""
    
    def track_image(self, input_source, output_path):
        """Tracks roses in an image file and saves the annotated image."""
        # Validate and read image
        self.validate_image_source(input_source)
        image = self.read_image(input_source)
        
        # Process image with model
        results = self.model.track(
            source=image,
            tracker=self.tracker,
            conf=self.conf,
            iou=self.iou,
            persist=True
        )
        
        # Create annotated image
        annotated_image = results[0].plot()
        if annotated_image is None:
            logger.error("Failed to create annotated image")
            raise ValueError("Failed to create annotated image")
        
        # Save annotated image
        output_file = self.get_image_output_path(input_source, output_path)
        self.save_image(output_file, annotated_image)
        
        # Save annotations in YOLO format alongside the tracked image
        self._save_image_annotations(results, output_file)
        
        # Get tracking metadata
        number_of_roses = self.get_number_of_roses(results)
        
        logger.info(f"Image processed and saved: {output_file} Number of roses: {number_of_roses}")
        return output_file, number_of_roses

    def _save_image_annotations(self, results, image_path):
        """Save tracking results as YOLO format annotations.
        """
        if not results or not image_path:
            return

        # Get image dimensions for normalization
        image = cv2.imread(image_path)
        if image is None:
            logger.error("Failed to read image")
            raise ValueError("Failed to read image")
        img_height, img_width = image.shape[:2]

        # Create label filename (same as image but with .txt extension)
        label_filename = os.path.splitext(os.path.basename(image_path))[0] + '.txt'
        label_path = os.path.join(os.path.dirname(image_path), 'labels', label_filename)
        
        # Create labels directory if it doesn't exist
        os.makedirs(os.path.dirname(label_path), exist_ok=True)
        
        # Convert tracking results to YOLO format and save
        with open(label_path, 'w') as f:
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get normalized coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    width = x2 - x1
                    height = y2 - y1
                    x_center = x1 + width/2
                    y_center = y1 + height/2

                    # Normalize coordinates
                    x_center = x_center / img_width
                    y_center = y_center / img_height
                    width = width / img_width
                    height = height / img_height

                    # Write annotation in YOLO format
                    f.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n") 
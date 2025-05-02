from src.services.tracking_service.base_tracking_service import BaseTrackingService
import os

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
            raise ValueError("Failed to create annotated image")
        
        # Save annotated image
        output_file = self.get_image_output_path(input_source, output_path)
        self.save_image(output_file, annotated_image)
        
        # Get tracking metadata
        number_of_roses = self.get_number_of_roses(results)
        
        print("Image processed and saved:", output_file, "Number of roses:", number_of_roses)
        return output_file, number_of_roses 
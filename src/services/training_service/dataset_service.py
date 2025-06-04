"""
Dataset Service

This module provides functionality for managing the dataset used in model training.
It handles annotation saving, dataset preparation, and dataset organization.
"""

import os
import random
import shutil
from datetime import datetime
from config.settings import Settings
from src.utils.training_utils import TrainingUtils

class DatasetService:
    """Service class for dataset management operations."""
    
    def __init__(self):
        """Initialize the dataset service."""
        self.settings = Settings()
        
        # Dataset paths
        self.data_dir = self.settings.DATA_DIR
        self.temp_dir = os.path.join(self.data_dir, 'temp')
        self.latest_dataset_dir = os.path.join(self.data_dir, 'latest_dataset')
        
        # Create essential directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.latest_dataset_dir, exist_ok=True)

    def save_annotation(self, original_image_path, annotation_data):
        """Save multiple annotations for an original image in YOLO format."""
        
        # 1. Validate and prepare paths
        image_filename = original_image_path  # This is already file_id.jpg from frontend
        file_id = os.path.splitext(image_filename)[0]  # Extract file_id without extension
        
        original_image_full_path = os.path.join(self.settings.UPLOAD_IMAGES_DIR, image_filename)
        tracked_labels_path = os.path.join(self.settings.TRACKING_IMAGES_DIR, 'labels', f"{file_id}.txt")
        
        if not os.path.exists(original_image_full_path):
            raise FileNotFoundError(f"Original image not found: {original_image_full_path}")

        # 2. Validate annotation structure
        if 'boxes' not in annotation_data:
            raise ValueError("No boxes found in annotation data")
        
        if 'media_width' not in annotation_data or 'media_height' not in annotation_data:
            raise ValueError("No media dimensions found in annotation data")

        img_width = annotation_data['media_width']
        img_height = annotation_data['media_height']

        # 3. Process all boxes in the annotation
        all_annotations = []
        for box in annotation_data['boxes']:
            try:
                # Validate box dimensions (minimum 10 pixels)
                pixel_width = box['width'] * img_width
                pixel_height = box['height'] * img_height
                if pixel_width < 10 or pixel_height < 10:
                    print(f"Skipping small annotation: {pixel_width}x{pixel_height} pixels")
                    continue
                    
                # Box is already in normalized format from frontend
                # Just need to convert to YOLO format (class x_center y_center width height)
                yolo_annotation = f"0 {box['x']} {box['y']} {box['width']} {box['height']}"
                all_annotations.append(yolo_annotation)
                
            except Exception as e:
                print(f"Error processing annotation: {str(e)}")
                continue

        if not all_annotations:
            raise ValueError("No valid annotations to save (all were too small or invalid)")

        # 4. Get existing annotations from tracked labels
        existing_annotations = []
        if os.path.exists(tracked_labels_path):
            with open(tracked_labels_path, 'r') as f:
                existing_annotations = [line.strip() for line in f.readlines() if line.strip()]

        # 5. Save to temp directory
        temp_images_dir = os.path.join(self.temp_dir, 'images')
        temp_labels_dir = os.path.join(self.temp_dir, 'labels')
        os.makedirs(temp_images_dir, exist_ok=True)
        os.makedirs(temp_labels_dir, exist_ok=True)
        
        # Copy original image to temp if not exists
        temp_image_path = os.path.join(temp_images_dir, image_filename)
        if not os.path.exists(temp_image_path):
            shutil.copy2(original_image_full_path, temp_image_path)
        
        # Save all annotations (existing + new) to temp labels
        temp_label_path = os.path.join(temp_labels_dir, f"{file_id}.txt")
        combined_annotations = existing_annotations + all_annotations
        
        with open(temp_label_path, 'w') as f:
            f.write('\n'.join(combined_annotations))
        
        return {
            "original_image_path": original_image_full_path,
            "tracked_labels_path": tracked_labels_path,
            "temp_image_path": temp_image_path,
            "temp_label_path": temp_label_path,
            "new_annotations_count": len(all_annotations),
            "existing_annotations_count": len(existing_annotations),
            "total_annotations_count": len(combined_annotations)
        }

    def prepare_dataset(self):
        """Prepare the dataset by splitting into train and val sets."""
        temp_images_dir = os.path.join(self.temp_dir, 'images')
        temp_labels_dir = os.path.join(self.temp_dir, 'labels')
        
        if not os.path.exists(temp_images_dir) or not os.path.exists(temp_labels_dir):
            raise ValueError("No annotations found. Please add some annotations before preparing the dataset.")
            
        # Get all image files
        image_files = [f for f in os.listdir(temp_images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not image_files:
            raise ValueError("No images found in the temporary directory.")
            
        # Verify that each image has a corresponding label file
        valid_image_files = []
        for image_file in image_files:
            label_file = os.path.splitext(image_file)[0] + '.txt'
            label_path = os.path.join(temp_labels_dir, label_file)
            if os.path.exists(label_path):
                # Verify label file is not empty
                if os.path.getsize(label_path) > 0:
                    valid_image_files.append(image_file)
                else:
                    print(f"Warning: Empty label file for {image_file}")
            else:
                print(f"Warning: No label file found for {image_file}")
        
        if not valid_image_files:
            raise ValueError("No valid image-label pairs found. Please ensure each image has a corresponding non-empty label file.")
            
        # Shuffle the files for random split
        random.shuffle(valid_image_files)
        
        # Calculate split index (80% train, 20% val)
        split_idx = int(len(valid_image_files) * 0.8)
        train_files = valid_image_files[:split_idx]
        val_files = valid_image_files[split_idx:]
        
        # Prepare dataset structure
        train_dir, val_dir = TrainingUtils.prepare_dataset_structure(self.latest_dataset_dir, self.temp_dir)
        
        # Copy files to their respective directories
        for files, target_dir in [(train_files, train_dir), (val_files, val_dir)]:
            for image_file in files:
                # Copy image
                src_image = os.path.join(temp_images_dir, image_file)
                dst_image = os.path.join(target_dir, 'images', image_file)
                shutil.copy2(src_image, dst_image)
                
                # Copy corresponding label
                label_file = os.path.splitext(image_file)[0] + '.txt'
                src_label = os.path.join(temp_labels_dir, label_file)
                dst_label = os.path.join(target_dir, 'labels', label_file)
                shutil.copy2(src_label, dst_label)
        
        # Create dataset.yaml
        yaml_path = TrainingUtils.create_dataset_yaml(self.latest_dataset_dir)
        
        return {
            "dataset_dir": self.latest_dataset_dir,
            "yaml_path": yaml_path,
            "train_count": len(train_files),
            "val_count": len(val_files)
        }

    def clear_temp_dataset(self):
        """Clear the temporary dataset directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            os.makedirs(os.path.join(self.temp_dir, 'images'))
            os.makedirs(os.path.join(self.temp_dir, 'labels'))
        return {"message": "Temporary dataset cleared successfully"}

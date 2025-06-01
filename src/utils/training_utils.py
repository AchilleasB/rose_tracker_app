"""
Training utilities for the Rose Tracker Application.
Contains helper functions for model training, dataset preparation, and metadata management.
"""

import os
import shutil
import json
import yaml
import cv2
import random
from datetime import datetime

class TrainingUtils:
    """Utility class for training-related operations."""

    @staticmethod
    def validate_annotation(image_path, annotation_data):
        """Validate annotation coordinates and dimensions."""
        if not os.path.exists(image_path):
            raise FileNotFoundError("Image not found")

        # Get image dimensions for normalization
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Failed to read image")
        img_height, img_width = image.shape[:2]

        # Validate new annotation coordinates
        x_center = annotation_data['x_center']
        y_center = annotation_data['y_center']
        width = annotation_data['width']
        height = annotation_data['height']

        # Check if coordinates are within image boundaries
        if not (0 <= x_center <= img_width and 0 <= y_center <= img_height):
            raise ValueError(f"Annotation center point ({x_center}, {y_center}) is outside image boundaries ({img_width}x{img_height})")

        # Check if width and height are positive and reasonable
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid annotation dimensions: width={width}, height={height}")
        
        # Check if the bounding box is within image boundaries
        half_width = width / 2
        half_height = height / 2
        if (x_center - half_width < 0 or x_center + half_width > img_width or
            y_center - half_height < 0 or y_center + half_height > img_height):
            raise ValueError(f"Annotation bounding box exceeds image boundaries")

        # Check if the bounding box size is reasonable
        min_size = 10
        max_size = min(img_width, img_height) * 0.9  # maximum size as 90% of image
        if width < min_size or height < min_size:
            raise ValueError(f"Annotation is too small: {width}x{height} pixels (minimum {min_size} pixels)")
        if width > max_size or height > max_size:
            raise ValueError(f"Annotation is too large: {width}x{height} pixels (maximum {max_size} pixels)")

        return img_width, img_height

    @staticmethod
    def normalize_annotation(x_center, y_center, width, height, img_width, img_height):
        """Convert annotation coordinates to YOLO format (normalized)."""
        return {
            'x_center': x_center / img_width,
            'y_center': y_center / img_height,
            'width': width / img_width,
            'height': height / img_height
        }

    @staticmethod
    def read_existing_annotations(label_path):
        """Read existing annotations from a label file."""
        existing_annotations = []
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    try:
                        class_id, x, y, w, h = map(float, line.strip().split())
                        existing_annotations.append({
                            'x_center': x,
                            'y_center': y,
                            'width': w,
                            'height': h
                        })
                    except ValueError:
                        continue
        return existing_annotations

    @staticmethod
    def save_annotations(label_path, annotations):
        """Save annotations to a label file in YOLO format."""
        with open(label_path, 'w') as f:
            for ann in annotations:
                f.write(f"0 {ann['x_center']:.6f} {ann['y_center']:.6f} {ann['width']:.6f} {ann['height']:.6f}\n")

    @staticmethod
    def prepare_dataset_structure(base_dir, temp_dir):
        """Prepare the dataset directory structure."""
        # Clean up and create latest_dataset directory
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
        
        # Create train and val directories
        train_dir = os.path.join(base_dir, 'train')
        val_dir = os.path.join(base_dir, 'val')
        
        for split_dir in [train_dir, val_dir]:
            for subdir in ['images', 'labels']:
                os.makedirs(os.path.join(split_dir, subdir), exist_ok=True)
        
        return train_dir, val_dir

    @staticmethod
    def create_dataset_yaml(dataset_dir):
        """Create dataset.yaml file for YOLO training."""
        dataset_yaml = {
            'path': dataset_dir,
            'train': 'train/images',
            'val': 'val/images',
            'names': {
                0: 'rose'
            },
            'nc': 1
        }
        
        yaml_path = os.path.join(dataset_dir, 'dataset.yaml')
        with open(yaml_path, 'w') as f:
            yaml.dump(dataset_yaml, f, default_flow_style=False)
        
        return yaml_path

    @staticmethod
    def extract_training_metrics(results):
        """Extract metrics from training results."""
        metrics = {}
        try:
            # Try to get metrics from results.results_dict
            if hasattr(results, 'results_dict'):
                metrics = {
                    'mAP50': float(results.results_dict.get('metrics/mAP50(B)', 0)),
                    'precision': float(results.results_dict.get('metrics/precision(B)', 0)),
                    'recall': float(results.results_dict.get('metrics/recall(B)', 0))
                }
            # If not found in results_dict, try to get from results.results
            elif hasattr(results, 'results'):
                metrics = {
                    'mAP50': float(results.results.get('metrics/mAP50(B)', 0)),
                    'precision': float(results.results.get('metrics/precision(B)', 0)),
                    'recall': float(results.results.get('metrics/recall(B)', 0))
                }
            # If still not found, try to get from results directly
            else:
                metrics = {
                    'mAP50': float(getattr(results, 'mAP50', 0)),
                    'precision': float(getattr(results, 'precision', 0)),
                    'recall': float(getattr(results, 'recall', 0))
                }
        except (AttributeError, ValueError, TypeError) as e:
            print(f"Warning: Could not extract all metrics: {str(e)}")
            # Set default values if extraction fails
            metrics = {
                'mAP50': 0.0,
                'precision': 0.0,
                'recall': 0.0
            }
        return metrics

    @staticmethod
    def load_model_metadata(metadata_file):
        """Load model metadata from JSON file."""
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {"models": []}

    @staticmethod
    def save_model_metadata(metadata_file, metadata):
        """Save model metadata to JSON file."""
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4) 
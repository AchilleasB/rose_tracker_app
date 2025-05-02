"""
Model Retraining Service

This module provides functionality for retraining the rose detection model
using user-provided annotations. It handles the management of model versions,
training data organization, and model retraining process.
"""

import os
import shutil
import json
import yaml
import cv2
import torch
import random
from datetime import datetime
from ultralytics import YOLO
from config.settings import Settings

class ModelRetrainerService:
    """Service class for model retraining operations."""
    settings = Settings()

    def __init__(self):
        """Initialize the model retrainer service."""
        # Model paths
        self.models_dir = self.settings.MODELS_DIR
        self.default_model = self.settings.DEFAULT_MODEL
        self.metadata_file = self.settings.MODEL_METADATA_FILE
        
        # Dataset paths
        self.data_dir = self.settings.DATA_DIR
        self.temp_dir = os.path.join(self.data_dir, 'temp')
        self.latest_dataset_dir = os.path.join(self.data_dir, 'latest_dataset')
        self.training_outputs_dir = os.path.join(self.data_dir, 'training_outputs')
        
        # Create only the essential directories
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.latest_dataset_dir, exist_ok=True)
        os.makedirs(self.training_outputs_dir, exist_ok=True)

    def save_annotation(self, tracked_image_path, annotation_data):
        """Save a new annotation for an existing image in YOLO format.
        """
        if not os.path.exists(tracked_image_path):
            raise FileNotFoundError("Tracked image not found")

        # Get the original image from uploads
        image_filename = os.path.basename(tracked_image_path)
        original_image_path = os.path.join(self.settings.UPLOADS_DIR, 'images', image_filename)
        if not os.path.exists(original_image_path):
            raise FileNotFoundError("Original image not found in uploads")

        # Get image dimensions for normalization
        image = cv2.imread(original_image_path)
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

        # Check if the bounding box size is reasonable (not too small or too large)
        min_size = 10  # minimum size in pixels
        max_size = min(img_width, img_height) * 0.9  # maximum size as 90% of image
        if width < min_size or height < min_size:
            raise ValueError(f"Annotation is too small: {width}x{height} pixels (minimum {min_size} pixels)")
        if width > max_size or height > max_size:
            raise ValueError(f"Annotation is too large: {width}x{height} pixels (maximum {max_size} pixels)")

        # Convert new annotation to YOLO format (normalized)
        new_annotation = {
            'x_center': x_center / img_width,
            'y_center': y_center / img_height,
            'width': width / img_width,
            'height': height / img_height
        }

        # Get existing annotations from runs/detect/track/images/labels
        label_filename = os.path.splitext(image_filename)[0] + '.txt'
        existing_label_path = os.path.join(os.path.dirname(tracked_image_path), 'labels', label_filename)
        existing_annotations = []
        
        if os.path.exists(existing_label_path):
            with open(existing_label_path, 'r') as f:
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

        # Save to temporary directory for training
        temp_images_dir = os.path.join(self.temp_dir, 'images')
        temp_labels_dir = os.path.join(self.temp_dir, 'labels')
        os.makedirs(temp_images_dir, exist_ok=True)
        os.makedirs(temp_labels_dir, exist_ok=True)
        
        # Copy original image to temp directory if not exists
        temp_image_path = os.path.join(temp_images_dir, image_filename)
        if not os.path.exists(temp_image_path):
            shutil.copy2(original_image_path, temp_image_path)
        
        # Save all annotations to temp labels
        temp_label_path = os.path.join(temp_labels_dir, label_filename)
        with open(temp_label_path, 'w') as f:
            # Write existing annotations
            for ann in existing_annotations:
                f.write(f"0 {ann['x_center']:.6f} {ann['y_center']:.6f} {ann['width']:.6f} {ann['height']:.6f}\n")
            
            # Write new annotation
            f.write(f"0 {new_annotation['x_center']:.6f} {new_annotation['y_center']:.6f} {new_annotation['width']:.6f} {new_annotation['height']:.6f}\n")
        
        return {
            "original_image_path": original_image_path,
            "tracked_image_path": tracked_image_path,
            "temp_image_path": temp_image_path,
            "temp_label_path": temp_label_path,
            "total_annotations": len(existing_annotations) + 1,
            "annotations": {
                "new": new_annotation,
                "existing": existing_annotations
            }
        }

    def prepare_dataset(self):
        """Prepare the dataset by splitting into train and val sets"""
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
        
        # Clean up and create latest_dataset directory
        if os.path.exists(self.latest_dataset_dir):
            shutil.rmtree(self.latest_dataset_dir)
        
        # Create train and val directories
        train_dir = os.path.join(self.latest_dataset_dir, 'train')
        val_dir = os.path.join(self.latest_dataset_dir, 'val')
        
        for split_dir in [train_dir, val_dir]:
            for subdir in ['images', 'labels']:
                os.makedirs(os.path.join(split_dir, subdir), exist_ok=True)
        
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
        dataset_yaml = {
            'path': self.latest_dataset_dir,
            'train': 'train/images',
            'val': 'val/images',
            'names': {
                0: 'rose'
            },
            'nc': 1
        }
        
        yaml_path = os.path.join(self.latest_dataset_dir, 'dataset.yaml')
        with open(yaml_path, 'w') as f:
            yaml.dump(dataset_yaml, f, default_flow_style=False)
        
        return {
            "dataset_dir": self.latest_dataset_dir,
            "yaml_path": yaml_path,
            "train_count": len(train_files),
            "val_count": len(val_files)
        }

    def retrain_model(self):
        """Retrain the model using the collected annotations"""
        # First prepare the dataset
        try:
            dataset_info = self.prepare_dataset()
            print(f"Dataset prepared successfully:")
            print(f"- Training images: {dataset_info['train_count']}")
            print(f"- Validation images: {dataset_info['val_count']}")
            print(f"- Dataset directory: {dataset_info['dataset_dir']}")
        except ValueError as e:
            raise ValueError(f"Dataset preparation failed: {str(e)}")

        # Load the default model
        model = YOLO(self.default_model)
        print(f"Loaded base model: {self.default_model}")
        
        # Generate unique model name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_name = f"model_{timestamp}"
        
        # Create training output directory for this run
        training_output_dir = os.path.join(self.training_outputs_dir, model_name)
        os.makedirs(training_output_dir, exist_ok=True)
        
        print(f"Starting model training...")
        # Retrain the model
        results = model.train(
            data=dataset_info['yaml_path'],
            epochs=20,
            imgsz=640,
            batch=16,
            name=model_name,
            project=training_output_dir,
            patience=50,
            save=True,
            device='0' if torch.cuda.is_available() else 'cpu',
            exist_ok=True,
            pretrained=True,
            optimizer='auto',
            verbose=True
        )
        
        print(f"Training completed. Saving best model...")
        # Copy the best model to the models directory
        best_model_path = os.path.join(training_output_dir, model_name, 'weights/best.pt')
        if not os.path.exists(best_model_path):
            raise FileNotFoundError("Model training completed but best model not found")
            
        new_model_path = os.path.join(self.models_dir, f"{model_name}.pt")
        shutil.copy2(best_model_path, new_model_path)
        
        # Extract metrics from results
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
        
        # Update metadata
        metadata = self.load_model_metadata()
        metadata['models'].append({
            'name': f"{model_name}.pt",
            'created_at': timestamp,
            'training_dir': training_output_dir,
            'metrics': metrics
        })
        self.save_model_metadata(metadata)
        
        print(f"Training results:")
        print(f"- mAP50: {metrics['mAP50']:.4f}")
        print(f"- Precision: {metrics['precision']:.4f}")
        print(f"- Recall: {metrics['recall']:.4f}")
        
        return {
            "model_name": f"{model_name}.pt",
            "model_path": new_model_path,
            "training_dir": training_output_dir,
            "metrics": metrics
        }

    def load_model_metadata(self):
        """Load model metadata from JSON file"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {"models": []}

    def save_model_metadata(self, metadata):
        """Save model metadata to JSON file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
            
    def list_models(self):
        """List all available models with their metadata"""
        metadata = self.load_model_metadata()
        return {
            "default_model": self.default_model,
            "retrained_models": metadata['models']
        }

    def get_model_path(self, model_name):
        """Get the path for a specific model"""
        if model_name == 'default':
            return self.default_model
            
        model_path = os.path.join(self.models_dir, model_name)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model {model_name} not found")
            
        return model_path 
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
from src.utils.training_utils import TrainingUtils

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

    def save_annotation(self, original_image_path, annotation_data):
        """Save multiple annotations for an original image in YOLO format."""
        
        # Find the original image file
        image_filename = original_image_path
        original_image_full_path = os.path.join(self.settings.UPLOADS_DIR, 'images', image_filename)
        
        if not os.path.exists(original_image_full_path):
            raise FileNotFoundError(f"Original image not found: {original_image_full_path}")

        # Validate annotation structure
        if 'boxes' not in annotation_data:
            raise ValueError("No boxes found in annotation data")
        
        if 'image_dimensions' not in annotation_data:
            raise ValueError("No image dimensions found in annotation data")

        img_width = annotation_data['image_dimensions']['width']
        img_height = annotation_data['image_dimensions']['height']

        # Process all boxes in the annotation
        all_annotations = []
        for i, box in enumerate(annotation_data['boxes']):
            try:
                # Validate annotation size (minimum 10 pixels)
                if box['width'] < 10 or box['height'] < 10:
                    print(f"Skipping small annotation {i+1}: {box['width']}x{box['height']} pixels")
                    continue
                    
                # Convert to YOLO normalized format
                normalized_annotation = TrainingUtils.normalize_annotation(
                    box['x_center'],
                    box['y_center'],
                    box['width'],
                    box['height'],
                    img_width,
                    img_height
                )
                all_annotations.append(normalized_annotation)
                
            except Exception as e:
                print(f"Error processing annotation {i+1}: {str(e)}")
                continue

        if not all_annotations:
            raise ValueError("No valid annotations to save (all were too small or invalid)")

        # Get existing annotations from previous saves
        label_filename = os.path.splitext(image_filename)[0] + '.txt'
        existing_label_path = os.path.join(self.temp_dir, 'labels', label_filename)
        existing_annotations = TrainingUtils.read_existing_annotations(existing_label_path)

        # Save original image to temp directory if not exists
        temp_images_dir = os.path.join(self.temp_dir, 'images')
        temp_labels_dir = os.path.join(self.temp_dir, 'labels')
        os.makedirs(temp_images_dir, exist_ok=True)
        os.makedirs(temp_labels_dir, exist_ok=True)
        
        temp_image_path = os.path.join(temp_images_dir, image_filename)
        if not os.path.exists(temp_image_path):
            shutil.copy2(original_image_full_path, temp_image_path)
        
        # Combine existing and new annotations
        combined_annotations = existing_annotations + all_annotations
        
        # Save all annotations to one label file
        temp_label_path = os.path.join(temp_labels_dir, label_filename)
        TrainingUtils.save_annotations(temp_label_path, combined_annotations)
        
        return {
            "original_image_path": original_image_full_path,
            "temp_image_path": temp_image_path,
            "temp_label_path": temp_label_path,
            "new_annotations_count": len(all_annotations),
            "total_annotations_count": len(combined_annotations),
            "annotations": {
                "new": all_annotations,
                "existing": existing_annotations,
                "combined": combined_annotations
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
        metrics = TrainingUtils.extract_training_metrics(results)
        
        # Update metadata
        metadata = TrainingUtils.load_model_metadata(self.metadata_file)
        metadata['models'].append({
            'name': f"{model_name}.pt",
            'created_at': timestamp,
            'training_dir': training_output_dir,
            'metrics': metrics
        })
        TrainingUtils.save_model_metadata(self.metadata_file, metadata)
        
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

    def list_models(self):
        """List all available models with their metadata"""
        metadata = TrainingUtils.load_model_metadata(self.metadata_file)
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
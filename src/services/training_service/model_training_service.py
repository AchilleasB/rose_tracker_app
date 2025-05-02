"""
Model Retraining Service

This module provides functionality for retraining the rose detection model
using user-provided annotations. It handles the management of model versions,
training data organization, and model retraining process.
"""

import os
import shutil
import json
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
        self.annotated_data_dir = self.settings.ANNOTATED_DATA_DIR
        
        # Training paths
        self.training_output_dir = self.settings.TRAINING_OUTPUT_DIR

    def save_annotation(self, original_image_path, annotation_data):
        """Save a new annotation for an existing image"""
        if not os.path.exists(original_image_path):
            raise FileNotFoundError("Original image not found")

        # Generate unique filename with timestamp for the annotation
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        annotation_filename = f"annotated_{timestamp}.txt"
        
        # Save the annotation in YOLO format (class x_center y_center width height)
        annotation_path = os.path.join(self.annotated_data_dir, 'annotations', annotation_filename)
        os.makedirs(os.path.dirname(annotation_path), exist_ok=True)
        with open(annotation_path, 'w') as f:
            f.write(f"0 {annotation_data['x_center']} {annotation_data['y_center']} {annotation_data['width']} {annotation_data['height']}\n")
        
        # Copy the original image to the annotated data directory
        image_filename = os.path.basename(original_image_path)
        image_dir = os.path.join(self.annotated_data_dir, 'images')
        os.makedirs(image_dir, exist_ok=True)
        copied_image_path = os.path.join(image_dir, image_filename)
        if not os.path.exists(copied_image_path):
            shutil.copy2(original_image_path, copied_image_path)
        
        return {
            "original_image_path": original_image_path,
            "annotation_path": annotation_path,
            "copied_image_path": copied_image_path
        }

    def retrain_model(self):
        """Retrain the model using the collected annotations"""
        # Create dataset.yaml file for training
        dataset_yaml = {
            'path': self.annotated_data_dir,
            'train': self.annotated_data_dir,
            'val': self.annotated_data_dir,
            'names': {0: 'rose'}
        }
        
        yaml_path = os.path.join(self.annotated_data_dir, 'dataset.yaml')
        with open(yaml_path, 'w') as f:
            import yaml
            yaml.dump(dataset_yaml, f)
        
        # Always use the default model as the base for retraining
        model = YOLO(self.default_model)
        
        # Generate unique model name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_name = f"model_{timestamp}"
        
        # Retrain the model
        results = model.train(
            data=yaml_path,
            epochs=10,
            imgsz=640,
            batch=16,
            name=model_name,
            project=self.training_output_dir  # Use our custom training output directory
        )
        
        # Copy the best model to the models directory
        best_model_path = os.path.join(self.training_output_dir, model_name, 'weights/best.pt')
        if not os.path.exists(best_model_path):
            raise FileNotFoundError("Model training completed but best model not found")
            
        new_model_path = os.path.join(self.models_dir, f"{model_name}.pt")
        shutil.copy2(best_model_path, new_model_path)
        
        # Update metadata
        metadata = self.load_model_metadata()
        metadata['models'].append({
            'name': f"{model_name}.pt",
            'created_at': timestamp,
            'metrics': {
                'mAP50': float(results.results_dict.get('metrics/mAP50', 0)),
                'precision': float(results.results_dict.get('metrics/precision', 0)),
                'recall': float(results.results_dict.get('metrics/recall', 0))
            }
        })
        self.save_model_metadata(metadata)
        
        # Clean up training artifacts
        self._cleanup_training_artifacts(model_name)
        
        return {
            "model_name": f"{model_name}.pt",
            "metrics": metadata['models'][-1]['metrics']
        }

    def _cleanup_training_artifacts(self, model_name):
        """Clean up training artifacts after copying the best model"""
        training_run_dir = os.path.join(self.training_output_dir, model_name)
        if os.path.exists(training_run_dir):
            shutil.rmtree(training_run_dir)

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
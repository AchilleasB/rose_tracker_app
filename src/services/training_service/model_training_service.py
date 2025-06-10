"""
Model Training Service  provides functionality for training a detection model based on YOLO11 pretrained model
"""

import os
import shutil
import json
import yaml
import cv2
import torch
from datetime import datetime
from ultralytics import YOLO
from config.settings import Settings
from src.utils.training_utils import TrainingUtils
from src.services.training_service.dataset_service import DatasetService
import logging

logger = logging.getLogger(__name__)

class ModelTrainingService:
    """Service class for model training operations."""
    settings = Settings()

    def __init__(self):
        """Initialize the model training service."""
        # Model paths
        self.models_dir = self.settings.MODELS_DIR
        self.default_model = self.settings.DEFAULT_MODEL
        self.metadata_file = self.settings.MODEL_METADATA_FILE
        
        # Training outputs directory
        self.training_outputs_dir = os.path.join(self.settings.DATA_DIR, 'training_outputs')
        os.makedirs(self.training_outputs_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)

    def train_model(self):
        """Train the model using the prepared dataset."""
        # Initialize dataset service to get dataset info
        dataset_service = DatasetService()
        
        # First prepare the dataset
        try:
            dataset_info = dataset_service.prepare_dataset()
            logger.info(f"Dataset prepared successfully:")
            logger.info(f"- Training images: {dataset_info['train_count']}")
            logger.info(f"- Validation images: {dataset_info['val_count']}")
            logger.info(f"- Dataset directory: {dataset_info['dataset_dir']}")
        except ValueError as e:
            raise ValueError(f"Dataset preparation failed: {str(e)}")

        # Load the default model
        model = YOLO(self.default_model)
        logger.info(f"Loaded base model: {self.default_model}")
        
        # Generate unique model name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_name = f"model_{timestamp}"
        
        # Create training output directory for this run
        training_output_dir = os.path.join(self.training_outputs_dir, model_name)
        os.makedirs(training_output_dir, exist_ok=True)
        
        logger.info(f"Starting model training...")
        # Train the model
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
        
        logger.info(f"Training completed. Saving best model...")
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
        
        logger.info(f"Training results:")
        logger.info(f"- mAP50: {metrics['mAP50']:.4f}")
        logger.info(f"- Precision: {metrics['precision']:.4f}")
        logger.info(f"- Recall: {metrics['recall']:.4f}")
        
        return {
            "model_name": f"{model_name}.pt",
            "model_path": new_model_path,
            "training_dir": training_output_dir,
            "metrics": metrics
        }

    def list_models(self):
        """List all available .pt model files in the models directory."""
        try:
            # Get all .pt files in the models directory
            model_files = [f for f in os.listdir(self.models_dir) if f.endswith('.pt')]
            
            # Sort files by creation time (newest first)
            model_files.sort(key=lambda x: os.path.getctime(os.path.join(self.models_dir, x)), reverse=True)
            
            return model_files
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []

    def select_model(self, model_name):
        """Select a model as the default model and update settings."""
        if model_name == 'default':
            # Reset to original default model
            model_path = self.settings.ORIGINAL_DEFAULT_MODEL
        else:
            # Get the full path of the selected model
            model_path = os.path.join(self.models_dir, model_name)
            if not os.path.exists(model_path):
                logger.error(f"Model {model_name} not found")
                raise FileNotFoundError(f"Model {model_name} not found")
        
        # Update the settings with the new default model
        self.settings.update_default_model(model_path)
        
        # Update the instance variable
        self.default_model = model_path
        
        return {
            "model_name": model_name,
            "model_path": model_path,
            "message": f"Model {model_name} set as default"
        }
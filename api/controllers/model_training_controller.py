from flask import Blueprint, jsonify, request
import os
import json
from src.services.training_service.model_training_service import ModelTrainingService
from src.services.training_service.dataset_service import DatasetService
from config.settings import Settings
import logging

class ModelTrainingController:
    def __init__(self):
        self.settings = Settings()
        self.blueprint = Blueprint('train_model', __name__)
        self.model_trainer = ModelTrainingService()
        self.dataset_service = DatasetService()
        self._register_routes()

    def _register_routes(self):
        # Dataset and annotation routes
        self.blueprint.route('/dataset/save-annotation', methods=['POST'])(self.save_annotation)
        self.blueprint.route('/dataset/prepare', methods=['POST'])(self.prepare_dataset)
        self.blueprint.route('/dataset/clear', methods=['POST'])(self.clear_dataset)
        self.blueprint.route('/dataset/images', methods=['GET'])(self.dataset_service.get_dataset_images)
        self.blueprint.route('/dataset/prepared-images', methods=['GET'])(self.dataset_service.get_prepared_dataset_images)

        # Model training routes
        self.blueprint.route('/model/train', methods=['POST'])(self.train_model)
        self.blueprint.route('/model/list', methods=['GET'])(self.list_models)
        self.blueprint.route('/model/select', methods=['POST'])(self.select_model)

    
    def save_annotation(self):
        """Save annotations for an image."""
        try:
            if 'filename' not in request.json:
                return jsonify({"error": "No filename provided"}), 400
            
            if 'annotation' not in request.json:
                return jsonify({"error": "No annotation data provided"}), 400

            result = self.dataset_service.save_annotation(
                request.json['filename'],
                request.json['annotation']
            )
            
            return jsonify({
                "message": "Annotation(s) saved successfully",
                **result
            }), 200
            
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    def get_dataset_images(self):
        """Get all images in the dataset."""
        try:
            result = self.dataset_service.get_dataset_images()
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def prepare_dataset(self):
        """Prepare the dataset for training."""
        try:
            result = self.dataset_service.prepare_dataset()
            return jsonify({
                "message": "Dataset prepared successfully",
                **result    
            }), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def clear_dataset(self):
        """Clear the temporary dataset."""
        try:
            result = self.dataset_service.clear_temp_dataset()
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def train_model(self):
        """Train the model using the prepared dataset."""
        try:
            result = self.model_trainer.train_model()
            return jsonify({
                "message": "Model training completed successfully",
                **result
            }), 200
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def list_models(self):
        """List all available trained models with their metadata."""
        try:
            return jsonify(self.model_trainer.list_models()), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def select_model(self):
        """Select a specific model for inference."""
        try:
            if 'model_name' not in request.json:
                return jsonify({"error": "No model name provided"}), 400

            
            result = self.model_trainer.select_model(request.json['model_name'])
            return jsonify(result), 200
            
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
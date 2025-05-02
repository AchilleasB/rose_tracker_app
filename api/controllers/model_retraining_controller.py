from flask import Blueprint, jsonify, request
import os
import json
from src.services import ModelRetrainerService
from config.settings import Settings
import logging

class ModelRetrainingController:
    def __init__(self):
        self.settings = Settings()
        self.blueprint = Blueprint('retrain_model', __name__)
        self.model_retrainer = ModelRetrainerService()
        self._register_routes()

    def _register_routes(self):
        self.blueprint.route('/save-annotation', methods=['POST'])(self.save_annotation)
        self.blueprint.route('/retrain-model', methods=['POST'])(self.retrain_model)
        self.blueprint.route('/models', methods=['GET'])(self.list_models)
        self.blueprint.route('/models/select', methods=['POST'])(self.select_model)

    def save_annotation(self):
        try:
            if 'original_image_path' not in request.json:
                return jsonify({"error": "No original image path provided"}), 400
            
            if 'annotation' not in request.json:
                return jsonify({"error": "No annotation data provided"}), 400

            result = self.model_retrainer.save_annotation(
                request.json['original_image_path'],
                request.json['annotation']
            )
            
            logging.debug(f"save_annotation called with original_image_path={request.json.get('original_image_path')}, annotation keys={list(request.json.get('annotation', {}).keys()) if isinstance(request.json.get('annotation'), dict) else type(request.json.get('annotation'))}")
            
            return jsonify({
                "message": "Annotation saved successfully",
                **result
            }), 200
            
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def retrain_model(self):
        try:
            result = self.model_retrainer.retrain_model()
            return jsonify({
                "message": "Model retraining completed successfully",
                **result
            }), 200
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def list_models(self):
        """List all available retrained models with their metadata"""
        try:
            return jsonify(self.model_retrainer.list_models()), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def select_model(self):
        """Select a specific model for inference"""
        try:
            if 'model_name' not in request.json:
                return jsonify({"error": "No model name provided"}), 400

            model_path = self.model_retrainer.get_model_path(request.json['model_name'])
            return jsonify({
                "message": f"Model {request.json['model_name']} selected successfully",
                "model_path": model_path
            }), 200
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500 
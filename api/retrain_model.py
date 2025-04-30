from flask import Blueprint, jsonify, request
import os
import shutil
from datetime import datetime
from ultralytics import YOLO
import json
from src.services.model_retrainer import ModelRetrainerService
from config.settings import Settings

settings = Settings()
retrain_bp = Blueprint('retrain_model', __name__)
model_retrainer = ModelRetrainerService()

@retrain_bp.route('/save-annotation', methods=['POST'])
def save_annotation():
    try:
        if 'original_image_path' not in request.json:
            return jsonify({"error": "No original image path provided"}), 400
        
        if 'annotation' not in request.json:
            return jsonify({"error": "No annotation data provided"}), 400

        result = model_retrainer.save_annotation(
            request.json['original_image_path'],
            request.json['annotation']
        )
        
        return jsonify({
            "message": "Annotation saved successfully",
            **result
        }), 200
        
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@retrain_bp.route('/retrain-model', methods=['POST'])
def retrain_model():
    try:
        result = model_retrainer.retrain_model()
        return jsonify({
            "message": "Model retraining completed successfully",
            **result
        }), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@retrain_bp.route('/models', methods=['GET'])
def list_models():
    """List all available retrained models with their metadata"""
    try:
        return jsonify(model_retrainer.list_models()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@retrain_bp.route('/models/select', methods=['POST'])
def select_model():
    """Select a specific model for inference"""
    try:
        if 'model_name' not in request.json:
            return jsonify({"error": "No model name provided"}), 400

        model_path = model_retrainer.get_model_path(request.json['model_name'])
        return jsonify({
            "message": f"Model {request.json['model_name']} selected successfully",
            "model_path": model_path
        }), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def load_model_metadata():
    """Load model metadata from JSON file"""
    if os.path.exists(settings.MODEL_METADATA_FILE):
        with open(settings.MODEL_METADATA_FILE, 'r') as f:
            return json.load(f)
    return {"models": []}

def save_model_metadata(metadata):
    """Save model metadata to JSON file"""
    with open(settings.MODEL_METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)
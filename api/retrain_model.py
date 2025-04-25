from flask import Blueprint, jsonify
import os

retrain_model = Blueprint('realtime_tracking', __name__)
model = 'data/best.pt'
tracker_path = 'config/modified_botsort.yaml'

# POST endpoint for retraining the model
@retrain_model.route('/retrain-model', methods=['POST'])
def retrain_model():
    # Trigger retraining (e.g., call a script to train YOLO on the custom dataset)
    os.system("python train.py --data custom_dataset.yaml --weights {model} --epochs 10")
    return jsonify({"message": "Model retraining started."}), 200

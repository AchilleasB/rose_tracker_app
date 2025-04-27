"""
YOLO-BoTSORT Integration Module

This module handles the integration with YOLO-BoTSORT tracking system.
It provides functionality to download, modify, and configure the BoTSORT
tracker for rose detection and tracking purposes.

The module ensures that the tracking system is properly configured
for the specific requirements of rose tracking, including:
- Custom confidence thresholds
- Specialized tracking parameters
- Rose-specific detection optimization
"""

import requests
import os
from config.settings import settings

def download_and_modify_botsort():
    """Download and configure the YOLO-BoTSORT tracker."""
    output_path = 'config/modified_botsort.yaml'

    if os.path.exists(output_path):
        print(f"{output_path} already exists. Skipping download and modification.")
        return

    try:
        botsort_yaml = download_botsort(settings.BOTSORT_CONFIG_URL)
        modify_botsort(botsort_yaml, output_path)
    except Exception as e:
        print(f"Error in download_and_modify_botsort: {str(e)}")
        raise


def download_botsort(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to download file. Status code: {response.status_code}")
    
def modify_botsort(botsort_yaml, output_path):
    modifications = {
        "match_thresh: 0.8": "match_thresh: 0.9",
        "track_buffer: 30": "track_buffer: 50",
        "new_track_thresh: 0.25": "new_track_thresh: 0.75",
        "track_high_thresh: 0.25": f"track_high_thresh: 0.6",
        "track_low_thresh: 0.1": "track_low_thresh: 0.2"
    }
    # Update values programmatically
    updated_yaml = botsort_yaml
    for old_value, new_value in modifications.items():
        updated_yaml = updated_yaml.replace(old_value, new_value)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding='utf-8') as file:
        file.write(updated_yaml)

    print("Updated botsort.yaml applied.")
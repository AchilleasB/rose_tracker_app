import requests
import configparser
import os

def get_botsort_url(config_path='config/config.ini'):
    config = configparser.ConfigParser()
    config.read(config_path)
    url = config.get('botsort', 'url', fallback=None)
    if not url:
        raise ValueError("BOTSORT_URL not found in the config.ini file.")
    return url

def download_botsort(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to download file. Status code: {response.status_code}")
    
def modify_botsort(botsort_yaml, output_path='config/modified_botsort.yaml'):
    # Update values programmatically
    updated_yaml = botsort_yaml.replace("match_thresh: 0.8", "match_thresh: 0.93") \
                               .replace("track_buffer: 30", "track_buffer: 50") \
                               .replace("new_track_thresh: 0.25", "new_track_thresh: 0.75") \
                               .replace("track_high_thresh: 0.25", "track_high_thresh: 0.6") \
                               .replace("track_low_thresh: 0.1", "track_low_thresh: 0.2")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding='utf-8') as file:
        file.write(updated_yaml)

    print("Updated botsort.yaml applied.")


def download_and_modify_botsort(config_path='config/config.ini', output_path='config/modified_botsort.yaml'):
    # Check if the modified botsort.yaml file already exists
    if os.path.exists(output_path):
        print(f"{output_path} already exists. Skipping download and modification.")
        return

    url = get_botsort_url(config_path)
    botsort_yaml = download_botsort(url)
    modify_botsort(botsort_yaml, output_path)
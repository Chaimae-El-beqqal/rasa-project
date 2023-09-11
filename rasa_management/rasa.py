# rasa_management/rasa_management.py
import os

import requests
from flask import jsonify


def send_yaml(max_data_size):
    try:
        # Check the size of the output YAML file
        yaml_file_size = os.path.getsize('output.yml')

        if yaml_file_size > max_data_size:
            return jsonify({"error": "File size exceeds 1MB, please check your training data"}), 400
        url = 'http://localhost:5005/model/train?save_to_default_model_directory=true&force_training=false&augmentation=50&num_threads=1&token'  # API endpoint
        headers = {
            'Content-Type': 'application/x-yaml'  # content type
        }

        # Read YAML content from file
        with open('output.yml', 'r', encoding='utf-8') as yaml_file:
            yaml_data = yaml_file.read()
        # Encode YAML data in UTF-8
        yaml_data_encoded = yaml_data.encode('utf-8')
        # Make the POST request with YAML data
        response = requests.post(url, data=yaml_data_encoded, headers=headers)
        # Check response status and return result
        if response.status_code == 200:
            head = response.headers
            # print(head.get('filename'))
            # print()
            global model_path
            model_path = "C:/Users/Lenovo/Downloads/pythonProject/models/" + head.get(
                'filename')  # Send training progress as plain text response
            return jsonify({"message": "Training completed successfully"})
            # return jsonify({"message": "model Trained successfully"})
        else:
            return jsonify({"error": "Request failed"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "An error occurred"})



def send_reload_request_to_rasa():
    try:
        reload_url = 'http://localhost:5005/model'
        headers = {
            'Content-Type': 'application/json'  # content type
        }
        data = {
            "model_file": model_path,

        }

        response = requests.put(reload_url, json=data, headers=headers)

        # Check response status and return result
        if response.status_code == 204:
            print("yes")
            return jsonify({"message": "You can use the trained bot now !"})
        else:
            return jsonify({"error": "Request failed"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "An error occurred"}), 500


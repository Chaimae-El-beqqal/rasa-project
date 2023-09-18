# rasa_management/rasa_management.py
import os
import requests
from flask import jsonify

def send_yaml(max_data_size,model_folder,rasa_train):
    try:
        # Check the size of the output YAML file
        yaml_file_size = os.path.getsize('output.yml')
        max_data_size = int(max_data_size)

        if int(yaml_file_size) > max_data_size:
            return jsonify({"error": "File size exceeds 1MB, please check your training data"}), 400

        headers = {
            'Content-Type': 'application/x-yaml'  # content type
        }

        # Read YAML content from file
        with open('output.yml', 'r', encoding='utf-8') as yaml_file:
            yaml_data = yaml_file.read()
        # Encode YAML data in UTF-8
        yaml_data_encoded = yaml_data.encode('utf-8')
        # Make the POST request with YAML data
        response = requests.post(rasa_train, data=yaml_data_encoded, headers=headers)
        # Check response status and return result
        if response.status_code == 200:
            head = response.headers

            model_path = model_folder + head.get(
                'filename')  # Send training progress as plain text response
            return {"success": "✅ Training completed successfully",
                            "model_path":model_path,
                             "status_code":200}

        else:
            return jsonify({"error": "Request failed"}), response.status_code

    except (OSError, IOError) as e:
        return jsonify({"error": "An error occurred while accessing the YAML file"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "An error occurred during the POST request"}), 500

def send_reload_request_to_rasa(rasa_relod,trained_model_path):
    try:
        reload_url = rasa_relod
        headers = {
            'Content-Type': 'application/json'  # content type
        }
        data = {
            "model_file": trained_model_path,
        }

        response = requests.put(reload_url, json=data, headers=headers)
        # Check response status and return result
        if response.status_code == 204:

            return jsonify({"success": "✅ You can use the trained bot now !"})
        else:
            return jsonify({"error": "Request failed"}), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "An error occurred during the PUT request"}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500

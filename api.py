from flask import Flask, render_template, request, jsonify, Response
import os

from flask_cors import CORS

from data_preprocessing.data_preprocessing import generate_rasa_training_data, append_uploaded_data_to_existing_file
from rasa_management.rasa import send_yaml, send_reload_request_to_rasa
from decouple import config

app = Flask(__name__)
CORS(app)

# == VARIABLES ==============
# Access DEBUG variable
debug_mode = config('DEBUG', default=False, cast=bool)
output_folder = config('output_folder')  # Specify the folder name of domain file
RASA_API_URL = config('RASA_API_URL')  # Rasa API URL
model_path = config('model_path')
data_folder = config('data_folder')
output_yaml_path = config('output_yaml_path')


@app.route('/')
def index():
    return render_template('home.html')

# === upload the data files : NLU , STORIES , RULES ===================
@app.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist("files[]")
    filenames = ['nlu.csv', 'stories.csv', 'rules.csv', 'responses.csv']
    type = request.headers.get('Custom-Info')
    # Create the 'uploads' directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    for file, filename in zip(uploaded_files, filenames):
        file.save(os.path.join('uploads', filename))
    if type == "new":
        generate_rasa_training_data(60, output_yaml_path)
    elif type == "add":
        append_uploaded_data_to_existing_file(60, output_yaml_path)
    with open('output.yml', 'r', encoding='utf-8') as yaml_file:
        yaml_data = yaml_file.read()
        # print(yaml_data)
    response = ""
    if type == "new":
        response = {"message": "Files uploaded and Rasa training data generated successfully!"}
    elif type == "add":
        response = {"message": "Data added successfully!"}

    return jsonify(response)

@app.route('/train', methods=['POST'])
def train():
    # Call the send_yaml function from the rasa_management module
    return send_yaml()


@app.route('/reload', methods=['POST'])
def reload():
    return send_reload_request_to_rasa()


if __name__ == '__main__':
    app.static_folder = 'static'
    app.run(host='0.0.0.0', port=5000)

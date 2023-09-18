from flask import Flask, render_template, request, jsonify
import os
from flask_cors import CORS

from services.data_management.data_preprocessing import generate_rasa_training_data, append_uploaded_data_to_existing_file
from services.rasa_management.rasa import send_yaml, send_reload_request_to_rasa
from decouple import config

app = Flask(__name__)
CORS(app)

# == VARIABLES ==============
# Access DEBUG variable
debug_mode = config('DEBUG', default=False, cast=bool)
output_folder = config('output_folder')  # Specify the folder name of domain file

model_path = config('model_path')
data_folder = config('data_folder')
output_yaml_path = config('output_yaml_path')
max_data_size = 1*1024*1024

MAX_FILE_SIZE_BYTES = 500 * 1024  # 0.5MB
train_response =''
# RASA ENDPOINTS ========================
model_folder = config('MODEL_FOLDER')
rasa_api = config('RASA_API')  # Rasa API
rasa_train = config('RASA_TRAIN')  # Rasa training
rasa_reload = config('RASA_RELOAD')  # Rasa reloading


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
        file_contents = file.read()

        # Check if the file is empty
        if len(file_contents) == 0:
            if type == "new":
                return jsonify({"error": f"{filename} file is required"}), 400
            elif type == "add":
                file.save(os.path.join('uploads', filename))
                continue  # allow empty files when adding data

        # Check if the file size is within the limit
        if len(file_contents) <= MAX_FILE_SIZE_BYTES:
            file.seek(0)  # Reset the file pointer to the beginning
            file.save(os.path.join('uploads', filename))
        else:

            return jsonify({"error": f"File size for {filename} exceeds the maximum allowed (500KB)."}), 400

    response = {}
    # try:
    if type == "new":
        rapport = generate_rasa_training_data(60, output_yaml_path)
        msg = "✅ Files uploaded and Rasa training data generated successfully!"
        if rapport.get('missing columns'):
            msg = '🟡 Please check missing columns'
            response = {"warning": msg,
                        "rapport": rapport}
        else:
            response = {"success": msg,
                        "rapport": rapport}
    elif type == "add":
        rapport = append_uploaded_data_to_existing_file(60, output_yaml_path)
        response = {"success": "✅ Data added successfully!",
                        "rapport": rapport}
    print(rapport)
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

    return jsonify(response)


@app.route('/train', methods=['POST'])
def train():
    # Call the send_yaml function from the rasa_management module
    train_response = send_yaml(max_data_size,model_folder,rasa_train)

    # Check if train_response is a tuple and its first element is a Response object
    if train_response["status_code"] == 200:
        print(train_response['model_path'])
        global  trained_model_path
        trained_model_path = train_response['model_path']
    else:
        print("Invalid train_response format")

    return train_response

@app.route('/reload', methods=['POST'])
def reload():
    print(trained_model_path)
    if(trained_model_path):
        return send_reload_request_to_rasa(rasa_reload,trained_model_path)
    else:
        return jsonify({'error':'please check the model path'})

if __name__ == '__main__':
    app.static_folder = 'static'
    app.run(host='0.0.0.0', port=5000)

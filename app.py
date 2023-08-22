from flask import Flask, render_template, request, jsonify
import csv
import os
import subprocess
from flask_cors import CORS

app = Flask(__name__)
data_folder = "data"  # the folder name to replace training data in the data folder
output_folder = ""  # Specify the folder name of domain file
RASA_API_URL = "http://localhost:5005"  # Rasa API URL
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')


# ======================================= upload the data files : NLU , STORIES , RULES ===================
@app.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist("files[]")
    filenames = ['nlu.csv', 'stories.csv', 'rules.csv']

    for file, filename in zip(uploaded_files, filenames):
        file.save(os.path.join('uploads', filename))

    generate_rasa_training_data()
    response = {"message": "Files uploaded and Rasa training data generated successfully!"}
    return jsonify(response)
    # data_res = "Files uploaded and Rasa training data generated successfully!"
    # return render_template('index.html',data_res)


def save_to_file(data, filename):
    with open(os.path.join(data_folder, filename), 'w') as output_file:
        output_file.write(data)


# ---------------------------------------- generate the data files -----------------------------------------
def generate_rasa_training_data():
    uploaded_files = os.listdir('uploads')
    nlu_data = ""
    stories_data = ""
    rules_data = ""

    for filename in uploaded_files:
        csv_filename = os.path.join('uploads', filename)
        if os.path.exists(csv_filename):
            with open(csv_filename, 'r', encoding='utf-8-sig') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                if filename == 'nlu.csv':
                    nlu_data += "version: '3.1'\nnlu:\n"
                    for row in csv_reader:
                        intent = row['intent']
                        examples = row['examples'].split(',')
                        nlu_data += f"- intent: {intent}\n"
                        nlu_data += "  examples: |\n"
                        for example in examples:
                            nlu_data += f"    - {example}\n"

                elif filename == 'stories.csv':
                    stories_data += "version: '3.1'\nstories:\n"
                    for row in csv_reader:
                        story = row['story']
                        steps = row['steps'].split(',')
                        stories_data += f"- story: {story}\n"
                        stories_data += "  steps:\n"
                        for i in range(0, len(steps), 2):
                            element = steps[i].strip()
                            if element.startswith("utter"):
                                action = element
                                intent = None
                            else:
                                intent = element
                                action = steps[i + 1].strip() if i + 1 < len(steps) else None
                            if intent:
                                stories_data += f"  - intent: {intent}\n"
                            if action:
                                stories_data += f"  - action: {action}\n"

                elif filename == 'rules.csv':
                    rules_data += "version: '3.1'\nrules:\n"
                    for row in csv_reader:
                        rule = row['rule']
                        steps = row['steps'].split(',')
                        rules_data += f"- rule: {rule}\n"
                        rules_data += "  steps:\n"
                        for i in range(0, len(steps), 2):
                            element = steps[i].strip()
                            if element.startswith("utter"):
                                action = element
                                intent = None
                            else:
                                intent = element
                                action = steps[i + 1].strip() if i + 1 < len(steps) else None
                            if intent:
                                rules_data += f"  - intent: {intent}\n"
                            if action:
                                rules_data += f"  - action: {action}\n"

    clear_data_folder()

    os.makedirs(data_folder, exist_ok=True)
    save_to_file(nlu_data, 'nlu.yml')
    save_to_file(stories_data, 'stories.yml')
    save_to_file(rules_data, 'rules.yml')


def clear_data_folder():
    for file_name in os.listdir(data_folder):
        file_path = os.path.join(data_folder, file_name)
        # print(file_path)
        if os.path.isfile(file_path):
            os.remove(file_path)


# ==================================================== generate domain file ========================================
@app.route('/generate_domain', methods=['POST'])
def generate_domain():
    uploaded_files = request.files.getlist("files[]")
    expiration_time = request.form.get("expiration_time")

    nlu_data = get_nlu_data()
    for file in uploaded_files:
        file.save(os.path.join('uploads', file.filename))

    generate_domain_file(uploaded_files, nlu_data, expiration_time)

    response = {"message": "Domain file generated successfully!"}
    return jsonify(response)

def get_nlu_data():
    nlu_intents = []

    # Read the existing NLU CSV file and extract intent names
    nlu_csv_path = os.path.join('uploads', 'nlu.csv')
    if os.path.exists(nlu_csv_path):
        with open(nlu_csv_path, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                intent_name = row['intent'].strip()
                if intent_name:
                    nlu_intents.append(intent_name)

    return nlu_intents


def generate_domain_file(response_files, nlu_data, expiration_time):
    domain_content = "version: '3.1'\n"

    # Generate intents section using NLU data
    domain_content += "intents:\n"
    for intent in nlu_data:
        domain_content += f"- {intent}\n"

    # Generate responses section
    domain_content += "\nresponses:\n"
    for response_file in response_files:
        with open(os.path.join('uploads', response_file.filename), 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            # print(csv_reader)
            for row in csv_reader:
                # print(row)
                utter_name = row['utter_name']
                response_text = row['text']
                domain_content += f"  {utter_name}:\n"
                domain_content += f"  - text: \"{response_text}\"\n"

    # Add session config
    domain_content += "\nsession_config:\n"
    domain_content += f"  session_expiration_time: {expiration_time}\n"
    domain_content += "  carry_over_slots_to_new_session: true\n"

    save_to_file(domain_content, 'domain.yml')


def save_to_file(data, filename):
    if filename == 'domain.yml':
        output_folder = ""
    else:
        output_folder = "data"
    with open(os.path.join(output_folder, filename), 'w') as output_file:
        output_file.write(data)


# ================================================= TRAIN THE MODEL =====================================
@app.route('/model/train', methods=['POST'])
def train_rasa_model():
    try:
        # Run the Rasa training command
        subprocess.run(['rasa', 'train'])

        response = {"message": "Model trained successfully"}
        return jsonify(response)
    except Exception as e:
        err_res = str(e) +" 500"
        # return render_template('index.html',err_res )



if __name__ == '__main__':
    app.static_folder = 'static'
    app.run(host='0.0.0.0', port=5000)

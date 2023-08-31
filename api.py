from flask import Flask, render_template, request, jsonify, Response
import csv
import os

from flask_cors import CORS
import requests

app = Flask(__name__)
data_folder = "data"  # the folder name to replace training data in the data folder
output_folder = ""  # Specify the folder name of domain file
RASA_API_URL = "http://localhost:5005"  # Rasa API URL
CORS(app)
model_path = ""


@app.route('/')
def index():
    return render_template('home.html')


# Modify these paths accordingly
data_folder = ""
output_yaml_path = os.path.join(data_folder, "output.yml")


# Append section content to output YAML
def append_section_to_yaml(section_content):
    with open(output_yaml_path, 'a', encoding='utf-8') as output_file:
        output_file.write(section_content)
        output_file.write("\n")  # Add a newline after each section


config = '''assistant_id: default_config_bot
language: "fr"  

pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: "char_wb"
    min_ngram: 1
    max_ngram: 4
  - name: DIETClassifier
    epochs: 100
  - name: EntitySynonymMapper
  - name: ResponseSelector
    epochs: 100

policies:
- name: MemoizationPolicy
- name: TEDPolicy
  max_history: 5
  epochs: 10
- name: RulePolicy
'''


# ======================================= upload the data files : NLU , STORIES , RULES ===================
@app.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist("files[]")
    filenames = ['nlu.csv', 'stories.csv', 'rules.csv', 'responses.csv']
    expiration_time = request.form.get("expiration_time")
    for file, filename in zip(uploaded_files, filenames):
        file.save(os.path.join('uploads', filename))

    generate_rasa_training_data(expiration_time)
    with open('output.yml', 'r', encoding='utf-8') as yaml_file:
        yaml_data = yaml_file.read()
        print(yaml_data)

    response = {"message": "Files uploaded and Rasa training data generated successfully!"}
    return jsonify(response)
    # data_res = "Files uploaded and Rasa training data generated successfully!"
    # return render_template('index.html',data_res)


# ---------------------------------------- generate the data files -----------------------------------------
def generate_rasa_training_data(expiration_time):
    uploaded_files = os.listdir('uploads')
    nlu_data = "nlu:\n"
    stories_data = "stories:\n"
    rules_data = "rules:\n"
    nlu_intents = []

    domain_content = ""

    for filename in uploaded_files:
        csv_filename = os.path.join('uploads', filename)
        if os.path.exists(csv_filename):
            with open(csv_filename, 'r', encoding='utf-8-sig') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                if filename == 'nlu.csv':
                    for row in csv_reader:
                        intent_name = row['intent'].strip()
                        if intent_name:
                            nlu_intents.append(intent_name)
                        intent = row['intent']
                        examples = row['examples'].split(',')
                        nlu_data += f"- intent: {intent}\n"
                        nlu_data += "  examples: |\n"

                        for example in examples:
                            nlu_data += f"    - {example}\n"

                elif filename == 'stories.csv':
                    current_story_actions = []
                    for row in csv_reader:
                        story = row['story']
                        steps = row['steps'].split(',')

                        current_story_actions = []  # Reset for each new story
                        for i in range(0, len(steps)):
                            element = steps[i].strip()
                            if element.startswith("utter"):
                                current_story_actions.append(element)
                            else:
                                intent = element
                                current_story_actions.append(intent)
                                # action = steps[i + 1].strip() if i + 1 < len(steps) else None

                        stories_data += f"- story: {story}\n"
                        stories_data += "  steps:\n"
                        for action in current_story_actions:
                            if action.startswith("utter"):
                                stories_data += f"  - action: {action}\n"
                            else:
                                stories_data += f"  - intent: {action}\n"

                elif filename == 'rules.csv':
                    for row in csv_reader:
                        rule = row['rule']
                        steps = row['steps'].split(',')
                        rules_data += f"- rule: {rule}\n"
                        rules_data += "  steps:\n"
                        for i in range(0, len(steps)):
                            element = steps[i].strip()
                            if element.startswith("utter"):
                                rules_data += f"  - action: {element}\n"

                            else:
                                rules_data += f"  - intent: {element}\n"


                elif filename == 'responses.csv':
                    domain_content += "intents:\n"
                    for intent in nlu_intents:
                        domain_content += f"- {intent}\n"
                    domain_content += "\nresponses:\n"
                    for row in csv_reader:
                        utter_name = row['utter_name']
                        response_text = row['text']
                        domain_content += f"  {utter_name}:\n"
                        domain_content += f"  - text: \"{response_text}\"\n"

    domain_content += "\nsession_config:\n"
    domain_content += f"  session_expiration_time: {expiration_time}\n"
    domain_content += "  carry_over_slots_to_new_session: true\n"

    if os.path.exists(output_yaml_path):
        os.remove(output_yaml_path)

    append_section_to_yaml(config)
    append_section_to_yaml(domain_content)
    append_section_to_yaml(nlu_data)
    append_section_to_yaml(stories_data)
    append_section_to_yaml(rules_data)


@app.route('/train', methods=['POST'])
def send_yaml():
    try:
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
            print(head.get('filename'))
            # print()
            global model_path
            model_path = "C:/Users/Lenovo/Downloads/pythonProject/models/" + head.get(
                'filename')  # Send training progress as plain text response
            return jsonify({"message": "Training completed successfully"})
            # return jsonify({"message": "model Trained successfully"})
        else:
            return jsonify({"error": "Request failed"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "An error occurred"}), response.status_code


@app.route('/reload', methods=['POST'])
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


if __name__ == '__main__':
    app.static_folder = 'static'
    app.run(host='0.0.0.0', port=5000)

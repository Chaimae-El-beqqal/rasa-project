import yaml
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
    type = request.headers.get('Custom-Info')
    # Create the 'uploads' directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    for file, filename in zip(uploaded_files, filenames):
        file.save(os.path.join('uploads', filename))
    if type == "new":
        generate_rasa_training_data(60)
    elif type =="add":
        append_uploaded_data_to_existing_file(60, output_yaml_path)
    with open('output.yml', 'r', encoding='utf-8') as yaml_file:
        yaml_data = yaml_file.read()
        # print(yaml_data)
    response =""
    if type == "new":
        response = {"message": "Files uploaded and Rasa training data generated successfully!"}
    elif type =="add":
        response = {"message": "Data added successfully!"}

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
                        # ============== this is for appending intents names in domain part  ==========================
                        if intent_name:
                            # ------------- to check retrieval intents ----------
                            if "/" in intent_name :
                                name = intent_name.split("/")
                                if not name[0] in nlu_intents:
                                    nlu_intents.append(name[0])
                            else :
                                nlu_intents.append(intent_name)
                        # =========         end of domain part  ========================================================
                        intent = row['intent']
                        examples = row['examples'].split(';')
                        nlu_data += f"- intent: {intent}\n"
                        nlu_data += "  examples: |\n"

                        for example in examples:
                            # print("hello exp", example, "\n")
                            nlu_data += f"    - {example}\n"
                    nlu_data+= "# NLU DATA PLACEHOLDER\n"

                elif filename == 'stories.csv':
                    for row in csv_reader:
                        story = row['story']
                        steps = row['steps'].split(';')

                        stories_data += f"- story: {story}\n"
                        stories_data += "  steps:\n"
                        for elt in steps:
                            if elt.startswith("utter"):
                                stories_data += f"  - action: {elt}\n"
                            else:
                                stories_data += f"  - intent: {elt}\n"
                    stories_data+= "# STORIES DATA PLACEHOLDER\n"

                elif filename == 'rules.csv':
                    for row in csv_reader:
                        rule = row['rule']
                        steps = row['steps'].split(';')
                        rules_data += f"- rule: {rule}\n"
                        rules_data += "  steps:\n"
                        for i in range(0, len(steps)):
                            element = steps[i].strip()
                            if element.startswith("utter"):
                                rules_data += f"  - action: {element}\n"
                            else:
                                rules_data += f"  - intent: {element}\n"
                    rules_data+="# RULES DATA PLACEHOLDER\n"

                elif filename == 'responses.csv':
                    domain_content += "intents:\n"
                    for intent in nlu_intents:
                        domain_content += f"- {intent}\n"
                    domain_content += "# INTENTS DATA PLACEHOLDER\n"
                    domain_content += "\nresponses:\n"
                    for row in csv_reader:
                        # =========== handle response name =================

                        utter_name = row['utter_name']
                        domain_content += f"  {utter_name}:\n"

                        # =========== handle response texts =================
                        text = row['text'].split(';')
                        for i in range(0, len(text)):
                            element = text[i].strip()
                            domain_content += f"  - text: \"{element}\"\n"

                        # =========== handle response buttons =================
                        if row['buttons']:
                            domain_content += f"    buttons: \n"
                            btns = row['buttons'].split(';')
                            # print(btns)
                            for i in range(0, len(btns), 2):
                                # print(btns[i], i)
                                domain_content += f"    - title: \"{btns[i]}\"\n"
                                domain_content += f"      payload: \"{btns[i + 1]}\"\n"

                        # =========== handle response imgs =================
                        if row['images']:
                            img = row['images']
                            domain_content += f"    image: \"{img}\"\n"
                    domain_content+= "# DOMAIN DATA PLACEHOLDER\n"
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

# ---------------------------------------- update the data files -----------------------------------------

def append_uploaded_data_to_existing_file(expiration_time, output_yaml_path):
    uploaded_files = os.listdir('uploads')
    nlu_data = ""
    stories_data = ""
    rules_data = ""
    nlu_intents = []
    intents =""
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
                            if "/" in intent_name:
                                name = intent_name.split("/")
                                if not name[0] in nlu_intents:
                                    nlu_intents.append(name[0])
                                    print(name[0])
                            else:
                                nlu_intents.append(intent_name)

                        intent = row['intent']
                        examples = row['examples'].split(';')
                        nlu_data += f"- intent: {intent}\n"
                        nlu_data += "  examples: |\n"

                        for example in examples:
                            nlu_data += f"    - {example}\n"
                    nlu_data+= "# NLU DATA PLACEHOLDER\n"

                elif filename == 'stories.csv':
                    for row in csv_reader:
                        story = row['story']
                        steps = row['steps'].split(';')

                        stories_data += f"- story: {story}\n"
                        stories_data += "  steps:\n"
                        for elt in steps:
                            if elt.startswith("utter"):
                                stories_data += f"  - action: {elt}\n"
                            else:
                                stories_data += f"  - intent: {elt}\n"
                    stories_data+= "# STORIES DATA PLACEHOLDER\n"

                elif filename == 'rules.csv':
                    for row in csv_reader:
                        rule = row['rule']
                        steps = row['steps'].split(';')
                        rules_data += f"- rule: {rule}\n"
                        rules_data += "  steps:\n"
                        for i in range(0, len(steps)):
                            element = steps[i].strip()
                            if element.startswith("utter"):
                                rules_data += f"  - action: {element}\n"
                            else:
                                rules_data += f"  - intent: {element}\n"
                    rules_data+= "# RULES DATA PLACEHOLDER\n"

                elif filename == 'responses.csv':

                    for row in csv_reader:
                        utter_name = row['utter_name']
                        domain_content += f"  {utter_name}:\n"

                        text = row['text'].split(';')
                        for i in range(0, len(text)):
                            element = text[i].strip()
                            domain_content += f"  - text: \"{element}\"\n"

                        if row['buttons']:
                            domain_content += f"    buttons: \n"
                            btns = row['buttons'].split(';')
                            for i in range(0, len(btns), 2):
                                domain_content += f"    - title: \"{btns[i]}\"\n"
                                domain_content += f"      payload: \"{btns[i + 1]}\"\n"

                        if row['images']:
                            img = row['images']
                            domain_content += f"    image: \"{img}\"\n"
                    domain_content += "# DOMAIN DATA PLACEHOLDER\n"    

    # Read the existing YAML file
    with open(output_yaml_path, 'r', encoding='utf-8') as existing_yaml_file:
        existing_yaml_data = existing_yaml_file.read()
    # ============== TO ADD INTENTS NAME
    if "intents:" in existing_yaml_data:
        for intent in nlu_intents:
            if f"- {intent}" not in existing_yaml_data:
                intents += f"- {intent}\n"
        intents += "# INTENTS DATA PLACEHOLDER\n"
    # Replace the placeholders in the existing file with the new data
    updated_yaml_data = existing_yaml_data.replace("# NLU DATA PLACEHOLDER", nlu_data)
    updated_yaml_data = updated_yaml_data.replace("# STORIES DATA PLACEHOLDER", stories_data)
    updated_yaml_data = updated_yaml_data.replace("# RULES DATA PLACEHOLDER", rules_data)
    updated_yaml_data = updated_yaml_data.replace("# DOMAIN DATA PLACEHOLDER", domain_content)
    updated_yaml_data = updated_yaml_data.replace("# INTENTS DATA PLACEHOLDER", intents)

    # Write the updated data back to the YAML file
    with open(output_yaml_path, 'w', encoding='utf-8') as updated_yaml_file:
        updated_yaml_file.write(updated_yaml_data)
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



# Append section content to output YAML
def append_section_to_yaml(section_content):
    with open(output_yaml_path, 'a', encoding='utf-8') as output_file:
        output_file.write(section_content)
        output_file.write("\n")  # Add a newline after each section

def get_section_from_yaml(yaml_file_path, section_name):
    with open(yaml_file_path, 'r', encoding='utf-8') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    return yaml_data.get(section_name)

def convert(data_dict):
    return yaml.dump(data_dict, default_flow_style=False)


if __name__ == '__main__':
    app.static_folder = 'static'
    app.run(host='0.0.0.0', port=5000)

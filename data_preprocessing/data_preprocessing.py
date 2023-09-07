# data_processing/data_processing.py
import os
import csv
import data_preprocessing.helpers as hl

# --------- this var is for rasa pipline, policies -----
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


def append_section_to_yaml(section_content, output_yaml_path):
    with open(output_yaml_path, 'a', encoding='utf-8') as output_file:
        output_file.write(section_content)
        output_file.write("\n")  # Add a newline after each section


def generate_rasa_training_data(expiration_time, output_yaml_path):
    uploaded_files = os.listdir('uploads')
    nlu_data = ""
    stories_data = ""
    rules_data = ""
    intents = ""
    domain_content = ""

    for filename in uploaded_files:
        csv_filename = os.path.join('uploads', filename)

        if os.path.exists(csv_filename):

            with open(csv_filename, 'r', encoding='utf-8-sig') as csv_file:
                csv_reader = csv.DictReader(csv_file)

                # ======== NLU && INTENTS ==========
                if filename == 'nlu.csv':
                    nlu_data, nlu_intents = hl.generate_nlu(csv_reader, 'new')
                    intents = hl.generate_intents_names(nlu_intents, 'new')
                # ======== STORIES ==========
                elif filename == 'stories.csv':
                    stories_data = hl.generate_stories(csv_reader, 'new')

                # ======== RULES ==========
                elif filename == 'rules.csv':
                    rules_data = hl.generate_rules(csv_reader, 'new')

                # ======== RESPONSES ==========
                elif filename == 'responses.csv':
                    domain_content = hl.generate_responses(csv_reader, 'new')

    domain_content += "\nsession_config:\n"
    domain_content += f"  session_expiration_time: {expiration_time}\n"
    domain_content += "  carry_over_slots_to_new_session: true\n"

    if os.path.exists(output_yaml_path):
        os.remove(output_yaml_path)

    append_section_to_yaml(config, output_yaml_path)
    append_section_to_yaml(intents, output_yaml_path)
    append_section_to_yaml(domain_content, output_yaml_path)
    append_section_to_yaml(nlu_data, output_yaml_path)
    append_section_to_yaml(stories_data, output_yaml_path)
    append_section_to_yaml(rules_data, output_yaml_path)
def append_uploaded_data_to_existing_file(expiration_time, output_yaml_path):

    uploaded_files = os.listdir('uploads')
    intents = ""
    changed_parts = {}
    # Read the existing YAML file
    with open(output_yaml_path, 'r', encoding='utf-8') as existing_yaml_file:
        existing_yaml_data = existing_yaml_file.read()

    for filename in uploaded_files:
        csv_filename = os.path.join('uploads', filename)
        if os.path.exists(csv_filename):
            with open(csv_filename, 'r', encoding='utf-8-sig') as csv_file:
                csv_reader = csv.DictReader(csv_file)

                if filename == 'nlu.csv':
                    nlu_data, nlu_intents = hl.generate_nlu(csv_reader, 'add')
                    # ============== TO ADD INTENTS NAME
                    if "intents:" in existing_yaml_data:
                        for intent in nlu_intents:
                            if f"- {intent}" not in existing_yaml_data:
                                intents += f"- {intent}\n"

                        intents += "# INTENTS DATA PLACEHOLDER\n"

                    changed_parts.update({'NLU':nlu_data})
                    changed_parts.update({'INTENTS':intents})

                # ======== STORIES ==========
                elif filename == 'stories.csv':
                    stories_data = hl.generate_stories(csv_reader, 'add')
                    changed_parts.update({'STORIES':stories_data})

                # ======== RULES ==========
                elif filename == 'rules.csv':
                    rules_data = hl.generate_rules(csv_reader, 'add')
                    changed_parts.update({'RULES':rules_data})

                # ======== RESPONSES ==========
                elif filename == 'responses.csv':
                    domain_content = hl.generate_responses(csv_reader, 'add')
                    changed_parts.update({'DOMAIN':domain_content})


    # Replace the placeholders in the existing file with the new data
    updated_yaml_data = existing_yaml_data
    for key,value in changed_parts.items():
        updated_yaml_data = updated_yaml_data.replace(f"# {key} DATA PLACEHOLDER",value)

    # Write the updated data back to the YAML file
    with open(output_yaml_path, 'w', encoding='utf-8') as updated_yaml_file:
        updated_yaml_file.write(updated_yaml_data)

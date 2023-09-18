# data_processing/data_processing.py
import os
import services.data_management.helpers as hl
import pandas as pd
import services.data_management.checkers as chkr

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

    empty_files = []
    missing_col = []
    missing_data = {}
    duplicated_data = {}

    for filename in uploaded_files:
        csv_filename = os.path.join('uploads', filename)

        if os.path.exists(csv_filename):
            # Check if the CSV file is empty
            if os.path.getsize(csv_filename) == 0:
                print(f"Warning: The file '{filename}' is empty.")
                empty_files.append(filename)
                continue
            # with open(csv_filename, 'r', encoding='utf-8-sig') as csv_file:
            df = pd.read_csv(csv_filename)
            # ======== NLU && INTENTS ==========
            if filename == 'nlu.csv':
                # --- check missing columns
                # print(f"Type before: {type(df)}")
                validate_nlu = chkr.validate_columns(df, ['intent', 'examples'])
                if not validate_nlu:
                    df, missing_nlu, duplicate_nlu = chkr.data_preprocessing(df, 'nlu')
                    # print('missing_nlu: ', missing_nlu, 'duplicate_nlu: ', duplicate_nlu)
                    if len(missing_nlu) >0:
                        print(missing_nlu)
                        missing_data.update({'intents': missing_nlu})
                    if len(duplicate_nlu)>0:
                        print(duplicate_nlu)
                        duplicated_data.update({'intents': duplicate_nlu})
                        # print(duplicated_data)
                    nlu_data, nlu_intents, long_exp = hl.generate_nlu(df, 'new')
                    intents = hl.generate_intents_names(nlu_intents, 'new')
                else:
                    for col in validate_nlu:
                        missing_col.append(col)

            # ======== RESPONSES ==========
            elif filename == 'responses.csv':
                    # --- check missing columns
                    validate_responses = chkr.validate_columns(df, ['utter_name', 'text'])
                    if not validate_responses:
                        df, missing_res, duplicate_res = chkr.data_preprocessing(df, 'responses')
                        domain_content, long_text = hl.generate_responses(df, 'new')
                        if len(missing_res)>0:
                            missing_data.update({'responses': missing_res})
                        if len(duplicate_res)>0:
                            duplicated_data.update({'responses': duplicate_res})
                    else:
                        for col in validate_responses:
                            missing_col.append(col)
            # ======== STORIES ==========
            elif filename == 'stories.csv':
                # --- check missing columns
                validate_stories = chkr.validate_columns(df, ['story', 'steps'])
                if not validate_stories:
                    df, missing_stories, duplicate_stories = chkr.data_preprocessing(df, 'stories')
                    # print('missing_stories:', missing_stories, 'duplicate_stories:', duplicate_stories)
                    if len(missing_stories)>0:
                        missing_data.update({'stories': missing_stories})
                    if len(duplicate_stories)>0:
                        duplicated_data.update({'stories': duplicate_stories})
                    stories_data = hl.generate_stories(df, 'new')
                else:
                    for col in validate_stories:
                        missing_col.append(col)

            # ======== RULES ==========
            elif filename == 'rules.csv':
                # --- check missing columns

                validate_rules = chkr.validate_columns(df, ['rule', 'steps'])
                if not validate_rules:
                    df, missing_rules, duplicate_rules = chkr.data_preprocessing(df, 'rules')
                    # print('missing_rules:', missing_rules, 'duplicate_rules:', duplicate_rules)
                    if len(missing_rules)>0:
                        missing_data.update({'rules': missing_rules})
                    if len(duplicate_rules)>0:
                        duplicated_data.update({'rules': duplicate_rules})
                    rules_data = hl.generate_rules(df, 'new')
                else:
                    for col in validate_rules:
                        missing_col.append(col)



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

    rapport = {}

    if len(missing_col)>0:
        rapport.update({'missing columns':missing_col})
    if len(missing_data)>0:
        rapport.update({'missing data':missing_data})
    if len(duplicated_data)>0:
        rapport.update({'duplicated data':duplicated_data})
    return rapport



def append_uploaded_data_to_existing_file(expiration_time, output_yaml_path):
    uploaded_files = os.listdir('uploads')
    intents = ""
    changed_parts = {}

    missing_col = []
    missing_data = {}
    duplicated_data ={}
    # Read the existing YAML file
    with open(output_yaml_path, 'r', encoding='utf-8') as existing_yaml_file:
        existing_yaml_data = existing_yaml_file.read()

    for filename in uploaded_files:
        csv_filename = os.path.join('uploads', filename)
        if os.path.exists(csv_filename):
            # Check if the CSV file is empty
            if os.path.getsize(csv_filename) == 0:
                print(f"Warning: The file '{filename}' is empty.")

                continue
            with open(csv_filename, 'r', encoding='utf-8-sig') as csv_file:
                df = pd.read_csv(csv_filename)

                if filename == 'nlu.csv':
                    # --- check missing columns

                    validate_nlu = chkr.validate_columns(df, ['intent', 'examples'])
                    if not validate_nlu:
                        df, missing_nlu, duplicate_nlu = chkr.data_preprocessing(df, 'nlu')
                        nlu_data, nlu_intents, long_exp = hl.generate_nlu(df, 'add')
                        # ============== TO ADD INTENTS NAME
                        if "intents:" in existing_yaml_data:
                            for intent in nlu_intents:
                                if f"- {intent}" not in existing_yaml_data:
                                    intents += f"- {intent}\n"

                            intents += "# INTENTS DATA PLACEHOLDER\n"

                        changed_parts.update({'NLU': nlu_data})
                        changed_parts.update({'INTENTS': intents})
                        if len(missing_nlu)>0:
                            missing_data.update({'intents': missing_nlu})
                        if len(duplicate_nlu)>0:
                            duplicated_data.update({'intents': duplicate_nlu})
                    else:
                        for col in validate_nlu:
                            missing_col.append(col)


                # ======== STORIES ==========
                elif filename == 'stories.csv':
                    # --- check missing columns

                    validate_stories = chkr.validate_columns(df, ['story', 'steps'])
                    if not validate_stories:
                        df, missing_stories, duplicate_stories = chkr.data_preprocessing(df, 'stories')
                        stories_data = hl.generate_stories(df, 'add')
                        changed_parts.update({'STORIES': stories_data})
                        if len(missing_stories)>0:
                            missing_data.update({'stories': missing_stories})
                        if len(duplicate_stories)>0:
                            duplicated_data.update({'stories': duplicate_stories})

                    else:
                        for col in validate_stories:
                            missing_col.append(col)

                # ======== RULES ==========
                elif filename == 'rules.csv':
                    # --- check missing columns

                    validate_rules = chkr.validate_columns(df, ['rule', 'steps'])
                    if not validate_rules:
                        df, missing_rules, duplicate_rules = chkr.data_preprocessing(df, 'rules')
                        rules_data = hl.generate_rules(df, 'add')
                        changed_parts.update({'RULES': rules_data})
                        if len(missing_rules)>0:
                            missing_data.update({'rules': missing_rules})
                        if len(duplicate_rules)>0:
                            duplicated_data.update({'rules': duplicate_rules})
                    else:
                        for col in validate_rules:
                            missing_col.append(col)

                # ======== RESPONSES ==========
                elif filename == 'responses.csv':
                    # --- check missing columns

                    validate_responses = chkr.validate_columns(df, ['utter_name', 'text'])
                    if not validate_responses:
                        df, missing_res, duplicate_res = chkr.data_preprocessing(df, 'responses')
                        domain_content, long_text = hl.generate_responses(df, 'add')
                        changed_parts.update({'DOMAIN': domain_content})
                        if len(missing_res)>0:
                            missing_data.update({'responses': missing_res})
                        if len(duplicate_res)>0:
                            duplicated_data.update({'responses': duplicate_res})
                    else:
                        for col in validate_responses:
                            missing_col.append(col)

    # Replace the placeholders in the existing file with the new data
    updated_yaml_data = existing_yaml_data
    for key, value in changed_parts.items():
        updated_yaml_data = updated_yaml_data.replace(f"# {key} DATA PLACEHOLDER", value)

    # Write the updated data back to the YAML file
    with open(output_yaml_path, 'w', encoding='utf-8') as updated_yaml_file:
        updated_yaml_file.write(updated_yaml_data)
    rapport = {}

    if len(missing_col)>0:
        rapport.update({'missing columns': missing_col})
    if len(missing_data)>0:
        rapport.update({'missing data': missing_data})
    if len(duplicated_data)>0:
        rapport.update({'duplicated data': duplicated_data})
    return rapport
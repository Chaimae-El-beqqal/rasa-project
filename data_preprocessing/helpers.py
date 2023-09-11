import pandas as pd


def generate_nlu(df,op_type):
    nlu_intents = []
    nlu_data = ""
    long_exp = 0
    if op_type == 'new':
        nlu_data = "nlu:\n"
    elif op_type == 'add':
        nlu_data = ""
    for i in range(len(df)):
        row = df.iloc[i]
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
            if len(example) > 815:
                long_exp+=1
                continue
            nlu_data += f"    - {example}\n"
    nlu_data += "# NLU DATA PLACEHOLDER\n"
    return nlu_data,nlu_intents,long_exp


def generate_stories(df,op_type):

    stories_data = ""
    if op_type == 'new':
        stories_data = "stories:\n"
    elif op_type == 'add':
        stories_data = ""

    for i in range(len(df)):
        row = df.iloc[i]
        story = row['story']
        steps = row['steps'].split(';')

        stories_data += f"- story: {story}\n"
        stories_data += "  steps:\n"
        for elt in steps:
            if elt.startswith("utter"):
                stories_data += f"  - action: {elt}\n"
            else:
                stories_data += f"  - intent: {elt}\n"
    stories_data += "# STORIES DATA PLACEHOLDER\n"
    return stories_data

def generate_rules(df, op_type):

    rules_data = ""
    if op_type == 'new':
        rules_data = "rules:\n"
    elif op_type == 'add':
        rules_data = ""

    for i in range(len(df)):
        row = df.iloc[i]
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
    rules_data += "# RULES DATA PLACEHOLDER\n"
    return  rules_data

def generate_intents_names(nlu_intents,op_type):

    intents = ""
    if op_type == 'new':
        intents = "intents:\n"
    elif op_type == 'add':
        intents = ""

    for intent in nlu_intents:
        intents += f"- {intent}\n"
    intents += "# INTENTS DATA PLACEHOLDER\n"
    return  intents
def generate_responses(df,op_type):

    long_text = 0
    domain_content = ""
    if op_type == 'new':
        domain_content = "\nresponses:\n"
    elif op_type == 'add':
        domain_content = ""
    print(len(df))
    for i in range(len(df)):
        row = df.iloc[i]
        # print(row)
        # =========== handle response name =================
        utter_name = row['utter_name']
        domain_content += f"  {utter_name}:\n"

        # =========== handle response texts =================
        text = row['text'].split(';')
        for i in range(0, len(text)):
            element = text[i].strip()
            if len(element) > 815:
                long_text+=1
                continue
            domain_content += f"  - text: \"{element}\"\n"

        # =========== handle response buttons =================
        if pd.notna(row['buttons']):
            domain_content += f"    buttons: \n"
            btns = row['buttons'].split(';')
            # print(btns)
            for i in range(0, len(btns), 2):
                # print(btns[i], i)
                domain_content += f"    - title: \"{btns[i]}\"\n"
                domain_content += f"      payload: \"{btns[i + 1]}\"\n"

        # =========== handle response imgs =================
        if pd.notna(row['images']):
            img = row['images']
            domain_content += f"    image: \"{img}\"\n"
    domain_content += "# DOMAIN DATA PLACEHOLDER\n"
    return domain_content,long_text
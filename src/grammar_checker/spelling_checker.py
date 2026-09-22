from spellchecker import SpellChecker

import argparse
import os
import json
import sys
from gpt import spelling_fixer

def write_output(output, output_path):
    if os.path.exists(output_path):
        print(f"Warning: Output file already exists and will be overwritten: {output_path}")
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4)
        print(f"Output successfully saved as JSON: {output_path}")
    except TypeError as e:
        print(f"Output is not JSON serializable: {e}")
        txt_output_path = output_path.replace(".json", ".txt")
        with open(txt_output_path, "w", encoding="utf-8") as f:
            f.write(str(output))
        print(f"Output saved as plain text: {txt_output_path}")


def load_json(json_path):
    if not os.path.exists(json_path):
        print(f"Error: JSON file does not exist: {json_path}")
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"JSON file successfully loaded: {json_path}")
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error loading JSON file: {e}")
        return None



def text_correction(text, language="de"):
    """Corrects the spelling of the input text using the specified language."""
    """Args:
        text (str): The input text to be corrected.
        language (str): The language for spell checking (default is "de" for German).
    Returns:
        dict: A dictionary of misspelled words and their suggested corrections.
        str: The corrected text with suggested corrections applied.
    """
    spell = SpellChecker(language=language)

    misspelled = spell.unknown(text.split())
    corrections = {word: spell.correction(word) for word in misspelled}
    text_corrected = []
    text_words = text.split()
    for word in text_words:
        if word in corrections.keys():
            correction = corrections[word]
            print(f"Misspelled word: '{word}' -> Suggested correction: '{correction}'")
            if correction is not None:
                text_corrected.append(correction)
            else:
                text_corrected.append(word)
        else:
            text_corrected.append(word)
    text_corrected = " ".join(text_corrected)

    return corrections, text_corrected

def clean_text(text):
    """Cleans the input text by removing unwanted characters and normalizing whitespace."""
    if text is None:
        return text
    cleaned_text = text.replace("-\n", "").replace("\n", " ").replace("\r", " ").replace("//", ".").replace(" /", ",").replace("/", ",").strip()

    print(f"Original text: '{text}'")
    return cleaned_text

def spelling_checker_process(input_folder_path, output_folder_path, gpt_information_file):
    gpt_information = load_json(gpt_information_file)
    print(f"GPT information loaded: {gpt_information}")
    for section in os.listdir(input_folder_path):
        input_section_folder_path = os.path.join(input_folder_path, section)
        output_section_folder_path = os.path.join(output_folder_path, section)
        if section == ".DS_Store":
            continue

        for file_name in os.listdir(input_section_folder_path):

            if file_name.endswith(".json"):
                input_file_path = os.path.join(input_section_folder_path, file_name)
                output_file_path = os.path.join(output_section_folder_path, file_name)
                data = load_json(input_file_path)
                text = data['natural_text']
                text = clean_text(text)
                # print(f"Processing file: {text}")
                if text is not None:
                    # corrections, text_corrected = text_correction(text)
                    
                    # corrected_text = spelling_fixer(text, gpt_information)
                    output_data = {
                        "corrections": [],
                        "corrected_text": text,
                        "type":'text'
                    }
                    print(f"Corrected text: {text}")
                    write_output(output_data, output_file_path)
                else:
                    output_data = {
                        "corrections": [],
                        "corrected_text": text,
                        "type":'image'
                    }
                    write_output(output_data, output_file_path)
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Spell checker for text correction.")
    parser.add_argument("--input_folder_path", type=str, default="/Users/sefika/projects/nature_culture_heritage_ontology/results/merian_maria_sybilla", help="Path to the input JSON file containing the text to be corrected.")
    parser.add_argument("--gpt_information_file", type=str, default="/Users/sefika/projects/nature_culture_heritage_ontology/keys/api_token.json", help="Path to the JSON file containing GPT information.")
    parser.add_argument("--output_folder_path", type=str, default="/Users/sefika/projects/nature_culture_heritage_ontology/results/merian_maria_sybilla_corrected", help="Path to save the output JSON file with corrections and corrected text.")
    args = parser.parse_args()
    
    input_folder_path = args.input_folder_path
    output_folder_path = args.output_folder_path
    gpt_information_file = args.gpt_information_file

    spelling_checker_process(input_folder_path, output_folder_path, gpt_information_file)

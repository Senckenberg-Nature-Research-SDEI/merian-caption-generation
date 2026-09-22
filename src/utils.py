import os
import json
import sys


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



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


import sys
import json

def read_json_file(file_path):
    """
    Reads a JSON file and returns its content.
    
    Args:
        file_path (str): The path to the JSON file.
        
    Returns:
        dict: The content of the JSON file.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r') as file:
        return json.load(file)
    
def write_json_file(data, file_path):
    """
    Writes data to a JSON file.
    
    Args:
        data (dict): The data to be written to the file.
        file_path (str): The path to the JSON file.
    """
    if os.path.exists(file_path):
        print(f"Warning: The file {file_path} already exists and will be overwritten.", file=sys.stderr)
    
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def write_json_str(data, file_path):
    """
    Writes data to a JSON file, converting non-serializable types (like sets).

    Args:
        data (dict): The data to be written to the file.
        file_path (str): The path to the JSON file.
    """
    def convert(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    if os.path.exists(file_path):
        print(f"Warning: The file {file_path} already exists and will be overwritten.", file=sys.stderr)
    
    json_str = json.dumps(data, indent=4, default=convert)
    
    with open(file_path, 'w') as file:
        file.write(json_str)
        
def write_turtle_to_ttl(file_path, content):
    """
    Writes Turtle content to a TTL file.
    
    Args:
        file_path (str): The path to the TTL file.
        content (str): The Turtle content to be written.
    """
    content = "\n".join(content)  # Ensure content is a single string
    content = content.replace(' .', '.')
    content = content.replace(' ;', ';')

    with open(file_path, 'w') as file:
        file.write(content)

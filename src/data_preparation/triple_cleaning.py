import os
import sys
import json

from tqdm import tqdm
import ast
import logging

PACKAGE_PARENT = '.'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
PREFIX_PATH = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-2])
sys.path.append(PREFIX_PATH)

from src.utils import read_json_file, write_json_str

logging.basicConfig(level=logging.INFO, filename=f"{PREFIX_PATH}/logging/triple_cleaning.log", format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f"Prefix path: {PREFIX_PATH}")


def parse_first_json(json_str):
    decoder = json.JSONDecoder()
    obj, idx = decoder.raw_decode(json_str)
    return obj

def safe_str_to_dict(s):

    try:
        return parse_first_json(s)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(s)
        except Exception as e:
            # print("Parsing failed:", e)
            return s
def clenan_duplicates(data):
    
    seen = set()
    unique_data = []

    for item in data:
        item_str = json.dumps(item, sort_keys=True)
        if item_str not in seen:
            seen.add(item_str)
            unique_data.append(item)

    return unique_data

def clean_triples(input_data, dtype="text"):
    """
    Cleans triples from an input file and writes the cleaned triples to an output file.
    
    Args:
        input_file (str): The path to the input file containing triples.
        output_file (str): The path to the output file where cleaned triples will be saved.
    """
    try:

        
        cleaned_triples = []
        

        for item in tqdm(input_data, desc="Cleaning triples"):

            if dtype == "text":
                parts = item['entities_and_properties']
            elif dtype == "image":
                parts = item['image_info']['entities_and_properties']
            
            
            # Flatten parts in case it's a list of lists
            triple_list = []
            for i, part in enumerate(parts):
                # logging.info(f"Processing part {i+1}/{len(parts)}")

                json_str = "\n".join(part)
                # logging.info(f"JSON String: {json_str}")
                d = safe_str_to_dict(json_str)
                triple_list.append(d)
                # logging.info(f"Parsed JSON: {d}")

            if dtype == "text":
                item['cleaned_entities_and_properties'] = triple_list
            elif dtype == "image":
                item['image_info']['cleaned_entities_and_properties'] = triple_list
            
            cleaned_triples.append(item)
        
        # write_json_file(cleaned_triples, output_file)
   
        
        return cleaned_triples
    except Exception as e:
        logging.error(f"Error occurred while cleaning triples: {e}")
        return None


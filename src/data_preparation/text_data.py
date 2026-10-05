import os
import sys
import logging
import json

PACKAGE_PARENT = '.'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
PREFIX_PATH = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-3])
sys.path.append(PREFIX_PATH)

from src.utils import write_json_file
logging.basicConfig(level=logging.INFO, filename=f"{PREFIX_PATH}/logging/text_data.log", format='%(asctime)s - %(levelname)s - %(message)s')


def prepare_text_data(input_folder):
    """
    Prepares text data by reading from an input file and writing to an output file.
    
    Args:
        input_folder (str): The path to the input folder containing text files.
    """
    try:
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"The input folder {input_folder} does not exist.")
        
        data = []

        for filename in os.listdir(input_folder):
            if filename.endswith('.json'):
                file_path = os.path.join(input_folder, filename)
                file_data = open(file_path).read()

                file_data = json.loads(file_data)
                if not file_data['type'] == "text":
                    continue
          
                file_data = file_data['corrected_text']
                file_data = ''.join(file_data).strip()  # Join lines and strip whitespace
                
                info_file= {'file_name': filename, 'content': file_data}

                data.append(info_file)
        

        logging.info(f"Data has been prepared")
        return data

        

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return None

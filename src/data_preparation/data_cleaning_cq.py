import os
import sys
import logging
from tqdm import tqdm

PACKAGE_PARENT = '.'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
PREFIX_PATH = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-2])
sys.path.append(PREFIX_PATH)

logging.basicConfig(level=logging.INFO, filename=f"{PREFIX_PATH}/logging/data_cleaning_cq.log", format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f"Prefix path: {PREFIX_PATH}")



def prepare_data_cq(input_data, data_type='image'):
    """Cleans the competency questions from the input data
    Args:
        input_data (list): List of dictionaries containing competency questions.
        data_type (str): Type of data, either 'text' or 'image'. Default is 'image'.    
    Returns:
        list: Cleaned competency questions.
    """
    logging.info(f"Preparing data for {data_type}...")
    try:
       

        cleaned_data = []
        logging.info(f"Preparing data for {data_type}...")

        for item in tqdm(input_data, desc=f"Cleaning {data_type} data"):

            if data_type == "text":
                questions = item['competency_questions']

            if data_type == "image":
                questions = item['image_info']['competency_questions']

            competency_questions = []

            for question in questions:
                question = question.rstrip()
                if '.' in question:
                    question = ' '.join(question.split('.')[1:]).strip()
                    competency_questions.append(question)
            if data_type == "text":
                item['competency_questions'] = competency_questions
            if data_type == "image":
                item['image_info']['cleaning_question'] = competency_questions
            cleaned_data.append(item)
        logging.info(f"Data preparation for {data_type} completed successfully.")
        return cleaned_data
    
    except Exception as e:
        # print(f"Error in prepare_data_cq: {e}")
        logging.error(f"Error in prepare_data_cq: {e}")
        return None
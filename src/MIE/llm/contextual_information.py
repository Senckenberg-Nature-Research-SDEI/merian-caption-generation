import os
import sys
import json
import argparse
import logging
PACKAGE_PARENT = '.'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
PREFIX_PATH = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-3])
sys.path.append(PREFIX_PATH)
from src.utils import read_json_file, write_json_file

logging.basicConfig(level=logging.INFO, filename=f"{PREFIX_PATH}/logging/contextual_information.log", format='%(asctime)s - %(levelname)s - %(message)s')


def get_answer_from_conversation(context:str, delimiter: str = "###Assistant:") -> str:
    """
    Extracts the answer from a conversation string.
    
    Args:
        context (str): The conversation string containing the answer.
        
    Returns:
        str: The extracted answer.
    """
    if not context:
        return ""

    # Split the context by newline and take the last part as the answer
    parts = context.split(delimiter)
    return parts[-1].strip() if parts else ""


def combine_contextual_information(
    contextual_information: list[dict[str, str | int | float]], delimiter: str = "###Assistant:"
) -> dict[str, str | int | float]:
    """
    Combine a list of contextual information dictionaries into a single dictionary.
    
    Args:
        contextual_information (list[dict[str, str | int | float]]): List of dictionaries containing contextual information.
        
    Returns:
        dict[str, str | int | float]: Combined dictionary with unique keys.
    """
    try:
        combined_info = []
        logging.info("Combining contextual information...")
        for info in contextual_information:

            text_info = get_answer_from_conversation(info['image_info']['description'], delimiter) +\
                        get_answer_from_conversation(info['image_info']['objects'], delimiter) +\
                        get_answer_from_conversation(info['image_info']['basic_caption'], delimiter) +\
                        get_answer_from_conversation(info['image_info']['detailed_caption'], delimiter)
            
            info['image_info']['text'] = text_info

            combined_info.append(info)
        logging.info("Contextual information combined successfully.")
        return combined_info
    except Exception as e:
        logging.error(f"Error occurred while combining contextual information: {e}")
        return None
import os
import sys


from tqdm import tqdm
import logging

PACKAGE_PARENT = '.'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
PREFIX_PATH = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-3])
sys.path.append(PREFIX_PATH)
from src.utils import read_json_file, write_json_file  
logging.basicConfig(level=logging.INFO, filename=f"{PREFIX_PATH}/logging/gpt_based_cq_generation.log", format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f"GPT_based_cq_generation.py. Prefix path: {PREFIX_PATH}")

from MIE.llm.gpt import run_gpt_chat

def get_gpt_information(gpt_info):
    logging.info(f"Reading GPT information from {gpt_info}...")

    try:

        openai_api_key = gpt_info["openai_api_key"]

        if not openai_api_key:
            raise ValueError(f"The file {gpt_info} does not contain a valid 'openai_api_key' field.")
        gpt_role = gpt_info['gpt_role']

        model = gpt_info['model']


    except FileNotFoundError:
        raise FileNotFoundError(f"The file {gpt_info} does not exist.")

    return openai_api_key, gpt_role, model

def compentency_question_base(contextual_text):
    """
    Generates a competency question based on the provided contextual text.
    
    Args:
        contextual_text (str): The contextual text to base the question on.
        
    Returns:
        str: The generated competency question.
    """
    return f"Based on the following context, Please prepare competency questions for ontology development? Context: {contextual_text}"

def run_gpt_based_cq_generation(input_context, gpt_information_file):
    """
    Runs the GPT-based contextual question generation.
    
    Args:
        input_context (json): The JSON object containing contextual information.
        model (str): The GPT model to be used (default is "gpt-3.5-turbo").
    """


    
    input_queries = input_context
    cq_results = []
   
    for query in tqdm(input_queries, desc="Running GPT-based contextual question generation"):
       
        contextual_text = query['image_info']['text']
        user_query = compentency_question_base(contextual_text)
        gpt_information_file['user_query'] = user_query
        questions = run_gpt_chat(gpt_information_file)

        query['image_info']['competency_questions'] = questions
        cq_results.append(query)

    return cq_results


def run_gpt_based_cq_generation_from_text(input_context, gpt_information_file):
    """
    Runs the GPT-based contextual question generation.
    
    Args:
        input_file (str): Path to the JSON file containing GPT information.
        user_query (str): The user's query to be processed by GPT.
        model (str): The GPT model to be used (default is "gpt-3.5-turbo").
    """


    cq_results = []
    
    for query in tqdm(input_context, desc="Running GPT-based contextual question generation from text"):
        # print(f"Generated questions:")
        contextual_text = query['content']
        user_query = compentency_question_base(contextual_text)
        gpt_information_file['user_query'] = user_query
        questions = run_gpt_chat(gpt_information_file)
        query['competency_questions'] = questions
        
        cq_results.append(query)

    return cq_results

def cq_generation(input_context, gpt_information_file, image_file=True):
    """
    Main function to run the GPT-based contextual question generation.
    
    Args:
        input_file (str): Path to the JSON file containing GPT information.
        gpt_information_file (str): Path to the file containing GPT role and model information.
    """
    try:
        if image_file:
            compentency_questions = run_gpt_based_cq_generation(input_context, gpt_information_file)
        else:
            compentency_questions = run_gpt_based_cq_generation_from_text(input_context, gpt_information_file)
        logging.info("GPT-based contextual question generation completed.")
        return compentency_questions
    except Exception as e:
        logging.error(f"Error occurred during GPT-based contextual question generation: {e}")
        return None
  


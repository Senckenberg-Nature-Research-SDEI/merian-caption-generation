import openai
import logging
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

def run_gpt_chat(config):

    user_query = config['user_query']
   
    API_KEY = config['openai_api_key']
    model = config['model']

    openai.api_key = API_KEY

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": user_query}
        ],
        temperature=0,          # Makes output deterministic
        seed=42                 # Ensures repeatability across runs
    )

    return response['choices'][0]['message']['content'].split('\n')

def spelling_fixer(input_context, gpt_information):
    """
    Runs the GPT-based spelling correction for old German text.
    
    Args:
        input_context (str): The input text to be corrected.
        gpt_information (dict): A dictionary containing GPT information such as API key, role, and model.
    """

    contextual_text =input_context
    user_query = f"You are a helpful assistant for spelling correction in old German text.\n\nContext:\n{contextual_text}\n\n Please fix any spelling mistakes in the above old German text and return the corrected text."
    if gpt_information is None:
        raise ValueError("GPT information is required for spelling correction.")
    gpt_information["user_query"] = user_query
    
    corrected_text = run_gpt_chat(gpt_information)
        
    print(f"Corrected text: {corrected_text}")
    return corrected_text
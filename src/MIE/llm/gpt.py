import openai
import logging

def run_gpt_chat(config):
    # print(config)
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

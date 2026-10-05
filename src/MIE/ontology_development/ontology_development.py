import os
import sys
import json
import argparse
import openai
from tqdm import tqdm
import logging
from MIE.llm.gpt import run_gpt_chat

PACKAGE_PARENT = '.'

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
PREFIX_PATH = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-3])

sys.path.append(PREFIX_PATH)
from src.utils import read_json_file, write_turtle_to_ttl, write_json_file
logging.basicConfig(level=logging.INFO, filename=f"{PREFIX_PATH}/logging/ontology_development.log", format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(f"Prefix path: {PREFIX_PATH}")




def get_triples(entities_and_properties, gpt_config):
    """Extracts triples from entities and properties."""
    results = []
    gpt_config['user_query'] = " ".join(open(PREFIX_PATH  + gpt_config['neogpt_prompt_4']).readlines()).strip() + f"Entities and Properties:{entities_and_properties}"
    
    response = run_gpt_chat(gpt_config)
    results.append(response)

    return results

def get_entities_and_properties(cq, gpt_config):
    """
    Extracts entities and properties from the input data using GPT.
    
    Args:
        input_data (dict): The input data containing competency questions.
        gpt_config (dict): Configuration for GPT API.
        
    Returns:
        dict: A dictionary with competency questions as keys and extracted entities and properties as values.
    """
    results = []

    # print(f"GPT Config: {gpt_config}")
    gpt_config['user_query'] = " ".join(open(PREFIX_PATH  + gpt_config['neogpt_prompt_3']).readlines()).strip() + cq
    response = run_gpt_chat(gpt_config)
    results.append(response)

    return results

def convert_json_to_RDF(json_data, gpt_config):
    """
    Converts JSON data to RDF format.
    
    Args:
        json_data (dict): The input JSON data.
        
    Returns:
        str: The RDF representation of the JSON data.
    """
    
    # Placeholder for actual conversion logic
    gpt_config['user_query'] = " ".join(open(PREFIX_PATH  + gpt_config['neogpt_prompt_5']).readlines()).strip() + f"Triples and Individual: {json_data}"
    response = run_gpt_chat(gpt_config)
    rdf_data = response if response else ""
   
    return rdf_data

def generate_triples(input_data, out_file,  gpt_config, rdf_folder, dtype="image"):
    """
    Generates triples from the input data using GPT.

    Args:
        input_data (dict): The input data containing entities and properties.
        gpt_config (dict): Configuration for GPT API.

    Returns:
        list: The generated triples.
    """
    try:
        logging.info("Generating triples from input data...")
    
        generated_triples = []
        print(f"Input data keys: {input_data[0].keys()}")
        for item in tqdm(input_data, desc="Generating Triples"):
            print(f"Processing item: {item.keys()}")

            if dtype == "text":
                entities_and_properties = item['cleaned_entities_and_properties']
                triples = get_triples(entities_and_properties, gpt_config)
                item['triples'] = triples
                rdf_data = convert_json_to_RDF(triples, gpt_config)
                item['rdf_data'] = rdf_data
                write_turtle_to_ttl(os.path.join(rdf_folder, f"{item['file_name'].replace('.txt','')}.ttl"), rdf_data)
                logging.info(f"Generated RDF data for {item['file_name']} and saved to Turtle format.")
            else:
                entities_and_properties = item['image_info']['cleaned_entities_and_properties']
                triples = get_triples(entities_and_properties, gpt_config)
                item['image_info']['triples'] = triples
                rdf_data = convert_json_to_RDF(triples, gpt_config)
                item['image_info']['rdf_data'] = rdf_data
                write_turtle_to_ttl(os.path.join(rdf_folder, f"{item['image_info']['image_name'].replace('.jpg','')}.ttl"), rdf_data)
                logging.info(f"Generated RDF data for {item['image_info']['image_name']} and saved to Turtle format.")
            
            generated_triples.append(item)
    
        logging.info("Triples generation completed.")
        write_json_file(generated_triples, out_file)

    except Exception as e:
        logging.error(f"Error in generating triples: {e}")
        return None
    


def generate_ontology_concepts(input_data, gpt_config, dtype="image"):
    """
    Generates an ontology from the input data using GPT.

    Args:
        input_data (dict): The input data containing entities and properties.
        gpt_config (dict): Configuration for GPT API.

    Returns:
        list: The generated ontology.
    """
    try:
        logging.info("Generating ontology from input data...")

        generated_ontology_content = []
        
        for item in tqdm(input_data, desc="Reading Competency Questions"):
            print(f"Processing item: {item.keys()}")
            if dtype == "text":
                cqs = item['competency_questions']
            else:
                cqs = item['image_info']['competency_questions']
            entities_and_properties = []

            for cq in cqs:
                entities_and_properties.extend(get_entities_and_properties(cq, gpt_config))

            if dtype == "text":
                item['entities_and_properties'] = entities_and_properties
            else:
                item['image_info']['entities_and_properties'] = entities_and_properties

            generated_ontology_content.append(item)

            logging.info("Ontology generation completed. Writing to output file...")
          
        return generated_ontology_content
    
    except Exception as e:

        logging.error(f"Error in generating ontology concepts: {e}")
        return None

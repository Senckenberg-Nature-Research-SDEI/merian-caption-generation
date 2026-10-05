
import os
import sys
import argparse
import logging 

PACKAGE_PARENT = '.'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
PREFIX_PATH = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-2])
sys.path.append(PREFIX_PATH)
from utils import read_json_file
from data_preparation.data_cleaning_cq import prepare_data_cq
from data_preparation.text_data import prepare_text_data
from data_preparation.triple_cleaning import clean_triples
from MIE.ontology_development.ontology_development import generate_ontology_concepts, generate_triples
from src.MIE.llm.cq_generation import cq_generation


from MIE.llm.contextual_information import combine_contextual_information
from MIE.image.image2text import context_generation

logging.basicConfig(level=logging.INFO, filename=f"{PACKAGE_PARENT}/logging/mie.log", format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(f"Prefix path at main.py: {PREFIX_PATH}")


def text2ontology(input_file, output_file, text_rdf_folder, gpt_config):
    """
    Generates an ontology from the input data using GPT.

    Args:
        input_file (str): Path to the input JSON file containing competency questions.
        output_file (str): Path to the output JSON file where the generated ontology will be saved.
        text_rdf_folder (str): Path to the folder where the text RDF files will be saved.
        gpt_config (dict): Configuration for GPT API.

    Returns:
        None
    """
    try:
        print("Generating ontology from input data...")

        input_data = prepare_text_data(input_file)
        logging.info(f"Main.py-Input data loaded: {len(input_data)} items.")
        # generate competency questions
        competency_questions = cq_generation(input_data, gpt_config, image_file=False)
        logging.info(f"Main.py-Competency questions generated: {len(competency_questions)}")

        # clean questions
        cleaned_competency_questions = prepare_data_cq(competency_questions, data_type="text")
        logging.info(f"Main.py-Competency questions cleaned: {len(cleaned_competency_questions)}")
        
        # generate ontology
        print("Generating ontology concepts...")
        ontology_concepts = generate_ontology_concepts(cleaned_competency_questions, gpt_config, dtype="text")
        logging.info("Main.py-Ontology generated.")

        cleaned_concepts = clean_triples(ontology_concepts, dtype="text")
        generate_triples(cleaned_concepts, output_file, gpt_config, text_rdf_folder, dtype="text")
        logging.info("Main.py-Triples and entities generated and saved Turtles.")

    except Exception as e:
        logging.error(f"Error occurred: {e}")


def image2ontology(image_input_file, vlm_model, delimiter, questions_file, output_file, gpt_config, image_rdf_folder):
    """
    Generates an ontology from the input data using GPT.

    Args:
        image_input_file (str): Path to the input JSON file containing competency questions.
        output_file (str): Path to the output JSON file where the generated ontology will be saved.
        gpt_config (dict): Configuration for GPT API.

    Returns:
        None
    """
    logging.info("Generating ontology from input data...")

    """ Steps:
    1. Image to Text: Extract text from images.
    2. Generate Competency Questions: Use GPT to generate competency questions based on the text.
    3. Extract Entities and Properties: Use GPT to extract entities and properties from the competency questions.
    4. Generate Triples: Create RDF triples from the entities and properties.
    5. Convert to RDF: Convert the triples to RDF format and save them.
    6. Save the generated ontology to a file.
    7. Return the generated ontology content.
    8. Save the RDF data to a file.
    """
    try:
        
        image_context = context_generation(image_folder=image_input_file, questions_file=questions_file, model_name=vlm_model)
        
        image_full_context = combine_contextual_information(image_context, delimiter)
        logging.info(f"Main.py-Image context generated: {image_full_context}")
        
        competency_questions = cq_generation(image_full_context, gpt_config, image_file=True)
        logging.info(f"Main.py-Competency questions generated: {len(competency_questions)}")

        # clean questions
        cleaned_competency_questions = prepare_data_cq(competency_questions, data_type="image")
        logging.info(f"Main.py-Competency questions cleaned: {len(cleaned_competency_questions)}")
       
        # generate ontology
        ontology_concepts = generate_ontology_concepts(cleaned_competency_questions, gpt_config)
        logging.info("Main.py-Ontology generated.")

        cleaned_concepts = clean_triples(ontology_concepts, dtype="image")
        logging.info("Main.py-Clean concepts generated.")

        generate_triples(cleaned_concepts, output_file, gpt_config, image_rdf_folder)
        logging.info("Main.py-Triples and entities generated and saved Turtles.")

    except Exception as e:
       logging.error(f"Error occurred: {e}")

def main(image_input_file, text_input_file, vlm_model, delimiter_llava, questions_file, output_file, gpt_config_file, data_type, image_rdf_folder, text_rdf_folder):
    """
    Main function to generate ontology from input data using GPT.

    Args:
        image_input_file (str): Path to the input JSON file containing competency questions.
        text_input_file (str): Path to the input JSON file containing competency questions.
        vlm_model (str): Name of the vision-language model to use for image processing.
        questions_file (str): Path to the questions JSON file.
        output_file (str): Path to the output JSON file where the generated ontology will be saved.
        gpt_config_file (str): Path to the GPT configuration file.
        data_type (str): Type of data to process ('text' or 'image').
        image_rdf_folder (str): Path to the RDF files folder for images.
        text_rdf_folder (str): Path to the RDF files folder for text.
    """
    gpt_config = read_json_file(gpt_config_file)
    if data_type == 'text':
        print("Processing text data...")
        text2ontology(text_input_file, output_file, text_rdf_folder, gpt_config)
    elif data_type == 'image':
        image2ontology(image_input_file,
                        vlm_model,
                        delimiter_llava,
                        questions_file,
                        output_file,
                        gpt_config,
                        image_rdf_folder)
    else:
        raise ValueError("Invalid data type. Use 'text' or 'image'.")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Generate ontology from input data using GPT.")
    parser.add_argument("--image_input_file", type=str, default=f"{PREFIX_PATH}/merian-caption-generation/data/dataset/III/30.tif", help="Path to the input JSON file containing competency questions.")
    parser.add_argument("--text_input_file", type=str, default=f"{PREFIX_PATH}/merian-caption-generation/results/merian_maria_sybilla_corrected/III", help="Path to the input JSON file containing competency questions.")
    parser.add_argument("--vlm_model", type=str, default="llava-hf/vip-llava-7b-hf", help="Name of the vision-language model to use for image processing.")
    parser.add_argument("--questions_file", type=str, default=f"{PREFIX_PATH}/merian-caption-generation/conversation_templates/questions.json", help="Path to the questions JSON file.")
    parser.add_argument("--output_file", type=str, default=f"{PREFIX_PATH}/merian-caption-generation/results/marian/generated_text_ontology.json", help="Path to the output JSON file where the generated ontology will be saved.")
    parser.add_argument("--gpt_config_file", type=str, default=f"{PREFIX_PATH}/merian-caption-generation/api_keys/gpt_information_sample.json", help="Path to the GPT configuration file.")
    parser.add_argument("--data_type", type=str, choices=['text', 'image'], default="text", help="Type of data to process (text or image).")
    parser.add_argument("--image_rdf_folder", type=str, default=f"{PREFIX_PATH}/merian-caption-generation/image_rdf_files/", help="Path to the RDF files folder.")
    parser.add_argument("--text_rdf_folder", type=str, default=f"{PREFIX_PATH}/merian-caption-generation/rdf_file/text_rdf_files/", help="Path to the RDF files folder.")

    parser.add_argument(
        "--delimiter",
        type=str,
        default="###Assistant:",
        help="Llava Delimiter used to separate answers in the conversation (default: '###Assistant:')."
    )
    args = parser.parse_args()
    gpt_config = read_json_file(args.gpt_config_file)
    main(args.image_input_file, args.text_input_file, args.vlm_model, args.delimiter, args.questions_file, args.output_file, args.gpt_config_file, args.data_type, args.image_rdf_folder, args.text_rdf_folder)
import os
import sys
import json
from tqdm import tqdm
import argparse

PACKAGE_PARENT = '.'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
PREFIX_PATH = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-1])
sys.path.append(PREFIX_PATH)

print(f"Prefix path on image2text.py: {PREFIX_PATH}")

from vlm.llava import VisionLanguageModel

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

class ImageInformationExtraction():
    def __init__(self, questions_file="questions.json", vlm_model="LlavaNext"):
        """
        Initializes the ImageInformationError with a custom message.
        
        Args:
            message (str): The error message to be displayed.
        """
 
        if not os.path.exists(questions_file):
            raise FileNotFoundError(f"The questions file {questions_file} does not exist ")
        

        self.vlm = VisionLanguageModel()
        self.questions = read_json_file(questions_file)


    def get_image_information(self, image_path):
        """
        Retrieves information about an image file.
        
        Args:
            image_path (str): The path to the image file.
            
        Returns:
            dict: A dictionary containing information about the image.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"The image {image_path} does not exist.")
        
        # Placeholder for actual image processing logic
        description_qa = self.questions['description'] 
        objects_qa = self.questions['objects']
        basic_caption_qa = self.questions['basic_caption']
        detailed_caption_qa = self.questions['detailed_caption']
        return {
            'image_path': image_path,
            "image_name": os.path.basename(image_path),
            "image_size": os.path.getsize(image_path),
            "image_format": os.path.splitext(image_path)[1].lower(),
            "description": self.vlm.generate_response(image_path, self.vlm.generate_conversation(description_qa)),
            "objects": self.vlm.generate_response(image_path, self.vlm.generate_conversation(objects_qa)),
            "basic_caption": self.vlm.generate_response(image_path, self.vlm.generate_conversation(basic_caption_qa)),
            "detailed_caption": self.vlm.generate_response(image_path, self.vlm.generate_conversation(detailed_caption_qa))
            }

    def vlm_prompting(self, image_path, model_name="LlavaNext"):
        """
        Prompts a vision-language model with an image and retrieves information.
        
        Args:
            image_path (str): The path to the image file.
            model_name (str): The name of the vision-language model to use.
            
        Returns:
            dict: A dictionary containing the model's response.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"The image {image_path} does not exist.")
        
        # Placeholder for actual model interaction logic
        return {
            "model_name": model_name,
            "image_info": self.get_image_information(image_path)
        }

    def vlm_for_all_images(self, image_folder, model_name="LlavaNext"):
        """
        Processes multiple images with a vision-language model.
        
        Args:
            image_folder (str): The folder containing the image files.
            model_name (str): The name of the vision-language model to use.
            
        Returns:
            list: A list of dictionaries containing the model's responses for each image.
        """
        responses = []
        if image_folder.lower().endswith(('.tif', '.png', '.jpg', '.jpeg')):

            image_paths = [image_folder]
        else:
            image_paths = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.lower().endswith(('.tif', '.png', '.jpg', '.jpeg'))]

        for image_path in tqdm(image_paths, desc="Processing images"):
            try:
                response = self.vlm_prompting(image_path, model_name)
                responses.append(response)
                # print(f"Processing {image_path} with model {model_name}")
            except FileNotFoundError as e:
                print(f"Error processing {image_path}: {e}", file=sys.stderr)
        
        return responses
   
def context_generation(image_folder, questions_file='questions.json', model_name="LlavaNext", output_file=None):
    """
    Main function to process images and retrieve information using a vision-language model.
    
    Args:
        questions_file (str): The path to the questions JSON file.
        image_folder (str): The folder containing the image files.
        model_name (str): The name of the vision-language model to use.
        
    Returns:
        list: A list of dictionaries containing the model's responses for each image.
    """
    image_info = ImageInformationExtraction(questions_file, model_name)
    responses = image_info.vlm_for_all_images(image_folder, model_name)

    if output_file:
        write_json_file(responses, output_file)
    else:
        return responses


            
from transformers import AutoProcessor, VipLlavaForConditionalGeneration, LlavaNextProcessor, LlavaNextForConditionalGeneration
import torch
from PIL import Image

class VisionLanguageModel():
    """
    A class to handle vision-language models, specifically LlavaNext.
    This class initializes the model and processor, prepares the input,
    and generates responses based on the input image and text prompt.
    """
    def __init__(self, model_name="llava-hf/vip-llava-7b-hf"):
        """
        Initializes the LlavaNext processor and model.
        Loads the model with low CPU memory usage and sets it to half precision.
        """
        # Use the correct processor and model class based on the model name
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.model_dtype = torch.float16
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
            self.model_dtype = torch.float16
        else:
            self.device = torch.device("cpu")
            self.model_dtype = torch.float32

        model_kwargs = {
            "torch_dtype": self.model_dtype,
        }
        if self.device.type == "cuda":
            model_kwargs["device_map"] = "auto"
        else:
            model_kwargs["low_cpu_mem_usage"] = True

        if model_name == "llava-hf/vip-llava-7b-hf":
            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = VipLlavaForConditionalGeneration.from_pretrained(model_name, **model_kwargs)
        else:
            # Default to LlavaNext if a different model name is provided
            self.processor = LlavaNextProcessor.from_pretrained(model_name)
            self.model = LlavaNextForConditionalGeneration.from_pretrained(model_name, **model_kwargs)

        if self.device.type != "cuda":
            self.model = self.model.to(self.device)


    def generate_response(self, image_url, conversation):
        """
        Generates a response based on the provided image URL and conversation history.

        Args:
            image_url (str): The URL of the image to be processed.
            conversation (list): A list of dictionaries representing the conversation history.

        Returns:
            str: The generated response from the model.
        """
        # Load the image from the URL
        image = Image.open(image_url)

        # Prepare the prompt using the conversation history
        prompt = self.processor.apply_chat_template(conversation, add_generation_prompt=True)

        # Process the inputs
        # Move inputs to the same device as the loaded model.
        inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(self.device, dtype=self.model_dtype)


        # Generate the output
        output = self.model.generate(**inputs, max_new_tokens=200)

        # The original code used [0][2:], let's keep it but be mindful
        return self.processor.decode(output[0][2:], skip_special_tokens=True)

    def generate_conversation(self, text_content):
        """
        Generates a conversation response based on the provided image URL and conversation history.

        Args:
            text_content (str): The text content for the user's message.

        Returns:
            list: A list of dictionaries representing the conversation.
        """
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{text_content}"},
                    {"type": "image"},
                ],
            }
        ]
        return conversation

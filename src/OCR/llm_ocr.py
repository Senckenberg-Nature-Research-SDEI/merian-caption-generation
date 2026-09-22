
import os
import base64
from io import BytesIO
from PIL import Image
import time
import json # Ensure json is imported if not already in global scope
import argparse

def write_output(output, output_path):
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4)
        print(f"Output successfully saved as JSON: {output_path}")
    except TypeError as e:
        print(f"Output is not JSON serializable: {e}")
        txt_output_path = output_path.replace(".json", ".txt")
        with open(txt_output_path, "w", encoding="utf-8") as f:
            f.write(str(output))
        print(f"Output saved as plain text: {txt_output_path}")

def olmocr_setup(folder_path, media_extension=".tif", output_base_dir="output"):
    
  document_name = os.path.basename(folder_path)

  os.makedirs(output_base_dir, exist_ok=True)

  for file_name in os.listdir(folder_path):
      if file_name.endswith(media_extension):
        start_time_file = time.time()
        file_full_path = os.path.join(folder_path, file_name)
        print(f"Processing file: {file_full_path}")

        image_base64 = None
        # Determine how to process the file based on its extension
        if media_extension == ".pdf":
            image_base64 = render_pdf_to_base64png(file_full_path, 1, target_longest_image_dim=1024)
            anchor_text = get_anchor_text(file_full_path, 1, pdf_engine="pdfreport", target_length=400000)
        elif media_extension == ".tif" or media_extension == ".png" or media_extension == ".jpg" or media_extension == ".jpeg":
            with Image.open(file_full_path) as img:
                if img.mode == 'CMYK':
                    img = img.convert('RGB')
                longest_dim = max(img.size)
                if longest_dim > 1024:
                    scale_factor = 1024 / longest_dim
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            anchor_text = "" # No anchor text for images from PDF tools
        else:
            raise ValueError(f"Unsupported media extension: {media_extension}. Supported extensions are .pdf, .tif, .png, .jpg, .jpeg.")

        prompt = build_finetuning_prompt(anchor_text)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                ],
            }
        ]

        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        main_image = Image.open(BytesIO(base64.b64decode(image_base64)))

        inputs = processor(
            text=[text],
            images=[main_image],
            padding=True,
            return_tensors="pt",
        )
        inputs = {key: value.to(device) for (key, value) in inputs.items()}

        output = model.generate(
            **inputs,
            temperature=0.9,
            max_new_tokens=2000,
            num_return_sequences=1,
            do_sample=True,
        )

        prompt_length = inputs["input_ids"].shape[1]
        new_tokens = output[:, prompt_length:]

        print(f"Number of generated sequences: {len(new_tokens)}")

        text_output = processor.tokenizer.batch_decode(new_tokens, skip_special_tokens=True)
        generated_text = text_output[0]

        end_time_file = time.time()
        processing_time_file = end_time_file - start_time_file

        output_file_name = file_name.replace(media_extension, "_output.json")
        output_json_path = os.path.join(output_base_dir, output_file_name)

        json_successfully_parsed = False

        print(f"Attempting to save output to: {output_json_path}")

        try:
            parsed_output = json.loads(generated_text)
            write_output(parsed_output, output_json_path)
            json_successfully_parsed = True
        except json.JSONDecodeError:

            print("Output is not valid JSON, saving as plain text.")

            txt_output_path = output_json_path.replace(".json", ".txt")
            with open(txt_output_path, "w", encoding="utf-8") as f:
                f.write(generated_text)

            print(f"Output saved as plain text: {txt_output_path}")

        print("\nGenerated Output:\n", generated_text)
        print(f"\nProcessing Time for {file_name}: {processing_time_file:.2f} seconds")

        final_output_path = output_json_path if json_successfully_parsed else output_json_path.replace('.json', '.txt')
        print(f"\nOutput saved to {final_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OLM OCR on a dataset.")
    parser.add_argument("--dataset_path", type=str, default="./dataset", help="Path to the dataset directory containing sections with media files.")
    args = parser.parse_args()  
    dataset_path = args.dataset_path
    output_base_dir = os.path.join("drive", "MyDrive", "SDEI", "merian_maria_sybilla", document_name)

    for section in os.listdir(dataset_path):
        section_folder_path = os.path.join(dataset_path, section)
        output_base_dir_section = os.path.join(output_base_dir, section)
        olmocr_setup(section_folder_path, output_base_dir=output_base_dir_section)

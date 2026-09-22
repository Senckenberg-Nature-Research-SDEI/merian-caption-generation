# Nature, Culture and Heritage Ontology

This repository contains a prototype pipeline for building a multimodal ontology from historical nature-heritage material. The project is centered on Maria Sibylla Merian's work and is intended to connect concepts identified in paintings or scanned documents with entities and descriptions found in related articles.

The current repository contains data derived from the digitized source described below, OCR output, shared JSON utilities, and an early text-cleaning/grammar-correction stage. The concept-recognition, entity-recognition, entity-linking, caption-generation, and ontology-drafting directories are present as extension points but do not currently contain implementation files.

## Pipeline

The intended workflow is:

1. **OCR**: extract structured text from images in `data/dataset/`.
2. **Text correction**: clean OCR output and prepare corrected JSON files.
3. **Multimodal information extraction**: recognize concepts and entities from images and text.
4. **Entity linking**: connect extracted entities to a shared vocabulary or ontology.
5. **Ontology drafting**: assemble the linked concepts into an ontology.

At present, the text-correction stage is the most complete runnable stage. Existing OCR results are stored under `results/merian_maria_sybilla/`, with corrected copies under `results/merian_maria_sybilla_corrected/`.

## Repository layout

```text
data/dataset/                         Source material, grouped by section
keys/api_token.json                   Local API configuration (do not commit secrets)
results/merian_maria_sybilla/         OCR JSON output
results/merian_maria_sybilla_corrected/  Cleaned/corrected JSON output
src/utils.py                          JSON loading and output helpers
src/OCR/llm_ocr.py                    Experimental image OCR pipeline
src/grammar_checker/gpt.py            OpenAI helper for German text correction
src/grammar_checker/spelling_checker.py  OCR text cleaning pipeline
src/multimodal_IE/                    Planned concept/entity extraction stages
src/caption_generation/               Planned image captioning stage
src/ontology_drafting/                Planned ontology construction stage
```

## Requirements

- Python 3.9 or newer
- An OpenAI API key for the GPT-based correction helper
- Image/model dependencies for the experimental OCR module, including Pillow and the model runtime used by the local OCR implementation

Install the dependencies currently declared by the project:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The OCR module imports `PIL`, but Pillow is not currently listed in `requirements.txt`. Install it separately when working on OCR:

```bash
python -m pip install pillow
```

## API configuration

The correction code expects a JSON configuration file with the following shape:

```json
{
	"gpt_role": "You are a helpful assistant for spelling and grammar correction in German.",
	"openai_api_key": "YOUR_API_KEY",
	"API_URL": "https://api.openai.com/v1/chat/completions",
	"model": "gpt-3.5-turbo"
}
```

Do not commit a real API key. Keep local credentials outside version control, rotate any key that has been exposed, and pass the path to a local configuration file with `--gpt_information_file`.

## Run text cleaning

The spelling-checker script reads sectioned OCR JSON files. Each input JSON file is expected to contain a `natural_text` field. The current process cleans line breaks and separator characters and writes a new JSON file with `corrected_text`, `corrections`, and `type` fields.

From the repository root:

```bash
python src/grammar_checker/spelling_checker.py \
	--input_folder_path results/merian_maria_sybilla \
	--output_folder_path results/merian_maria_sybilla_corrected \
	--gpt_information_file keys/api_token.json
```

The current implementation performs deterministic text normalization by default. The GPT correction call is available in `src/grammar_checker/gpt.py`, but is not enabled in `spelling_checker_process`.

## OCR stage

`src/OCR/llm_ocr.py` is an experimental batch OCR implementation. It scans section directories for `.tif` files, resizes images, prepares multimodal prompts, and attempts to save generated JSON or plain-text output.

Its command-line interface accepts:

```bash
python src/OCR/llm_ocr.py --dataset_path data/dataset
```

This module is not currently a self-contained executable: model, processor, device, prompt, and PDF helper objects are referenced but not defined in the file, and its `__main__` block uses an undefined `document_name`. Treat it as an implementation starting point until those runtime dependencies and configuration are supplied.

## Data and output conventions

- The source publication is the Zenodo record [*Der Raupen wunderbare Verwandelung, und sonderbare Blumen-nahrung*](https://zenodo.org/records/21458361), a digitized book by Maria Sibylla Merian published by Senckenberg – Leibniz Institution for Biodiversity and Earth System Research.
- The record provides PDF, JPG, and TIFF downloads under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/). The repository uses sectioned image data derived from this source.
- Source files are grouped into Roman-numeral section directories such as `I/`, `II/`, and `XLIX/`.
- OCR output is organized using the same section structure.
- JSON output is indented for readability.
- If generated OCR text cannot be parsed as JSON, the OCR stage writes a `.txt` fallback.
- Existing output files may be overwritten by the processing scripts.

Recommended citation for the source material:

> Merian, M. S. (2026). *Der Raupen wunderbare Verwandelung, und sonderbare Blumen-nahrung*. Senckenberg – Leibniz Institution for Biodiversity and Earth System Research. https://doi.org/10.12761/sgn.2026.07.b877

## Development status

**WIP:** This is research code under active development rather than a packaged command-line application. The remaining pipeline components and supporting code are planned to be included across the codebase within the next week. There are currently no automated tests or formal ontology schema in the repository. Before using the outputs for analysis, inspect representative JSON files and verify model responses, OCR quality, and entity-linking assumptions.

## License

The project is distributed under the GNU General Public License version 3. See [LICENSE](LICENSE).

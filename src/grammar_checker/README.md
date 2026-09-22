# Grammar checker

This folder contains utilities for cleaning and correcting OCR text before it is used in downstream analysis.

## Current contents

- `spelling_checker.py` – main text-cleaning pipeline for OCR output.
- `gpt.py` – GPT-based correction helper for grammar and spelling refinement.

## Purpose

The grammar-checking stage normalizes noisy text, repairs common OCR artifacts, and prepares cleaner textual data for concept extraction and captioning tasks.

## Typical workflow

1. Read OCR JSON files from the results directory.
2. Normalize text formatting and separators.
3. Optionally apply GPT-based correction.
4. Write corrected output into a new results directory.

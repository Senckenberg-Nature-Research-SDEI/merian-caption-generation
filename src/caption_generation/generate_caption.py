import argparse
import json
import logging
import re
from pathlib import Path
from typing import Iterable
from urllib import error, request


logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(levelname)s - %(message)s",
)


TRIPLE_PATTERN = re.compile(
	r"\(\s*([^,()]+?)\s*,\s*([^,()]+?)\s*,\s*([^,()]+?)\s*\)"
)


def read_json_file(file_path: Path) -> dict:
	"""Read a JSON file and return it as a dict."""
	with file_path.open("r", encoding="utf-8") as f:
		return json.load(f)


def parse_triples_text(triples_text: str) -> list[tuple[str, str, str]]:
	"""Parse triples from text in (subject, predicate, object) format."""
	triples: list[tuple[str, str, str]] = []
	for match in TRIPLE_PATTERN.finditer(triples_text):
		subject = match.group(1).strip()
		predicate = match.group(2).strip()
		obj = match.group(3).strip()
		triples.append((subject, predicate, obj))
	return triples


def parse_triples_file(triples_file: Path) -> list[tuple[str, str, str]]:
	"""Parse triples from either JSON list format or plain text tuple format."""
	content = triples_file.read_text(encoding="utf-8").strip()
	if not content:
		return []

	# First try JSON list format: [[s, p, o], ...]
	try:
		data = json.loads(content)
		if isinstance(data, list):
			triples: list[tuple[str, str, str]] = []
			for item in data:
				if isinstance(item, (list, tuple)) and len(item) == 3:
					triples.append((str(item[0]), str(item[1]), str(item[2])))
			return triples
	except json.JSONDecodeError:
		pass

	# Fallback to text format: (s, p, o)
	return parse_triples_text(content)


def normalize_triples(triples: Iterable[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
	"""Normalize and deduplicate triples while preserving order."""
	seen: set[tuple[str, str, str]] = set()
	normalized: list[tuple[str, str, str]] = []

	for triple in triples:
		if len(triple) != 3:
			continue
		subject, predicate, obj = (str(part).strip() for part in triple)
		current = (subject, predicate, obj)
		if subject and predicate and obj and current not in seen:
			seen.add(current)
			normalized.append(current)

	return normalized


def triples_to_prompt(triples: list[tuple[str, str, str]]) -> str:
	"""Build the user prompt for caption generation."""
	triple_lines = "\n".join(f"- ({s}, {p}, {o})" for s, p, o in triples)
	return (
		"Generate one coherent image caption from the RDF-like triples below. "
		"The caption must cover every triple fact at least once, avoid hallucinations, and keep it natural. "
		"Return only the caption text.\n\n"
		f"Triples:\n{triple_lines}\n"
	)


def run_gpt_chat(user_query: str, gpt_config: dict) -> str:
	"""Call GPT chat completions API and return plain text output."""
	api_key = gpt_config["openai_api_key"]
	api_url = gpt_config.get("API_URL", "https://api.openai.com/v1/chat/completions")
	model = gpt_config.get("caption_model", gpt_config.get("model", "gpt-4o-mini"))
	system_role = gpt_config.get(
		"caption_role",
		"You are a precise caption generator for ontology triples. Please do not include any new information that is not present in the triples.",
	)

	payload = {
		"model": model,
		"messages": [
			{"role": "system", "content": system_role},
			{"role": "user", "content": user_query},
		],
		"temperature": 0.2,
	}

	req = request.Request(
		api_url,
		data=json.dumps(payload).encode("utf-8"),
		headers={
			"Content-Type": "application/json",
			"Authorization": f"Bearer {api_key}",
		},
		method="POST",
	)

	try:
		with request.urlopen(req, timeout=180) as response:
			body = response.read().decode("utf-8")
	except error.HTTPError as e:
		error_text = e.read().decode("utf-8", errors="replace")
		raise RuntimeError(f"GPT API error: {e.code} {error_text}") from e

	response_json = json.loads(body)
	return response_json["choices"][0]["message"]["content"].strip()


def generate_caption_from_triples(
	triples: list[tuple[str, str, str]],
	gpt_config: dict,
) -> str:
	"""Generate caption text from a list of triples."""
	normalized = normalize_triples(triples)
	if not normalized:
		raise ValueError("No valid triples found. Expected format: (subject, predicate, object)")

	prompt = triples_to_prompt(normalized)
	return run_gpt_chat(prompt, gpt_config)


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Generate a caption from a list of triples using GPT."
	)
	parser.add_argument(
		"--triples-text",
		type=str,
		default="",
		help="Triples in text format, e.g. '(tulip, has_part, petal)'",
	)
	parser.add_argument(
		"--triples-file",
		type=Path,
		default=Path("/Users/sefeoglu/projects/merian-caption-generation/results/marian/triples/triples_2.json"),
		help="Optional text file containing triples in (s, p, o) format",
	)
	parser.add_argument(
		"--gpt-config-file",
		type=Path,
		default=Path("api_keys/gpt_information_sample.json"),
		help="Path to GPT config JSON file",
	)
	parser.add_argument(
		"--output-file",
		type=Path,
		default=Path("/Users/sefeoglu/projects/merian-caption-generation/results/marian/triples/triples_caption.txt"),
		help="Optional file to save generated caption",
	)

	args = parser.parse_args()

	triples: list[tuple[str, str, str]] = []
	if args.triples_text:
		triples = parse_triples_text(args.triples_text)
	elif args.triples_file is not None:
		triples = parse_triples_file(args.triples_file)

	gpt_config = read_json_file(args.gpt_config_file)
	caption = generate_caption_from_triples(triples, gpt_config)

	if args.output_file is not None:
		args.output_file.parent.mkdir(parents=True, exist_ok=True)
		args.output_file.write_text(caption + "\n", encoding="utf-8")
		logging.info("Caption written to: %s", args.output_file)

	print(caption)


if __name__ == "__main__":
	main()

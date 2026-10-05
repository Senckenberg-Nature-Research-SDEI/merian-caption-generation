import argparse
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(levelname)s - %(message)s",
)

TERM_PATTERN = re.compile(r":([A-Za-z_][A-Za-z0-9_-]*)")
CLASS_PATTERN = re.compile(r"^\s*:([A-Za-z_][A-Za-z0-9_-]*)\s+a\s+owl:Class\s*\.\s*$")
OBJECT_PROPERTY_PATTERN = re.compile(r"^\s*:([A-Za-z_][A-Za-z0-9_-]*)\s+a\s+owl:ObjectProperty\s*\.\s*$")
DATATYPE_PROPERTY_PATTERN = re.compile(r"^\s*:([A-Za-z_][A-Za-z0-9_-]*)\s+a\s+owl:DatatypeProperty\b")
INDIVIDUAL_PATTERN = re.compile(r"^\s*:([A-Za-z_][A-Za-z0-9_-]*)\s+rdf:type\s+owl:NamedIndividual\b")

GENERIC_TERMS = {
	"Class",
	"DatatypeProperty",
	"ObjectProperty",
	"NamedIndividual",
	"type",
	"range",
	"domain",
	"string",
	"boolean",
	"integer",
	"float",
	"double",
	"decimal",
	"date",
	"dateTime",
	"time",
	"anyURI",
}


@dataclass
class TurtleParts:
	prefixes: list[str]
	body_lines: list[str]


@dataclass
class OntologyTerms:
	classes: list[str]
	object_properties: list[str]
	datatype_properties: list[str]
	individuals: list[str]
	all_terms: list[str]


def read_json_file(file_path: str) -> dict:
	"""Read and parse a JSON file."""
	with open(file_path, "r", encoding="utf-8") as f:
		return json.load(f)


def build_text_rdf_paths(text_rdf_dir: Path, start: int, end: int) -> list[Path]:
	"""Build paths like 21_output.json.ttl ... 25_output.json.ttl."""
	return [text_rdf_dir / f"{idx}_output.json.ttl" for idx in range(start, end + 1)]


def split_turtle_content(file_path: Path) -> TurtleParts:
	"""Split Turtle-like content into prefix lines and body lines."""
	prefixes: list[str] = []
	body: list[str] = []

	with file_path.open("r", encoding="utf-8") as f:
		for line in f:
			stripped = line.strip()
			if not stripped:
				continue
			if stripped.startswith("@prefix"):
				prefixes.append(stripped)
			else:
				body.append(line)

	return TurtleParts(prefixes=prefixes, body_lines=body)


def extract_local_terms(lines: list[str]) -> list[str]:
	"""Extract local ontology terms like :Plant, :hasColor from Turtle lines."""
	terms: set[str] = set()
	for line in lines:
		for term in TERM_PATTERN.findall(line):
			if term not in GENERIC_TERMS:
				terms.add(term)
	return sorted(terms)


def extract_typed_terms(lines: list[str]) -> OntologyTerms:
	"""Extract ontology terms by type from Turtle body lines."""
	classes: set[str] = set()
	object_properties: set[str] = set()
	datatype_properties: set[str] = set()
	individuals: set[str] = set()

	for line in lines:
		class_match = CLASS_PATTERN.match(line)
		if class_match:
			classes.add(class_match.group(1))

		obj_prop_match = OBJECT_PROPERTY_PATTERN.match(line)
		if obj_prop_match:
			object_properties.add(obj_prop_match.group(1))

		datatype_match = DATATYPE_PROPERTY_PATTERN.match(line)
		if datatype_match:
			datatype_properties.add(datatype_match.group(1))

		individual_match = INDIVIDUAL_PATTERN.match(line)
		if individual_match:
			individuals.add(individual_match.group(1))

	all_terms = sorted((classes | object_properties | datatype_properties | individuals) - GENERIC_TERMS)
	return OntologyTerms(
		classes=sorted(classes - GENERIC_TERMS),
		object_properties=sorted(object_properties - GENERIC_TERMS),
		datatype_properties=sorted(datatype_properties - GENERIC_TERMS),
		individuals=sorted(individuals - GENERIC_TERMS),
		all_terms=all_terms,
	)


def strip_markdown_fences(text: str) -> str:
	"""Remove optional fenced code blocks from model output."""
	clean = text.strip()
	if clean.startswith("```"):
		clean = re.sub(r"^```[a-zA-Z0-9_]*\n", "", clean)
		clean = re.sub(r"\n```$", "", clean)
	return clean.strip()


def call_chatgpt_for_mapping(image_terms: OntologyTerms, text_terms: OntologyTerms, gpt_config: dict) -> dict:
	"""Ask ChatGPT for ontology alignments between source and target terms."""
	api_key = gpt_config["openai_api_key"]
	api_url = gpt_config.get("API_URL", "https://api.openai.com/v1/chat/completions")
	model = gpt_config.get("mapping_model", gpt_config.get("model", "gpt-4o-mini"))

	source_payload = {
		"classes": image_terms.classes,
		"object_properties": image_terms.object_properties,
		"datatype_properties": image_terms.datatype_properties,
		"individuals": image_terms.individuals,
	}
	target_payload = {
		"classes": text_terms.classes,
		"object_properties": text_terms.object_properties,
		"datatype_properties": text_terms.datatype_properties,
		"individuals": text_terms.individuals,
	}

	user_query = (
		"Create ontology alignments from SOURCE ontology to TARGET ontology. "
		"Link entities and concepts, not lexical identity. "
		"Avoid trivial mappings where source == target unless absolutely necessary. "
		"Do not invent terms; every source and target must be from the given lists. "
		"Use relation labels only: equivalentClass, equivalentProperty, sameAs, closeMatch, relatedMatch. "
		"Return ONLY valid JSON with exactly this shape: "
		"{\"links\":[{\"source\":\"...\",\"source_type\":\"class|object_property|datatype_property|individual\",\"target\":\"...\",\"target_type\":\"class|object_property|datatype_property|individual\",\"relation\":\"equivalentClass|equivalentProperty|sameAs|closeMatch|relatedMatch\",\"confidence\":0.0,\"reason\":\"short rationale\"}]}.\n\n"
		f"SOURCE_ONTOLOGY_TERMS (image RDF): {json.dumps(source_payload)}\n"
		f"TARGET_ONTOLOGY_TERMS (text RDF): {json.dumps(target_payload)}\n"
	)

	payload = {
		"model": model,
		"messages": [
			{"role": "system", "content": "You are a precise ontology alignment assistant."},
			{"role": "user", "content": user_query},
		],
		"temperature": 0,
	}

	data = json.dumps(payload).encode("utf-8")
	req = request.Request(
		api_url,
		data=data,
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
		raise RuntimeError(f"ChatGPT mapping request failed: {e.code} {error_text}") from e

	response_json = json.loads(body)
	content = response_json["choices"][0]["message"]["content"]
	content = strip_markdown_fences(content)
	mapping_payload = json.loads(content)

	if not isinstance(mapping_payload, dict) or "links" not in mapping_payload:
		raise ValueError("ChatGPT mapping response must be a JSON object with a 'links' key.")

	links = mapping_payload.get("links", [])
	if not isinstance(links, list):
		raise ValueError("ChatGPT mapping 'links' must be a list.")

	source_terms = set(image_terms.all_terms)
	target_terms = set(text_terms.all_terms)
	allowed_types = {"class", "object_property", "datatype_property", "individual"}
	allowed_relations = {"equivalentClass", "equivalentProperty", "sameAs", "closeMatch", "relatedMatch"}

	filtered_links: list[dict] = []
	for item in links:
		if not isinstance(item, dict):
			continue

		source = item.get("source")
		target = item.get("target")
		source_type = item.get("source_type")
		target_type = item.get("target_type")
		relation = item.get("relation")
		confidence = item.get("confidence", 0.0)
		reason = item.get("reason", "")

		if not isinstance(source, str) or not isinstance(target, str):
			continue
		if source == target:
			continue
		if source not in source_terms or target not in target_terms:
			continue
		if source in GENERIC_TERMS or target in GENERIC_TERMS:
			continue
		if source_type not in allowed_types or target_type not in allowed_types:
			continue
		if relation not in allowed_relations:
			continue

		try:
			confidence_val = float(confidence)
		except (TypeError, ValueError):
			confidence_val = 0.0

		filtered_links.append(
			{
				"source": source,
				"source_type": source_type,
				"target": target,
				"target_type": target_type,
				"relation": relation,
				"confidence": round(confidence_val, 3),
				"reason": str(reason),
			}
		)

	return {"links": filtered_links}


def build_rewrite_mapping(
	mapping_payload: dict,
	min_confidence: float = 0.65,
	allowed_relations: set[str] | None = None,
) -> dict[str, str]:
	"""Build source->target replacements from strong equivalence links only."""
	if allowed_relations is None:
		allowed_relations = {"equivalentClass", "equivalentProperty", "sameAs", "closeMatch"}

	rewrite_mapping: dict[str, str] = {}
	for link in mapping_payload.get("links", []):
		relation = link.get("relation")
		confidence = float(link.get("confidence", 0.0))
		if relation in allowed_relations and confidence >= min_confidence:
			rewrite_mapping[link["source"]] = link["target"]
	return rewrite_mapping


def filter_links(mapping_payload: dict, allowed_relations: set[str], min_confidence: float) -> list[dict]:
	"""Filter links by relation and confidence for export and auditing."""
	filtered: list[dict] = []
	for link in mapping_payload.get("links", []):
		relation = link.get("relation")
		confidence = float(link.get("confidence", 0.0))
		if relation in allowed_relations and confidence >= min_confidence:
			filtered.append(link)
	return filtered


def apply_term_mapping(lines: list[str], mapping: dict[str, str]) -> list[str]:
	"""Apply :Source -> :Target replacements on Turtle body lines."""
	mapped_lines: list[str] = []
	for line in lines:
		updated = line
		for src_term, dst_term in mapping.items():
			updated = re.sub(
				rf"(?<![A-Za-z0-9_-]):{re.escape(src_term)}(?![A-Za-z0-9_-])",
				f":{dst_term}",
				updated,
			)
		mapped_lines.append(updated)
	return mapped_lines


def read_many_ttl(files: list[Path]) -> TurtleParts:
	"""Read multiple Turtle-like files and return deduped prefixes and body lines."""
	all_prefixes: list[str] = []
	all_body: list[str] = []
	seen_prefixes: set[str] = set()

	for file_path in files:
		if not file_path.exists():
			logging.warning("Skipping missing file: %s", file_path)
			continue
		logging.info("Reading: %s", file_path)
		parts = split_turtle_content(file_path)

		for prefix in parts.prefixes:
			if prefix not in seen_prefixes:
				seen_prefixes.add(prefix)
				all_prefixes.append(prefix)
		all_body.extend(parts.body_lines)

	return TurtleParts(prefixes=all_prefixes, body_lines=all_body)


def write_merged_ttl(output_file: Path, prefixes: list[str], body_lines: list[str]) -> None:
	"""Write merged Turtle-like content with deduped body lines."""
	seen_body: set[str] = set()
	unique_body: list[str] = []
	for line in body_lines:
		if line not in seen_body:
			seen_body.add(line)
			unique_body.append(line)

	output_file.parent.mkdir(parents=True, exist_ok=True)
	with output_file.open("w", encoding="utf-8") as f:
		for prefix in prefixes:
			f.write(prefix + "\n")
		f.write("\n")
		for line in unique_body:
			f.write(line)

	logging.info("Merged output written with %d unique body lines: %s", len(unique_body), output_file)


def merge_with_gpt_mapping(
	text_files: list[Path],
	image_file: Path,
	gpt_config_file: Path,
	output_file: Path,
	mapping_output: Path,
	min_confidence: float,
	strict_links_only: bool,
) -> None:
	"""Map terms with ChatGPT, rewrite image triples, then merge into one Turtle file."""
	text_parts = read_many_ttl(text_files)
	if not image_file.exists():
		raise FileNotFoundError(f"Image RDF file not found: {image_file}")

	image_parts = split_turtle_content(image_file)

	text_typed_terms = extract_typed_terms(text_parts.body_lines)
	image_typed_terms = extract_typed_terms(image_parts.body_lines)
	logging.info(
		"Extracted typed terms for mapping. text(classes=%d, obj=%d, data=%d, ind=%d), image(classes=%d, obj=%d, data=%d, ind=%d)",
		len(text_typed_terms.classes),
		len(text_typed_terms.object_properties),
		len(text_typed_terms.datatype_properties),
		len(text_typed_terms.individuals),
		len(image_typed_terms.classes),
		len(image_typed_terms.object_properties),
		len(image_typed_terms.datatype_properties),
		len(image_typed_terms.individuals),
	)

	gpt_config = read_json_file(str(gpt_config_file))
	mapping_payload = call_chatgpt_for_mapping(image_terms=image_typed_terms, text_terms=text_typed_terms, gpt_config=gpt_config)
	logging.info("ChatGPT produced %d concept/entity links.", len(mapping_payload.get("links", [])))

	strict_relations = {"equivalentClass", "equivalentProperty", "sameAs"}
	default_relations = {"equivalentClass", "equivalentProperty", "sameAs", "closeMatch"}
	active_relations = strict_relations if strict_links_only else default_relations

	rewrite_mapping = build_rewrite_mapping(
		mapping_payload,
		min_confidence=min_confidence,
		allowed_relations=active_relations,
	)
	logging.info("Using %d high-confidence links for triple rewriting.", len(rewrite_mapping))

	exported_links = filter_links(
		mapping_payload,
		allowed_relations=active_relations,
		min_confidence=min_confidence,
	)

	mapped_image_body = apply_term_mapping(image_parts.body_lines, rewrite_mapping)
	merged_prefixes = text_parts.prefixes + [p for p in image_parts.prefixes if p not in text_parts.prefixes]
	merged_body = text_parts.body_lines + mapped_image_body

	write_merged_ttl(output_file=output_file, prefixes=merged_prefixes, body_lines=merged_body)

	mapping_output.parent.mkdir(parents=True, exist_ok=True)
	with mapping_output.open("w", encoding="utf-8") as f:
		json.dump(
			{
				"link_count": len(exported_links),
				"strict_links_only": strict_links_only,
				"allowed_relations": sorted(active_relations),
				"min_confidence": min_confidence,
				"rewrite_mapping": rewrite_mapping,
				"links": exported_links,
			},
			f,
			indent=2,
		)
	logging.info("Saved term mapping JSON: %s", mapping_output)


def main() -> None:
	parser = argparse.ArgumentParser(description="Merge RDF files using ChatGPT ontology term mapping.")
	parser.add_argument(
		"--text-rdf-dir",
		type=Path,
		default=Path("rdf_file/text_rdf_files"),
		help="Directory containing text RDF files like 21_output.json.ttl",
	)
	parser.add_argument(
		"--image-rdf-file",
		type=Path,
		default=Path("image_rdf_files/19.tif.ttl"),
		help="Image RDF Turtle file to map and merge",
	)
	parser.add_argument(
		"--start",
		type=int,
		default=21,
		help="Start index for text RDF files (default: 21)",
	)
	parser.add_argument(
		"--end",
		type=int,
		default=25,
		help="End index for text RDF files (default: 25)",
	)
	parser.add_argument(
		"--gpt-config-file",
		type=Path,
		default=Path("api_keys/gpt_information_sample.json"),
		help="GPT config JSON with API URL, model, and openai_api_key",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path("rdf_file/merged/mapped_merged_19_with_21_25.ttl"),
		help="Output Turtle file path",
	)
	parser.add_argument(
		"--mapping-output",
		type=Path,
		default=Path("rdf_file/merged/mapping_19_to_21_25.json"),
		help="Path to save ChatGPT term mapping JSON",
	)
	parser.add_argument(
		"--min-confidence",
		type=float,
		default=0.65,
		help="Minimum confidence required to apply source->target term rewriting",
	)
	parser.add_argument(
		"--strict-links-only",
		action="store_true",
		help="Keep only equivalentClass/equivalentProperty/sameAs links and drop weaker links",
	)
	args = parser.parse_args()

	text_files = build_text_rdf_paths(args.text_rdf_dir, args.start, args.end)
	merge_with_gpt_mapping(
		text_files=text_files,
		image_file=args.image_rdf_file,
		gpt_config_file=args.gpt_config_file,
		output_file=args.output,
		mapping_output=args.mapping_output,
		min_confidence=args.min_confidence,
		strict_links_only=args.strict_links_only,
	)


if __name__ == "__main__":
	main()

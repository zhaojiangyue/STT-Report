import os
import json
from google.genai import types

from stt.utils import read_json, write_json


def detect_content_type(client, model_id, generator, media_file):
    prompt = (
        "Classify the content type of this audio. "
        "Choose one of: lecture, interview, news, tutorial, podcast, meeting, other. "
        "Return JSON: {\"type\": \"...\", \"reason\": \"...\"}"
    )
    response = generator(
        client,
        model_id,
        contents=[media_file, prompt],
        config=types.GenerateContentConfig(temperature=0.2),
        message="Detecting Content Type",
    )
    return response.text


def extract_key_quotes(client, model_id, generator, media_file, lang):
    prompt = (
        f"Extract 5-8 memorable quotes with timestamps in [{lang}] language. "
        "Return Markdown list with [MM:SS] and the quote."
    )
    response = generator(
        client,
        model_id,
        contents=[media_file, prompt],
        config=types.GenerateContentConfig(temperature=0.3),
        message="Extracting Key Quotes",
    )
    return response.text


def fact_check_flags(client, model_id, generator, media_file, lang):
    prompt = (
        f"List claims that may need verification in {lang}. "
        "Return a bullet list of claims that should be fact-checked."
    )
    response = generator(
        client,
        model_id,
        contents=[media_file, prompt],
        config=types.GenerateContentConfig(temperature=0.2),
        message="Fact Check Flags",
    )
    return response.text


def follow_up_questions(client, model_id, generator, media_file, lang):
    prompt = f"Generate 5-7 follow-up questions this content raises in {lang}."
    response = generator(
        client,
        model_id,
        contents=[media_file, prompt],
        config=types.GenerateContentConfig(temperature=0.4),
        message="Follow-up Questions",
    )
    return response.text


def related_content(client, model_id, generator, media_file, lang, history_titles):
    prompt = (
        f"Suggest 3-5 related content items in {lang}. "
        "If relevant, use these previously processed titles: "
        + ", ".join(history_titles[:20])
    )
    response = generator(
        client,
        model_id,
        contents=[media_file, prompt],
        config=types.GenerateContentConfig(temperature=0.4),
        message="Related Content",
    )
    return response.text


def update_knowledge_graph(graph_path, doc_id, title, entities, topics):
    graph = read_json(graph_path, default={"nodes": [], "edges": []})
    node = {"id": doc_id, "label": title, "type": "document", "topics": topics, "entities": entities}
    graph["nodes"].append(node)
    for ent in entities:
        ent_id = f"entity:{ent}"
        if not any(n["id"] == ent_id for n in graph["nodes"]):
            graph["nodes"].append({"id": ent_id, "label": ent, "type": "entity"})
        graph["edges"].append({"from": doc_id, "to": ent_id, "type": "mentions"})
    write_json(graph_path, graph)


def extract_entities(client, model_id, generator, media_file):
    prompt = (
        "Extract key entities and topics. "
        "Return JSON: {\"entities\": [..], \"topics\": [..]}."
    )
    response = generator(
        client,
        model_id,
        contents=[media_file, prompt],
        config=types.GenerateContentConfig(temperature=0.2),
        message="Extracting Entities",
    )
    return response.text

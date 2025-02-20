import logging
import re
from collections import defaultdict
from typing import List

import nltk
import spacy
import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from nltk.tokenize import sent_tokenize
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nltk.download("punkt")
nltk.download("punkt_tab")

# Load NLP models
try:
    logger.info("Loading NLP models...")
    nlp = spacy.load("en_core_web_sm")
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    sentiment_analyzer = pipeline("sentiment-analysis")
    logger.info("All NLP models loaded successfully.")
except Exception as e:
    logger.error(f"Error loading NLP models: {e}")
    raise

# Configurations
try:
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    logger.info("Loaded configuration from config.yaml.")
except FileNotFoundError:
    logger.error("config.yaml not found.")
    raise
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    raise

SUMMARIZATION_MAX_LENGTH = config["summarization"]["max_length"]
SUMMARIZATION_MIN_LENGTH = config["summarization"]["min_length"]
CHUNK_SIZE = config["summarization"]["chunk_size"]


# Named Entity Extraction
def extract_entities(text: str):
    doc = nlp(text)
    entities = defaultdict(set)
    for ent in doc.ents:
        entities[ent.label_].add(ent.text)
    return {label: list(names) for label, names in entities.items()}


# Extract topics using TF-IDF
def extract_topics(text: str, top_n: int = 5):
    sentences = sent_tokenize(text)
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(sentences)
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.sum(axis=0).A1
    topic_scores = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
    return [topic for topic, _ in topic_scores[:top_n]]


# Chunk text for summarization
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current_chunk = [], ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


# Generate summary
def generate_summary(text: str):
    chunks = chunk_text(text)
    summaries = []

    for chunk in chunks:
        try:
            summary = summarizer(
                chunk,
                max_length=SUMMARIZATION_MAX_LENGTH,
                min_length=SUMMARIZATION_MIN_LENGTH,
                do_sample=False,
            )[0]["summary_text"]
            summaries.append(summary)
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            summaries.append("[Summary unavailable]")

    return " ".join(summaries)


@app.post("/extract_metadata")
async def extract_metadata(files: List[UploadFile] = File(...)):
    metadata = {}

    for file in files:
        try:
            content = await file.read()
            text = content.decode("utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error reading file {file.filename}: {e}"
            )

        metadata[file.filename] = {
            "entities": extract_entities(text),
            "topics": extract_topics(text),
        }

    return {"metadata": metadata}


@app.post("/query")
async def query_meeting_minutes(
    files: List[UploadFile] = File(...),
    entity: str = None,
    topic: str = None,
    summarize: bool = False,
):
    results = {}

    for file in files:
        try:
            content = await file.read()
            text = content.decode("utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error reading file {file.filename}: {e}"
            )

        entities = extract_entities(text)
        topics = extract_topics(text)
        summary = generate_summary(text) if summarize else None

        filtered_sentences = [
            sent
            for sent in sent_tokenize(text)
            if (entity and entity in sent) or (topic and topic in sent)
        ]

        results[file.filename] = {
            "filtered_sentences": filtered_sentences,
            "summary": summary,
        }

    return {"results": results}

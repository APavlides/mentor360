import re
from collections import Counter, defaultdict

import nltk
import spacy
import yaml
from fastapi import FastAPI, HTTPException
from nltk.tokenize import sent_tokenize
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline

nltk.download("punkt")

# Load NLP models
nlp = spacy.load("en_core_web_sm")
summarizer = pipeline("summarization")
sentiment_analyzer = pipeline("sentiment-analysis")

app = FastAPI()

# Configurations
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

SUMMARIZATION_MAX_LENGTH = config["summarization"]["max_length"]
SUMMARIZATION_MIN_LENGTH = config["summarization"]["min_length"]
CHUNK_SIZE = config["summarization"]["chunk_size"]


# Input model
class MeetingMinutesRequest(BaseModel):
    text: str
    entity: str = None  # Optional entity query


# Named Entity Extraction
def extract_entities(text: str):
    doc = nlp(text)
    entities = defaultdict(list)

    for ent in doc.ents:
        entities[ent.label_].append(ent.text)

    return {label: list(set(names)) for label, names in entities.items()}


# Extract topics using TF-IDF
def extract_topics(text: str, top_n: int = 5):
    sentences = sent_tokenize(text)
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(sentences)
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.sum(axis=0).A1
    topic_scores = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
    return [topic for topic, _ in topic_scores[:top_n]]


# Extract key events (MP contributions and timestamps)
def extract_key_events(text: str):
    doc = nlp(text)
    key_events = []

    for sent in doc.sents:
        entities = [ent.text for ent in sent.ents if ent.label_ in ["PERSON", "ORG"]]
        if entities:
            key_events.append({"sentence": sent.text, "entities": entities})

    return key_events


# Sentiment Analysis
def analyze_sentiment(text: str):
    sentences = sent_tokenize(text)
    sentiments = [sentiment_analyzer(sentence)[0] for sentence in sentences]
    sentiment_counts = Counter([s["label"] for s in sentiments])
    return dict(sentiment_counts)


# Summarization with chunking
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
            summaries.append("[Summary unavailable due to error]")
            print(f"Summarization error: {e}")

    return " ".join(summaries)


# Simple Regex/Heuristic Evaluation
def regex_based_extraction(text: str):
    regex_patterns = {
        "PERSON": r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)*",  # Capitalized names
        "DATE": r"\b\d{1,2}\s[A-Za-z]+\s\d{4}\b",  # e.g., 12 March 2023
        "ORG": r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)*",  # Simple org name heuristic
    }

    extracted = {
        label: re.findall(pattern, text) for label, pattern in regex_patterns.items()
    }
    return extracted


@app.post("/summarize")
async def summarize_text(request: MeetingMinutesRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Meeting text is required")
    return {"summary": generate_summary(request.text)}


@app.post("/extract_entities")
async def extract_entities_endpoint(request: MeetingMinutesRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Meeting text is required")
    return {"entities": extract_entities(request.text)}


@app.post("/extract_topics")
async def extract_topics_endpoint(request: MeetingMinutesRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Meeting text is required")
    return {"topics": extract_topics(request.text)}


@app.post("/analyze_sentiment")
async def analyze_sentiment_endpoint(request: MeetingMinutesRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Meeting text is required")
    return {"sentiment_analysis": analyze_sentiment(request.text)}


@app.post("/analyze_minutes")
async def analyze_minutes(request: MeetingMinutesRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Meeting text is required")

    summary = generate_summary(request.text)
    entities = extract_entities(request.text)
    heuristic_entities = regex_based_extraction(request.text)
    topics = extract_topics(request.text)
    key_events = extract_key_events(request.text)
    sentiment_analysis = analyze_sentiment(request.text)

    relevant_contributions = []
    if request.entity:
        relevant_contributions = [
            sent for sent in sent_tokenize(request.text) if request.entity in sent
        ]

    evaluation = {
        label: set(entities.get(label, [])) & set(heuristic_entities.get(label, []))
        for label in heuristic_entities
    }

    return {
        "summary": summary,
        "entities": entities,
        "topics": topics,
        "key_events": key_events,
        "sentiment_analysis": sentiment_analysis,
        "relevant_contributions": relevant_contributions,
        "heuristic_entities": heuristic_entities,
        "evaluation": evaluation,
    }


# TODO:
# Add evaluation as described in test
# Consider using llamaindex with openai API and a prompt template to extract more complicated insights.

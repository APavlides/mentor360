# Parliamentary Meeting Minutes Analysis

## Overview

This FastAPI service queries parliamentary meeting minutes and returns relevant information in a structured format.

## Prerequisites

- Docker
- Docker Compose
- MacOS (ARM64) operating system

## Instructions for how to run the service

### **Quick Start (Recommended)**

If you have Docker Compose installed, simply run:

```sh
docker compose up --build
```

### Manual Steps (If Not Using Docker Compose)

Build the Docker image:

```sh
docker buildx build --platform linux/arm64 --no-cache -t fastapi-parliamentary-meeting-analysis --load .
```

Run the container:

```sh
docker run -p 8000:8000 fastapi-parliamentary-meeting-analysis
```

## API Endpoints and curl Examples

1. Summarize Meeting Minutes \
   Endpoint: POST /summarize \
   Description: Summarizes the given meeting text.

Request Example:

```sh
curl -X POST "http://localhost:8000/summarize" \
     -H "Content-Type: application/json" \
     -d '{"text": "This is a sample meeting transcript discussing key points on AI regulation and ethical concerns."}'

```

```json
{
  "summary": "The meeting discussed key points on AI regulation and ethical concerns."
}
```

2. Extract Named Entities \
   Endpoint: POST /extract_entities \
   Description: Extracts named entities (persons, organizations, dates, etc.) from the text.

Request Example:

```sh
curl -X POST "http://127.0.0.1:8000/extract_entities" \
     -H "Content-Type: application/json" \
     -d '{"text": "John Doe from OpenAI discussed new advancements in AI safety on March 12, 2023."}'

```

```json
{
  "entities": {
    "PERSON": ["John Doe"],
    "ORG": ["OpenAI"],
    "DATE": ["March 12, 2023"]
  }
}
```

3. Extract Key Topics \
   Endpoint: POST /extract_topics \
   Description: Identifies key topics from the meeting transcript using TF-IDF.

Request Example:

```sh
curl -X POST "http://127.0.0.1:8000/extract_topics" \
     -H "Content-Type: application/json" \
     -d '{"text": "The discussion focused on AI safety, ethics, and regulations."}'

```

```json
{
  "topics": ["AI", "safety", "ethics", "regulations"]
}
```

4. Analyze Sentiment \
   Endpoint: POST /analyze_sentiment \
   Description: Analyzes sentiment in the meeting minutes and provides a count of positive, negative, and neutral sentiments.

Request Example:

```sh
curl -X POST "http://127.0.0.1:8000/analyze_sentiment" \
     -H "Content-Type: application/json" \
     -d '{"text": "I am happy with the AI progress. However, some concerns remain about bias."}'
```

```json
{
  "sentiment_analysis": {
    "POSITIVE": 1,
    "NEGATIVE": 1
  }
}
```

5. Analyze Meeting Minutes (Full Analysis) \
   Endpoint: POST /analyze_minutes \
   Description: Provides a full analysis including summary, topics, sentiment, key events, and entity extraction.

Request Example:

```sh
curl -X POST "http://127.0.0.1:8000/analyze_minutes" \
     -H "Content-Type: application/json" \
     -d '{"text": "Dr. Smith from MIT discussed AI ethics and safety at the UN conference.", "entity": "Dr. Smith"}'
```

```json
{
  "summary": "Dr. Smith from MIT discussed AI ethics and safety.",
  "entities": {
    "PERSON": ["Dr. Smith"],
    "ORG": ["MIT", "UN"]
  },
  "topics": ["AI", "ethics", "safety"],
  "key_events": [
    {
      "sentence": "Dr. Smith from MIT discussed AI ethics and safety at the UN conference.",
      "entities": ["Dr. Smith", "MIT", "UN"]
    }
  ],
  "sentiment_analysis": {
    "NEUTRAL": 1
  },
  "relevant_contributions": [
    "Dr. Smith from MIT discussed AI ethics and safety at the UN conference."
  ],
  "heuristic_entities": {
    "PERSON": ["Dr. Smith"],
    "ORG": ["MIT", "UN"],
    "DATE": []
  },
  "evaluation": {
    "PERSON": ["Dr. Smith"],
    "ORG": ["MIT", "UN"]
  }
}
```

## Evaluation

In the absence of a groundtruth dataset, there are a few options depending on what you want to measure. Here is a table summarising the possibilities.

| Aspect         | Method                                                           |
| -------------- | ---------------------------------------------------------------- |
| Quality        | LLM-as-a-judge, human ratings, embedding similarity              |
| Consistency    | Repeated prompts, variance analysis                              |
| Safety         | Toxicity/bias detection (Perspective API, OpenAI moderation API) |
| Robustness     | Edge case testing, adversarial prompts                           |
| Real-world Use | User feedback, logging & analytics                               |

I will focus on Quality (as that is often what people mean vy evaluation), and consistency, since it is useful to know if API responses are consistent for production use.

There was a recent paper on LLM-as-Judge which looks really promising [A Survey on LLM-as-a-Judge](https://arxiv.org/pdf/2411.15594}). I can see this being particularly powerful when you need a quick way to test how a cheaper model performs against a more expensive model. This is a real concern in application development since it's cost prohibative to use the best LLMs for many applications.

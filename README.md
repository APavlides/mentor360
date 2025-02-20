# Parliamentary Meeting Minutes Analysis

## Overview

This FastAPI service queries parliamentary meeting minutes and returns relevant information in a structured format. Additionally, it provides functionality for evaluating the relevancy of the extracted sentences through a locally running evaluation script.

## Prerequisites

- Docker
- Docker Compose
- MacOS (ARM64) operating system
- Python 3.9 for running the evaluation locally

## Instructions for How to Run the Service

### **Quick Start (Recommended)**

If you have Docker Compose installed, simply run:

```sh
docker compose up --build
```

This will build the Docker image and start the FastAPI service in a container.

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

### Features

- **Summarization**: Generates a concise summary of the meeting minutes.
- **Entity Extraction**: Identifies named entities (e.g., persons, organizations, dates) in the text.
- **Topic Extraction**: Uses TF-IDF to determine key topics in the meeting minutes.
- **Querying**: Allows users to filter relevant sentences based on a specified entity name or topic.
- **Metadata Extraction**: Retrieves all detected entities and topics from uploaded files.
- **Multiple File Support**: Users can upload multiple `.txt` files in a single request.

## Usage Examples

### Extract Metadata from Multiple Files

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/extract_metadata' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@data/scottish_parliament_report_07_01_25.txt' \
```

### Querying Multiple Files for a Specific Entity (Without Summary)

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/query?entity=Stuart%20Black' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@data/scottish_parliament_report_07_01_25.txt'
```

### Querying Multiple Files for a Specific Topic (With Summary)

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/query?topic=government&summarize=false' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@data/scottish_parliament_report_07_01_25.txt'

```

## Notes

- The API processes `.txt` files only.
- For accurate entity extraction, ensure the text is well-structured.
- Summarization is optional and can be requested by setting `summarize=true`.

## Evaluation

In the absence of a groundtruth dataset, there are a few options depending on what you want to measure. Here is a table summarising the possibilities.

| Aspect         | Method                                                           |
| -------------- | ---------------------------------------------------------------- |
| Quality        | LLM-as-a-judge, human ratings, embedding similarity              |
| Consistency    | Repeated prompts, variance analysis                              |
| Safety         | Toxicity/bias detection (Perspective API, OpenAI moderation API) |
| Robustness     | Edge case testing, adversarial prompts                           |
| Real-world Use | User feedback, logging & analytics                               |

I will focus on Quality (as that is often what people mean by evaluation), and consistency, since it is useful to know if API responses are consistent for production use.

There was a recent paper on LLM-as-Judge which looks really promising [A Survey on LLM-as-a-Judge](https://arxiv.org/pdf/2411.15594}). I can see this being particularly powerful when you need a quick way to test how a cheaper model performs against a more expensive model.

## To Run Evaluation

This is really a demo of how it would work since I don't have enough time to test it fully.

1. Get the service running by following instructions above.
2. I created a virtualenv using pyenv and installed additional packages required for this evaluation (I have highlighted in the requirements.txt which packages are used for evaluation).
3. Run the evalution script as a module with arguments.

```python
python -m src.evaluation.relevancy_evaluation \
  --query "Can you find any sentences that mention Stuart Black?" \
  --entity "Stuart Black" \
  --files \
  "data/scottish_parliament_report_07_01_25.txt" \
  "data/scottish_parliament_report_08_10_24.txt" \
  "data/scottish_parliament_report_10_09_24.txt" \
  "data/scottish_parliament_report_26_06_24.txt"

```

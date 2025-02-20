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

# Parliamentary Meeting Minutes Query API

## Overview

This API processes parliamentary meeting minutes and extracts relevant information based on user queries. It supports summarization, entity extraction, topic extraction, and querying by entity name or topic.

## Features

- **Summarization**: Generates a concise summary of the meeting minutes.
- **Entity Extraction**: Identifies named entities (e.g., persons, organizations, dates) in the text.
- **Topic Extraction**: Uses TF-IDF to determine key topics in the meeting minutes.
- **Querying**: Allows users to filter relevant sentences based on a specified entity name or topic.

## Installation

### Prerequisites

- Python 3.8+
- `pip install -r requirements.txt`

## Running the API

```sh
uvicorn main:app --reload
```

## API Endpoints

# Parliamentary Meeting Minutes Query API

## Overview

This API processes parliamentary meeting minutes and extracts relevant information based on user queries. It supports summarization, entity extraction, topic extraction, and querying by entity name or topic.

## Features

- **Summarization (Optional)**: Generates a concise summary of the meeting minutes if requested.
- **Entity Extraction**: Identifies named entities (e.g., persons, organizations, dates) in the text.
- **Topic Extraction**: Uses TF-IDF to determine key topics in the meeting minutes.
- **Querying**: Allows users to filter relevant sentences based on a specified entity name or topic.
- **Metadata Extraction**: Retrieves all detected entities and topics from uploaded files.
- **Multiple File Support**: Users can upload multiple `.txt` files in a single request.

## Installation

### Prerequisites

- Python 3.8+
- `pip install -r requirements.txt`

## Running the API

```sh
uvicorn main:app --reload
```

## API Endpoints

### 1. Upload and Extract Metadata (Entities & Topics)

**Endpoint:**

```
POST /extract_metadata
```

**Request:**

- Upload one or more `.txt` files containing meeting minutes.

**Response:**

```json
{
  "metadata": {
    "file1.txt": {
      "entities": { "PERSON": ["John Doe"], "ORG": ["Parliament"] },
      "topics": ["economy", "policy"]
    },
    "file2.txt": {
      "entities": { "PERSON": ["Jane Smith"], "ORG": ["Government"] },
      "topics": ["healthcare", "reform"]
    }
  }
}
```

### 2. Query Meeting Minutes by Entity or Topic

**Endpoint:**

```
POST /query
```

**Request:**

- Upload one or more `.txt` files.
- (Optional) Provide an entity name or topic as query parameters.
- (Optional) Include `summarize=true` in the query to enable summarization.

**Response:**

```json
{
  "results": {
    "file1.txt": {
      "entities": { "PERSON": ["John Doe"], "ORG": ["Parliament"] },
      "topics": ["economy", "policy"],
      "filtered_sentences": ["John Doe discussed the economy."],
      "summary": "(If requested) Summary of file1.txt"
    },
    "file2.txt": {
      "entities": { "PERSON": ["Jane Smith"], "ORG": ["Government"] },
      "topics": ["healthcare", "reform"],
      "filtered_sentences": ["Jane Smith debated healthcare reforms."],
      "summary": "(If requested) Summary of file2.txt"
    }
  }
}
```

## Usage Examples

### Extract Metadata from Multiple Files with cURL

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/extract_metadata' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@data/scottish_parliament_report_07_01_25.txt' \
```

### Querying Multiple Files for a Specific Entity with cURL (Without Summary)

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/query?entity=Stuart%20Black' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@data/scottish_parliament_report_07_01_25.txt'
```

### Querying Multiple Files for a Specific Topic with cURL (With Summary)

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

## License

MIT License.

## Notes

- The API processes `.txt` files only.
- For accurate entity extraction, ensure the text is well-structured.

## License

MIT License.

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

# Parliamentary Meeting Minutes Analysis

## Overview

This FastAPI service queries parliamentary meeting minutes and returns relevant information in a structured format. Additionally, it provides functionality for evaluating the relevancy of the extracted sentences through a locally running evaluation script.

## Prerequisites

- Docker
- Docker Compose
- MacOS (ARM64) operating system
- Python 3.9.19 for running the evaluation locally

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

- **Querying**: Allows users to filter relevant sentences based on a specified entity name or topic. Optionally, it can also provide a summary of the text.
- **Metadata Extraction**: Retrieves all detected entities and topics from uploaded files.

## Usage Examples

### Extract Metadata from Files

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/extract_metadata' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@data/scottish_parliament_report_07_01_25.txt'
```

Output (Snippet due to length):

```json
{
  "metadata": {
    "scottish_parliament_report_07_01_25.txt": {
      "entities": {
        "PERSON": [
          "Fiona Diggle",
          "Boyle",
          "Ross Greer’s",
          "Mary Morgan",
          "Liz",
          "Craig Hoy",
          "Fiona Diggle:",
          "Ms Smith",
          "Garry McEwan"
        ]
      }
    }
  }
}
```

### Querying Files for a Specific Entity (Without Summary)

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/query?entity=Stuart%20Black' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@data/scottish_parliament_report_07_01_25.txt'
```

Output:

```json
{
  "results": {
    "scottish_parliament_report_07_01_25.txt": {
      "filtered_sentences": [
        "One thing that Stuart Black and I very much agree on is that the rural economies have incredible unharnessed potential that can be engaged and focused on in the north and the south of Scotland."
      ],
      "summary": null
    }
  }
}
```

### Querying Files for a Specific Topic (With Summary)

The summary api can take a while on longer transcripts, so the example here uses the shortest transcript provided.

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/query?topic=government&summarize=true' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@data/scottish_parliament_report_26_06_24.txt'

```

Output

```json
{
  "results": {
    "scottish_parliament_report_26_06_24.txt": {
      "filtered_sentences": [
        "In the public sector, that might be local government or NatureScot.",
        "The Deputy First Minister and Cabinet Secretary for Economy and Gaelic (Kate Forbes):\r\nFurthermore, the funds cannot be used for core public services, so they cannot be used—as some have suggested—to mitigate the impact of austerity on our national health service, on local government or on core infrastructure.",
        "We worked with the European Commission and that was resolved, but from our partners’ perspective—from a charities perspective and a local government perspective—there was never any pause.",
        "Most of the projects that are being funded by European funding are delivered by third sector organisations, local government and organisations such as NatureScot."
      ],
      "summary": " The Deputy First Minister will take questions at the end of her statement...."
    }
  }
}
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

I will focus on LLM-as-judge and create a demo of how this might work.
There was a recent paper on LLM-as-Judge which looks really promising [A Survey on LLM-as-a-Judge](https://arxiv.org/pdf/2411.15594}).

## To Run Evaluation

This is really a demo of how it would work since there isn't time to fully flesh it out. This could be expanded to all api endpoints, but this only looks at an entry search. Essentially, you use a powerful LLM such as gpt-4 to do the same queries of the data you are interested in and then you compare the API service outputs with that of the LLM. This could be useful in various situations especially when using "inferior" or cheaper approaches to certain tasks.

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

Output:

```bash
INFO:__main__:Relevancy Score: 1.0
INFO:__main__:Passing: True
INFO:__main__:Feedback: YES
```

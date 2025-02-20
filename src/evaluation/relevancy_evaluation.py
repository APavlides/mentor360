import argparse
import logging
import os
import re
from contextlib import ExitStack

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.evaluation import RelevancyEvaluator
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from ..app.main import app

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the OpenAI model for LlamaIndex
llm = OpenAI(model="gpt-4-turbo", temperature=0.0)

# Initialize the OpenAI embedding model for indexing
embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

# Load documents for LlamaIndex indexing
documents_dir = os.path.join(os.getcwd(), "data")
documents = SimpleDirectoryReader(documents_dir).load_data()
index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
query_engine = index.as_query_engine(llm=llm)

# Define the evaluator from LlamaIndex
evaluator = RelevancyEvaluator(llm=llm)

# Initialize the FastAPI test client
client = TestClient(app)


def evaluate_relevancy(query: str, entity: str, file_paths: list):
    """
    Compare the sentences containing the entity from FastAPI with those from LlamaIndex.
    """
    # Ensure all files exist
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: File not found at {file_path}")

    # Prepare request parameters
    url = "/query"
    headers = {"Accept": "application/json"}
    params = {"entity": entity}

    try:
        with ExitStack() as stack:
            files = [
                (
                    "files",
                    (
                        os.path.basename(file_path),
                        stack.enter_context(open(file_path, "rb")),
                        "text/plain",
                    ),
                )
                for file_path in file_paths
            ]

            # Make the request to the FastAPI endpoint
            response = client.post(url, params=params, headers=headers, files=files)

            response.raise_for_status()

            print(f"Response Status: {response.status_code}")

            response_data = response.json()
            print(f"Response JSON: {response_data}")

            # Extract sentences from the response
            fastapi_sentences = {
                os.path.basename(file_path): response_data.get("results", {})
                .get(os.path.basename(file_path), {})
                .get("filtered_sentences", [])
                for file_path in file_paths
            }

    except Exception as e:
        print(f"Error occurred: {e}")
        fastapi_sentences = {}

    # Query LlamaIndex for sentences containing the same entity
    # query_str = f"Can you find any sentences that mention {entity}"
    llama_index_response = query_engine.query(query)

    # Split by punctuation marks instead of new lines
    llama_index_sentences = re.split(r"(?<=[.!?])\s+", llama_index_response.response)
    logger.info(f"LlamaIndex retrieved sentences: {llama_index_sentences}")

    # Compare FastAPI response with LlamaIndex response using the evaluator
    eval_result = evaluator.evaluate(
        query=query,
        response=" ".join(
            [" ".join(sentences) for sentences in fastapi_sentences.values()]
        ),
        contexts=llama_index_sentences,
    )
    return eval_result


def main():
    """
    Main function to parse command-line arguments and run the evaluation.
    """
    parser = argparse.ArgumentParser(
        description="Evaluate relevancy of entity mentions in text files."
    )
    parser.add_argument("--query", type=str, required=True, help="Query to search for.")
    parser.add_argument(
        "--entity", type=str, required=True, help="Entity to search in files."
    )
    parser.add_argument(
        "--files",
        type=str,
        nargs="+",
        required=True,
        help="List of file paths to search.",
    )

    args = parser.parse_args()

    eval_result = evaluate_relevancy(args.query, args.entity, args.files)

    logger.info(f"Relevancy Score: {eval_result.score}")
    logger.info(f"Passing: {eval_result.passing}")
    logger.info(f"Feedback: {eval_result.feedback}")


if __name__ == "__main__":
    main()

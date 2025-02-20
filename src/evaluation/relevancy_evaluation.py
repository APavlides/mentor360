import argparse
import logging
import os
from contextlib import ExitStack

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.evaluation import RelevancyEvaluator
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# from src.app.main import app  # Adjust import if needed
from ..app.main import app

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the OpenAI model for LlamaIndex
llm = OpenAI(model="gpt-3.5-turbo", temperature=0.0)

# Initialize the OpenAI embedding model for indexing
embed_model = OpenAIEmbedding(model="text-embedding-3-small")

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

    # Open multiple files and send them in the request
    try:
        with ExitStack() as stack:  # Ensures that files are properly closed after use
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

            # Debug: Print files to check correctness
            print(f"Sending files: {files}")

            # Make the request to the FastAPI endpoint
            response = client.post(url, params=params, headers=headers, files=files)

            # Check if the response was successful
            response.raise_for_status()

            # Debug: Print response status
            print(f"Response Status: {response.status_code}")

            # Debug: Print response content
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
    llama_index_response = query_engine.query(
        f"What sentences contain the entity {entity}?"
    )
    llama_index_sentences = llama_index_response.response.split(
        "\n"
    )  # Assuming sentences are split by new lines
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

    # Perform the relevancy evaluation
    eval_result = evaluate_relevancy(args.query, args.entity, args.files)

    # Print the evaluation results
    logger.info(f"Relevancy Score: {eval_result.score}")
    logger.info(f"Passing: {eval_result.passing}")
    logger.info(f"Feedback: {eval_result.feedback}")


if __name__ == "__main__":
    main()

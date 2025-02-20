import logging
import os

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.evaluation import RelevancyEvaluator
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# from src.app.main import app  # Assuming your FastAPI app is in src/app/main.py
from ..app.main import app

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")

# Ensure the key is set correctly
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the OpenAI model for LlamaIndex
# llm = OpenAI(model="gpt-4", temperature=0.0)
llm = OpenAI(model="gpt-3.5-turbo", temperature=0.0)


# # Load documents for LlamaIndex indexing
documents_dir = os.path.join(os.getcwd(), "data")
# documents = SimpleDirectoryReader(documents_dir).load_data()
# index = VectorStoreIndex.from_documents(documents)
# query_engine = index.as_query_engine()

# Initialize the OpenAI embedding model for indexing
embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# Load documents for LlamaIndex indexing
documents = SimpleDirectoryReader(documents_dir).load_data()
index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
query_engine = index.as_query_engine(llm=llm)

# Define the evaluator from LlamaIndex
evaluator = RelevancyEvaluator(llm=llm)

# Initialize the FastAPI test client
client = TestClient(app)


def evaluate_relevancy(query: str, entity: str):
    """
    Compare the sentences containing the entity from FastAPI with those from LlamaIndex.
    """

    # Define the directory containing the files
    data_dir = "data"  # Update this if needed
    file_names = ["scottish_parliament_report_07_01_25.txt", 
                "file2.txt", 
                "file3.txt", 
                "file4.txt"]  # Replace with actual filenames

    # Construct full file paths
    file_paths = [os.path.join(data_dir, file_name) for file_name in file_names]

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
        with ExitStack() as stack:  # Ensures files are properly closed
            files = {
                "files": [(file_name, stack.enter_context(open(file_path, "rb")), "text/plain")]
                for file_name, file_path in zip(file_names, file_paths)
            }

            # Make the request
            response = client.post(url, params=params, headers=headers, files=files)

        # Check if the response was successful
        response.raise_for_status()

        # Debug: Print response status
        print(f"Response Status: {response.status_code}")

        # Debug: Print response content
        response_data = response.json()
        print(f"Response JSON: {response_data}")

        # Extract sentences for each file
        fastapi_sentences = {
            file_name: response_data.get("results", {}).get(file_name, {}).get("filtered_sentences", [])
            for file_name in file_names
        }

    except Exception as e:
        print(f"Error occurred: {e}")
        fastapi_sentences = {}

    # Debug: Print extracted sentences per file
    for file, sentences in fastapi_sentences.items():
        print(f"Extracted Sentences from {file}: {sentences}")

    except Exception as e:
        print(f"Error occurred: {e}")
        fastapi_sentences = []  # Ensure variable is defined even in case of failure

    # Debug: Print extracted sentences
    print(f"Extracted Sentences: {fastapi_sentences}")

    logger.info(f"FastAPI retrieved sentences: {fastapi_sentences}")

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
        response=" ".join(fastapi_sentences),
        contexts=llama_index_sentences,
    )
    return eval_result


def main():
    # Define the query and entity for evaluation
    query = "What sentences contain the entity Stuart Black?"
    entity = "Stuart Black"

    # Perform the relevancy evaluation
    eval_result = evaluate_relevancy(query, entity)

    # Print the evaluation results
    logger.info(f"Relevancy Score: {eval_result.score}")
    logger.info(f"Passing: {eval_result.passing}")
    logger.info(f"Feedback: {eval_result.feedback}")


if __name__ == "__main__":
    main()

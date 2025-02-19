For consistency testing, here’s an approach:
Repeated Prompting: Send the same prompt multiple times to the API.
Variance Analysis: Compare outputs using similarity metrics (e.g., embedding similarity, token overlap, or exact match rates).
Automated Scoring: Use a threshold to flag responses that vary too much.
I’ll generate initial code for both quality evaluation (LLM-as-a-Judge) and consistency testing in the evaluation folder.


import numpy as np
import requests

# consistency.py - API response consistency testing
from sentence_transformers import SentenceTransformer, util


def test_consistency(
    api_url,
    prompt,
    num_retries=5,
    model_name="all-MiniLM-L6-v2",
    similarity_threshold=0.95,
):
    """
    Sends the same prompt multiple times and measures response consistency.

    Args:
        api_url (str): The API endpoint to test.
        prompt (str): The input prompt.
        num_retries (int): Number of times to send the same prompt.
        model_name (str): Embedding model for similarity.
        similarity_threshold (float): Minimum cosine similarity to be considered consistent.

    Returns:
        dict: Average similarity and consistency flag.
    """
    model = SentenceTransformer(model_name)
    responses = []

    for _ in range(num_retries):
        response = requests.post(api_url, json={"prompt": prompt}).json()["response"]
        responses.append(response)

    embeddings = model.encode(responses, convert_to_tensor=True)
    similarities = [
        util.pytorch_cos_sim(embeddings[i], embeddings[j]).item()
        for i in range(len(responses))
        for j in range(i + 1, len(responses))
    ]

    avg_similarity = np.mean(similarities)
    is_consistent = avg_similarity >= similarity_threshold

    return {"average_similarity": avg_similarity, "consistent": is_consistent}

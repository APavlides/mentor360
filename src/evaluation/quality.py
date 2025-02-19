# quality.py - LLM-as-a-Judge evaluation using LlamaIndex
from llama_index.evaluation import LLMEvaluator
from llama_index.llms import OpenAI  # Or another LLM provider


def evaluate_quality(model_outputs, reference_outputs, judge_model="gpt-4-turbo"):
    """
    Compare model outputs to reference outputs using LLM-as-a-Judge.

    Args:
        model_outputs (list[str]): The responses from the model being tested.
        reference_outputs (list[str]): The expected or ideal responses.
        judge_model (str): The LLM to use as the judge.

    Returns:
        list[dict]: A list of evaluation scores and explanations.
    """
    llm = OpenAI(model=judge_model)
    evaluator = LLMEvaluator(llm)

    results = []
    for model_resp, ref_resp in zip(model_outputs, reference_outputs):
        score = evaluator.evaluate(model_resp, ref_resp)
        results.append(score)

    return results

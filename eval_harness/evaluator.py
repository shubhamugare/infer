#!/usr/bin/env python3
"""
Evaluator script to run LLM on eval data and compute metrics.

Usage:
    python evaluator.py --data data/pulse_all_examples.jsonl \
                        --model gpt-4 \
                        --output results/gpt4/pulse_results.jsonl
"""

import argparse
import json
import os
import re
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class EvalMetrics:
    """Evaluation metrics for bug detection."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    correct_negatives: int = 0
    total_examples: int = 0

    @property
    def precision(self) -> float:
        """Precision = TP / (TP + FP)"""
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        """Recall = TP / (TP + FN)"""
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def f1_score(self) -> float:
        """F1 = 2 * P * R / (P + R)"""
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def accuracy(self) -> float:
        """Accuracy = (TP + TN) / Total"""
        return (self.true_positives + self.correct_negatives) / self.total_examples \
            if self.total_examples > 0 else 0.0


def load_system_prompt(path: str = "system_prompt.txt") -> str:
    """Load system prompt from file."""
    with open(path, 'r') as f:
        return f.read()


def extract_json_from_response(response: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response.
    Handles responses with thinking + JSON in markdown code blocks.

    Expected format:
    Some thinking...
    ```json
    {"has_bug": true, ...}
    ```
    """
    # Try to find JSON in markdown code block
    json_pattern = r'```json\s*\n(.*?)\n```'
    match = re.search(json_pattern, response, re.DOTALL)

    if match:
        json_str = match.group(1)
        return json.loads(json_str)

    # Fallback: try to parse the whole response as JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Last resort: find first { ... } block
        brace_pattern = r'\{[^}]*"has_bug"[^}]*\}'
        match = re.search(brace_pattern, response, re.DOTALL)
        if match:
            return json.loads(match.group(0))

        raise ValueError(f"Could not extract JSON from response: {response[:200]}...")


def construct_prompt(example: Dict[str, Any], include_context: bool = True) -> str:
    """
    Construct prompt for LLM evaluation.

    Args:
        example: Example dict from JSONL
        include_context: Whether to include includes/dependencies
    """
    prompt = "Analyze this C function for bugs:\n\n"

    # Add includes if needed
    if include_context and example['includes']:
        prompt += '\n'.join(example['includes']) + '\n\n'

    # Add function code
    prompt += f"```c\n{example['function_code']}```\n"

    return prompt


def call_llm(system_prompt: str, user_prompt: str, model: str = "gpt-4") -> str:
    """
    Call LLM API. This is a placeholder - implement with your LLM API.

    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        model: Model name

    Returns:
        Raw text response from LLM
    """
    # TODO: Implement actual LLM API call
    # Example with OpenAI:
    # import openai
    # response = openai.ChatCompletion.create(
    #     model=model,
    #     messages=[
    #         {"role": "system", "content": system_prompt},
    #         {"role": "user", "content": user_prompt}
    #     ],
    #     temperature=0.0
    # )
    # return response.choices[0].message.content

    raise NotImplementedError("Implement LLM API call for your provider")


def evaluate_prediction(prediction: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single prediction against ground truth.

    Format:
    prediction = {"has_bug": bool, "bugs": [{"type": str, "line": int, "explanation": str}]}
    ground_truth = {"has_bug": bool, "bugs": [{"bug_type": str, ...}]}

    Returns:
        Dict with evaluation results including match type
    """
    pred_has_bug = prediction.get('has_bug', False)
    gt_has_bug = ground_truth['has_bug']

    result = {
        'predicted_has_bug': pred_has_bug,
        'actual_has_bug': gt_has_bug,
        'match_type': None,
        'matched_bug_types': [],
        'missed_bugs': [],
        'wrong_bug_types': []
    }

    # Case 1: Both agree no bug
    if not pred_has_bug and not gt_has_bug:
        result['match_type'] = 'true_negative'
        return result

    # Case 2: Predicted no bug but there is one
    if not pred_has_bug and gt_has_bug:
        result['match_type'] = 'false_negative'
        result['missed_bugs'] = [bug['bug_type'] for bug in ground_truth['bugs']]
        return result

    # Case 3: Predicted bug but there isn't one
    if pred_has_bug and not gt_has_bug:
        result['match_type'] = 'false_positive'
        pred_bugs = prediction.get('bugs', [])
        result['wrong_bug_types'] = [bug.get('type') for bug in pred_bugs if bug.get('type')]
        return result

    # Case 4: Both agree there's a bug - check if any types match
    pred_bugs = prediction.get('bugs', [])
    pred_types = {bug.get('type') for bug in pred_bugs if bug.get('type')}
    gt_bug_types = {bug['bug_type'] for bug in ground_truth['bugs']}

    # Find matches
    matched_types = pred_types & gt_bug_types

    if matched_types:
        result['match_type'] = 'true_positive'
        result['matched_bug_types'] = list(matched_types)
        result['missed_bugs'] = list(gt_bug_types - matched_types)
        result['wrong_bug_types'] = list(pred_types - matched_types)
    else:
        result['match_type'] = 'false_positive'  # Wrong bug types
        result['wrong_bug_types'] = list(pred_types)
        result['missed_bugs'] = list(gt_bug_types)

    return result


def evaluate_dataset(data_path: str, model: str, output_path: str):
    """
    Evaluate LLM on full dataset.

    Args:
        data_path: Path to JSONL eval data
        model: Model name to use
        output_path: Path to save results
    """
    # Load system prompt
    system_prompt = load_system_prompt()

    # Load examples
    with open(data_path, 'r') as f:
        examples = [json.loads(line) for line in f]

    print(f"Loaded {len(examples)} examples from {data_path}")
    print(f"Using model: {model}")

    # Initialize metrics
    metrics = EvalMetrics()
    metrics.total_examples = len(examples)

    # Results
    results = []

    # Evaluate each example
    for i, example in enumerate(examples, 1):
        print(f"\nEvaluating {i}/{len(examples)}: {example['id']}")

        # Construct prompt
        user_prompt = construct_prompt(example)

        try:
            # Call LLM
            raw_response = call_llm(system_prompt, user_prompt, model)

            # Extract JSON from response (handles thinking + JSON format)
            prediction = extract_json_from_response(raw_response)

            # Evaluate
            eval_result = evaluate_prediction(prediction, example['ground_truth'])

            # Update metrics
            match_type = eval_result['match_type']
            if match_type == 'true_positive':
                metrics.true_positives += 1
            elif match_type == 'false_positive':
                metrics.false_positives += 1
            elif match_type == 'false_negative':
                metrics.false_negatives += 1
            elif match_type == 'true_negative':
                metrics.correct_negatives += 1

            # Store result
            result = {
                'example_id': example['id'],
                'source_file': example['source_file'],
                'original_function_name': example['original_function_name'],
                'raw_response': raw_response,
                'prediction': prediction,
                'ground_truth': example['ground_truth'],
                'evaluation': eval_result,
                'metadata': example['metadata']
            }
            results.append(result)

            # Print summary
            print(f"  Result: {match_type}")
            if eval_result.get('matched_bug_types'):
                print(f"  Matched: {eval_result['matched_bug_types']}")
            if eval_result.get('missed_bugs'):
                print(f"  Missed: {eval_result['missed_bugs']}")
            if eval_result.get('wrong_bug_types'):
                print(f"  Wrong types: {eval_result['wrong_bug_types']}")

        except Exception as e:
            print(f"  Error: {e}")
            result = {
                'example_id': example['id'],
                'source_file': example['source_file'],
                'error': str(e)
            }
            results.append(result)

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')

    # Print final metrics
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total Examples: {metrics.total_examples}")
    print(f"True Positives: {metrics.true_positives}")
    print(f"False Positives: {metrics.false_positives}")
    print(f"False Negatives: {metrics.false_negatives}")
    print(f"True Negatives: {metrics.correct_negatives}")
    print(f"\nPrecision: {metrics.precision:.2%}")
    print(f"Recall: {metrics.recall:.2%}")
    print(f"F1 Score: {metrics.f1_score:.2%}")
    print(f"Accuracy: {metrics.accuracy:.2%}")
    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate LLM on Infer bug detection tasks'
    )
    parser.add_argument(
        '--data',
        required=True,
        help='Path to JSONL eval data file'
    )
    parser.add_argument(
        '--model',
        default='gpt-4',
        help='Model name to use (default: gpt-4)'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to save results JSONL file'
    )

    args = parser.parse_args()

    evaluate_dataset(
        data_path=args.data,
        model=args.model,
        output_path=args.output
    )


if __name__ == '__main__':
    main()

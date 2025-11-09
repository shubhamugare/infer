#!/usr/bin/env python3
"""
Evaluator script to run LLM on eval data and compute metrics.

Usage:
    python evaluator.py --data data/nullptr_basic.jsonl \
                        --model gpt-4 \
                        --output results/gpt4/nullptr_basic_results.jsonl
"""

import argparse
import json
import os
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
    prompt += f"```c\n{example['function_code']}```\n\n"

    # Add task
    prompt += "Return a JSON object with your analysis. Format:\n"
    prompt += '{"has_bug": true|false, "bugs": [{"bug_type": "...", "line": N, "severity": "ERROR", "explanation": "..."}]}\n'

    return prompt


def call_llm(system_prompt: str, user_prompt: str, model: str = "gpt-4") -> Dict[str, Any]:
    """
    Call LLM API. This is a placeholder - implement with your LLM API.

    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        model: Model name

    Returns:
        Parsed JSON response from LLM
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
    # return json.loads(response.choices[0].message.content)

    raise NotImplementedError("Implement LLM API call for your provider")


def evaluate_prediction(prediction: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single prediction against ground truth.

    Returns:
        Dict with evaluation results including match type
    """
    pred_has_bug = prediction.get('has_bug', False)
    gt_has_bug = ground_truth['has_bug']

    result = {
        'predicted_has_bug': pred_has_bug,
        'actual_has_bug': gt_has_bug,
        'match_type': None,
        'matched_bugs': [],
        'missed_bugs': [],
        'false_alarms': []
    }

    # Case 1: Both agree no bug
    if not pred_has_bug and not gt_has_bug:
        result['match_type'] = 'true_negative'
        return result

    # Case 2: Predicted no bug but there is one
    if not pred_has_bug and gt_has_bug:
        result['match_type'] = 'false_negative'
        result['missed_bugs'] = ground_truth['bugs']
        return result

    # Case 3: Predicted bug but there isn't one
    if pred_has_bug and not gt_has_bug:
        result['match_type'] = 'false_positive'
        result['false_alarms'] = prediction.get('bugs', [])
        return result

    # Case 4: Both agree there's a bug - check if types match
    pred_bugs = prediction.get('bugs', [])
    gt_bugs = ground_truth['bugs']

    # Match bugs by type (simple matching)
    pred_types = {bug['bug_type'] for bug in pred_bugs}
    gt_types = {bug['bug_type'] for bug in gt_bugs}

    matched = pred_types & gt_types
    missed = gt_types - pred_types
    false_alarms = pred_types - gt_types

    if matched:
        result['match_type'] = 'true_positive'
        result['matched_bugs'] = list(matched)
    else:
        result['match_type'] = 'false_positive'  # Wrong bug type

    result['missed_bugs'] = [bug for bug in gt_bugs if bug['bug_type'] in missed]
    result['false_alarms'] = [bug for bug in pred_bugs if bug['bug_type'] in false_alarms]

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
            # Call LLM (you need to implement this)
            prediction = call_llm(system_prompt, user_prompt, model)

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
                'original_function_name': example['original_function_name'],
                'prediction': prediction,
                'ground_truth': example['ground_truth'],
                'evaluation': eval_result,
                'metadata': example['metadata']
            }
            results.append(result)

            # Print summary
            print(f"  Result: {match_type}")
            if eval_result['matched_bugs']:
                print(f"  Matched bugs: {eval_result['matched_bugs']}")
            if eval_result['missed_bugs']:
                print(f"  Missed bugs: {[b['bug_type'] for b in eval_result['missed_bugs']]}")
            if eval_result['false_alarms']:
                print(f"  False alarms: {[b['bug_type'] for b in eval_result['false_alarms']]}")

        except Exception as e:
            print(f"  Error: {e}")
            result = {
                'example_id': example['id'],
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

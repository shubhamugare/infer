#!/usr/bin/env python3
"""
Upload Infer Pulse evaluation dataset to Hugging Face Hub.

This script converts the JSONL dataset into Hugging Face datasets format
and uploads it to the Hub with proper metadata and documentation.

Usage:
    # Login first (interactive, saves token)
    huggingface-cli login

    # Or set token as environment variable
    export HF_TOKEN=your_token_here

    # Then upload
    python upload_to_huggingface.py --repo-id your-username/infer-pulse-eval
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Any

try:
    from datasets import Dataset, DatasetDict, Features, Value, Sequence
    from huggingface_hub import HfApi, login
except ImportError:
    print("ERROR: Required packages not installed.")
    print("\nPlease install:")
    print("  pip install datasets huggingface-hub")
    exit(1)


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load JSONL file into list of dicts."""
    examples = []
    with open(file_path, 'r') as f:
        for line in f:
            examples.append(json.loads(line))
    return examples


def convert_to_hf_format(examples: List[Dict[str, Any]]) -> Dict[str, List]:
    """
    Convert JSONL examples to Hugging Face dataset format.

    Flattens nested structures into columns.
    """
    hf_data = {
        'id': [],
        'source_file': [],
        'original_function_name': [],
        'anonymized_function_name': [],
        'function_code': [],
        'includes': [],
        'dependencies': [],

        # Ground truth
        'has_bug': [],
        'bug_types': [],  # List of bug types
        'bug_line_offsets': [],  # List of line offsets
        'bug_absolute_lines': [],  # List of absolute lines
        'bug_severities': [],  # List of severities
        'bug_traces': [],  # List of traces

        # Metadata
        'category': [],
        'difficulty': [],
        'requires_interprocedural': [],
        'start_line': [],
        'end_line': [],
    }

    for ex in examples:
        hf_data['id'].append(ex['id'])
        hf_data['source_file'].append(ex['source_file'])
        hf_data['original_function_name'].append(ex['original_function_name'])
        hf_data['anonymized_function_name'].append(ex['anonymized_function_name'])
        hf_data['function_code'].append(ex['function_code'])
        hf_data['includes'].append(ex['includes'])
        hf_data['dependencies'].append(ex['dependencies'])

        # Ground truth
        gt = ex['ground_truth']
        hf_data['has_bug'].append(gt['has_bug'])

        # Extract bug information into parallel lists
        if gt['bugs']:
            hf_data['bug_types'].append([b['bug_type'] for b in gt['bugs']])
            hf_data['bug_line_offsets'].append([b['line_offset'] for b in gt['bugs']])
            hf_data['bug_absolute_lines'].append([b['absolute_line'] for b in gt['bugs']])
            hf_data['bug_severities'].append([b['severity'] for b in gt['bugs']])
            hf_data['bug_traces'].append([b['trace'] for b in gt['bugs']])
        else:
            hf_data['bug_types'].append([])
            hf_data['bug_line_offsets'].append([])
            hf_data['bug_absolute_lines'].append([])
            hf_data['bug_severities'].append([])
            hf_data['bug_traces'].append([])

        # Metadata
        meta = ex['metadata']
        hf_data['category'].append(meta['category'])
        hf_data['difficulty'].append(meta['difficulty'])
        hf_data['requires_interprocedural'].append(meta['requires_interprocedural'])
        hf_data['start_line'].append(meta['start_line'])
        hf_data['end_line'].append(meta['end_line'])

    return hf_data


def create_dataset_splits(examples: List[Dict[str, Any]]) -> DatasetDict:
    """
    Create dataset splits for Hugging Face.

    Puts all examples in test split (evaluation-only dataset).
    """
    # Convert all examples to HF format
    test_data = convert_to_hf_format(examples)

    # Define features schema
    features = Features({
        'id': Value('string'),
        'source_file': Value('string'),
        'original_function_name': Value('string'),
        'anonymized_function_name': Value('string'),
        'function_code': Value('string'),
        'includes': Sequence(Value('string')),
        'dependencies': Sequence(Value('string')),

        'has_bug': Value('bool'),
        'bug_types': Sequence(Value('string')),
        'bug_line_offsets': Sequence(Value('int32')),
        'bug_absolute_lines': Sequence(Value('int32')),
        'bug_severities': Sequence(Value('string')),
        'bug_traces': Sequence(Value('string')),

        'category': Value('string'),
        'difficulty': Value('string'),
        'requires_interprocedural': Value('bool'),
        'start_line': Value('int32'),
        'end_line': Value('int32'),
    })

    # Create dataset (test split only)
    test_ds = Dataset.from_dict(test_data, features=features)

    return DatasetDict({
        'test': test_ds
    })


def create_readme(examples: List[Dict[str, Any]]) -> str:
    """Create README.md for the dataset."""
    from collections import Counter

    # Calculate statistics
    total = len(examples)
    with_bugs = sum(1 for ex in examples if ex['ground_truth']['has_bug'])
    safe = total - with_bugs

    categories = Counter(ex['metadata']['category'] for ex in examples)
    difficulties = Counter(ex['metadata']['difficulty'] for ex in examples)
    source_files = len(set(ex['source_file'] for ex in examples))

    readme = f"""---
license: mit
task_categories:
- text-classification
- text-generation
language:
- en
tags:
- code
- static-analysis
- bug-detection
- c
- memory-safety
size_categories:
- n<1K
---

# Infer Pulse Static Analysis Evaluation Dataset

## Dataset Description

This dataset contains **{total} C functions** extracted from Meta's [Infer](https://fbinfer.com/) static analyzer test suite, specifically the Pulse analyzer tests. It's designed for **evaluating** Large Language Models (LLMs) on static analysis tasks, particularly memory safety bug detection in C code.

**Note:** This is an evaluation-only dataset. All examples are provided in the `test` split.

### Key Features

- **{total} individual C functions** with ground truth bug annotations
- **{source_files} unique source files** from Infer's test suite
- **5 bug categories**: NULL pointer dereference, memory leak, use-after-free, uninitialized value, resource leak
- **Smart anonymization**: Function names preserve semantic meaning while removing evaluation hints (`_bad`, `_ok` suffixes)
- **Multiple bugs per function**: Some functions contain multiple bug types (2.5% of dataset)
- **Realistic code**: Actual test cases from a production static analyzer

## Dataset Statistics

- **Total examples:** {total}
- **With bugs:** {with_bugs} ({with_bugs/total*100:.1f}%)
- **Safe (no bugs):** {safe} ({safe/total*100:.1f}%)
- **Unique source files:** {source_files}

### Bug Category Distribution

| Category | Count | Percentage |
|----------|-------|------------|
"""

    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        readme += f"| {cat} | {count} | {count/total*100:.1f}% |\n"

    readme += f"""
### Difficulty Distribution

| Difficulty | Count | Percentage |
|------------|-------|------------|
"""

    for diff, count in sorted(difficulties.items(), key=lambda x: -x[1]):
        readme += f"| {diff} | {count} | {count/total*100:.1f}% |\n"

    readme += """
## Dataset Structure

Each example contains:

- **id**: Unique identifier
- **source_file**: Original file in Infer test suite
- **original_function_name**: Original name from Infer tests
- **anonymized_function_name**: Name with hints removed (e.g., `malloc_no_check_bad` → `malloc_no_check`)
- **function_code**: Complete C function code
- **includes**: Required #include statements
- **dependencies**: Helper functions/structs needed
- **has_bug**: Boolean indicating if function has bugs
- **bug_types**: List of bug types (NULLPTR_DEREFERENCE, MEMORY_LEAK, etc.)
- **bug_line_offsets**: Line numbers relative to function start
- **bug_absolute_lines**: Absolute line numbers in original file
- **bug_severities**: Bug severity levels
- **bug_traces**: Detailed trace information from Infer
- **category**: Primary bug category or "safe"
- **difficulty**: basic/intermediate/advanced
- **requires_interprocedural**: Whether analysis requires understanding function calls
- **start_line/end_line**: Location in original source file

## Example

```python
from datasets import load_dataset

dataset = load_dataset("YOUR_USERNAME/infer-pulse-eval")

# Get first test example
example = dataset['test'][0]

print(f"Function: {example['anonymized_function_name']}")
print(f"Has bug: {example['has_bug']}")
if example['has_bug']:
    print(f"Bug types: {example['bug_types']}")
print(f"\\nCode:\\n{example['function_code']}")
```

## Intended Use

This dataset is designed for:

1. **Evaluating LLMs on static analysis tasks**
2. **Benchmarking bug detection capabilities**
3. **Training models for code understanding**
4. **Researching AI-assisted program analysis**

### Evaluation Protocol

Send the LLM:
- System prompt with bug type definitions and analysis rules
- User prompt with the `function_code` and any needed `includes`

Expected LLM response format:
```json
{
  "has_bug": true|false,
  "bugs": [
    {
      "type": "NULLPTR_DEREFERENCE",
      "line": 3,
      "explanation": "malloc can return NULL, dereferenced without check"
    }
  ]
}
```

Compare against ground truth `has_bug` and `bug_types` fields.

## Anonymization Strategy

Function names are "anonymized" by removing evaluation hints while **preserving semantic meaning**:

- **Removed**: `_bad`, `_ok`, `_good`, `_latent` suffixes, `FP_`, `FN_` prefixes
- **Preserved**: Descriptive parts (e.g., `malloc_no_check`, `use_after_free_simple`)

This maintains realistic code analysis conditions without giving away answers.

## Data Source

All examples are extracted from Meta's Infer static analyzer:
- Repository: https://github.com/facebook/infer
- Test suite: `infer/tests/codetoanalyze/c/pulse/`
- Ground truth: `issues.exp` file from Infer's test expectations

## License

MIT License (same as Infer project)

## Citation

If you use this dataset, please cite:

```bibtex
@misc{{infer-pulse-eval-2024,
  title={{Infer Pulse Static Analysis Evaluation Dataset}},
  author={{Extracted from Meta's Infer project}},
  year={{2024}},
  url={{https://github.com/facebook/infer}}
}}
```

## Contact

For questions or issues, please open an issue on the dataset repository.

## Changelog

### Version 1.0 (2024-11-08)
- Initial release
- 523 examples from 51 source files
- Smart anonymization preserving semantic meaning
- Multiple bugs per function support
"""

    return readme


def upload_dataset(
    data_path: str,
    repo_id: str,
    token: str = None,
    private: bool = False
):
    """
    Upload dataset to Hugging Face Hub.

    Args:
        data_path: Path to JSONL file
        repo_id: Hugging Face repo ID (username/dataset-name)
        token: HF token (optional, will use saved token if not provided)
        private: Whether to create private dataset
    """
    print("=" * 80)
    print("Uploading Infer Pulse Evaluation Dataset to Hugging Face")
    print("=" * 80)
    print()

    # Login if token provided
    if token:
        print("Logging in with provided token...")
        login(token=token)
    else:
        print("Using saved Hugging Face credentials")
        print("(Run 'huggingface-cli login' first if not already logged in)")

    # Load data
    print(f"\nLoading data from {data_path}...")
    examples = load_jsonl(data_path)
    print(f"Loaded {len(examples)} examples")

    # Create dataset (test split only)
    print("\nCreating dataset (test split only)...")
    dataset_dict = create_dataset_splits(examples)
    print(f"  Test: {len(dataset_dict['test'])} examples")

    # Create README
    print("\nGenerating README.md...")
    readme = create_readme(examples)

    # Upload to Hub
    print(f"\nUploading to {repo_id}...")
    print(f"Private: {private}")

    try:
        dataset_dict.push_to_hub(
            repo_id=repo_id,
            private=private,
            token=token
        )
        print("✅ Dataset uploaded successfully!")

        # Upload README
        print("\nUploading README.md...")
        api = HfApi(token=token)

        # Save README to temp file
        readme_path = "/tmp/hf_dataset_readme.md"
        with open(readme_path, 'w') as f:
            f.write(readme)

        api.upload_file(
            path_or_fileobj=readme_path,
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
            token=token
        )
        print("✅ README uploaded successfully!")

        print()
        print("=" * 80)
        print("UPLOAD COMPLETE!")
        print("=" * 80)
        print(f"\nDataset URL: https://huggingface.co/datasets/{repo_id}")
        print("\nYou can now load it with:")
        print(f'  from datasets import load_dataset')
        print(f'  dataset = load_dataset("{repo_id}")')

    except Exception as e:
        print(f"\n❌ Error uploading dataset: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged in: huggingface-cli login")
        print("2. Check that repo_id format is correct: username/dataset-name")
        print("3. Verify you have write permissions to this repository")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Upload Infer Pulse evaluation dataset to Hugging Face Hub'
    )
    parser.add_argument(
        '--data',
        default='data/pulse_all_examples.jsonl',
        help='Path to JSONL data file (default: data/pulse_all_examples.jsonl)'
    )
    parser.add_argument(
        '--repo-id',
        required=True,
        help='Hugging Face repo ID (format: username/dataset-name)'
    )
    parser.add_argument(
        '--token',
        default=None,
        help='Hugging Face token (optional, uses saved token if not provided)'
    )
    parser.add_argument(
        '--private',
        action='store_true',
        help='Create private dataset (default: public)'
    )

    args = parser.parse_args()

    # Check data file exists
    if not os.path.exists(args.data):
        print(f"ERROR: Data file not found: {args.data}")
        exit(1)

    # Check token from env if not provided
    token = args.token or os.getenv('HF_TOKEN')

    upload_dataset(
        data_path=args.data,
        repo_id=args.repo_id,
        token=token,
        private=args.private
    )


if __name__ == '__main__':
    main()

# Infer LLM Evaluation Harness

This directory contains tools to evaluate LLMs on static analysis tasks similar to Infer's Pulse analyzer.

## Overview

The evaluation harness:
1. Extracts individual functions from Infer test files
2. Anonymizes function names to avoid giving hints
3. Maps to ground truth from issues.exp
4. Generates JSONL files for LLM evaluation

## Directory Structure

```
eval_harness/
├── README.md                 # This file
├── parser.py                 # Main parser to generate eval data
├── system_prompt.txt         # System prompt for LLM
├── schema.md                 # JSONL schema documentation
├── data/                     # Generated JSONL files
│   ├── nullptr_basic.jsonl
│   ├── memory_leak_basic.jsonl
│   └── ...
└── results/                  # LLM evaluation results
    └── model_name/
        └── predictions.jsonl
```

## JSONL Schema

Each line in the JSONL file represents one function to analyze:

```json
{
  "id": "nullptr_c_001",
  "source_file": "codetoanalyze/c/pulse/nullptr.c",
  "original_function_name": "malloc_no_check_bad",
  "anonymized_function_name": "function_001",
  "function_code": "int* function_001() {\n  int* p = (int*)malloc(sizeof(int));\n  *p = 42;\n  return p;\n}",
  "includes": ["#include <stdlib.h>"],
  "dependencies": [],
  "ground_truth": {
    "has_bug": true,
    "bugs": [
      {
        "bug_type": "NULLPTR_DEREFERENCE",
        "line_offset": 2,
        "absolute_line": 14,
        "severity": "ERROR",
        "trace": "in call to `malloc (null case)` (modelled),is assigned to the null pointer,assigned,invalid access occurs here"
      }
    ]
  },
  "metadata": {
    "difficulty": "basic",
    "requires_interprocedural": false,
    "category": "nullptr_dereference"
  }
}
```

## Usage

### Generate Evaluation Data

```bash
cd eval_harness
python parser.py --test-file ../infer/tests/codetoanalyze/c/pulse/nullptr.c \
                 --issues-exp ../infer/tests/codetoanalyze/c/pulse/issues.exp \
                 --output data/nullptr_basic.jsonl
```

### Run LLM Evaluation

```python
import json

# Load system prompt
with open('system_prompt.txt') as f:
    system_prompt = f.read()

# Load eval data
with open('data/nullptr_basic.jsonl') as f:
    examples = [json.loads(line) for line in f]

# For each example
for example in examples:
    # Construct prompt
    prompt = f"Analyze this C function:\n\n{example['function_code']}\n\nReturn JSON with any bugs found."

    # Call LLM
    response = llm_call(system_prompt, prompt)

    # Compare with ground truth
    evaluate(response, example['ground_truth'])
```

## Evaluation Metrics

- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)
- **F1 Score**: 2 * P * R / (P + R)

Where:
- TP: Correct bugs identified
- FP: Incorrect bugs reported
- FN: Missed bugs

## Test Categories

1. **nullptr_basic**: Simple null pointer dereferences
2. **memory_leak_basic**: Basic memory leaks
3. **interprocedural**: Cross-function analysis required
4. **path_sensitive**: Conditional bugs
5. **resource_leak**: File handle leaks

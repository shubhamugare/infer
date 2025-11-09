# Eval Harness Usage Guide

## Quick Start

### 1. Generate Evaluation Data

Extract functions from Infer test files and create JSONL evaluation datasets:

```bash
cd eval_harness

# Generate nullptr evaluation data
python parser.py \
    --test-file ../infer/tests/codetoanalyze/c/pulse/nullptr.c \
    --issues-exp ../infer/tests/codetoanalyze/c/pulse/issues.exp \
    --output data/nullptr_basic.jsonl

# Generate memory leak evaluation data
python parser.py \
    --test-file ../infer/tests/codetoanalyze/c/pulse/memory_leak.c \
    --issues-exp ../infer/tests/codetoanalyze/c/pulse/issues.exp \
    --output data/memory_leak_basic.jsonl
```

### 2. Inspect Generated Data

```bash
# View first example
head -1 data/nullptr_basic.jsonl | python3 -m json.tool

# Count examples
wc -l data/nullptr_basic.jsonl

# Count by category
python3 << 'EOF'
import json
from collections import Counter

with open('data/nullptr_basic.jsonl') as f:
    examples = [json.loads(line) for line in f]

categories = Counter(ex['metadata']['category'] for ex in examples)
for cat, count in sorted(categories.items()):
    print(f"{cat}: {count}")
EOF
```

### 3. Example JSONL Entry

Each line contains a single function to analyze:

```json
{
  "id": "nullptr_001",
  "source_file": "pulse/nullptr.c",
  "original_function_name": "malloc_no_check_bad",
  "anonymized_function_name": "test_function_001",
  "function_code": "int* test_function_001() {\n  int* p = (int*)malloc(sizeof(int));\n  *p = 42;\n  return p;\n}\n",
  "includes": ["#include <stdlib.h>"],
  "dependencies": [],
  "ground_truth": {
    "has_bug": true,
    "bugs": [{
      "bug_type": "NULLPTR_DEREFERENCE",
      "line_offset": 2,
      "absolute_line": 14,
      "severity": "ERROR",
      "trace": "malloc can return NULL..."
    }]
  },
  "metadata": {
    "difficulty": "basic",
    "requires_interprocedural": false,
    "category": "nullptr_dereference"
  }
}
```

## Using with LLMs

### Manual Evaluation (Python)

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
    user_prompt = f"""Analyze this C function:

{example['function_code']}

Return JSON: {{"has_bug": true|false, "bugs": [...]}}
"""

    # Call your LLM
    response = your_llm_api(system_prompt, user_prompt)

    # Compare with ground truth
    prediction = json.loads(response)
    ground_truth = example['ground_truth']

    if prediction['has_bug'] == ground_truth['has_bug']:
        print(f"✓ {example['id']}: Correct")
    else:
        print(f"✗ {example['id']}: Wrong")
```

### Using the Evaluator Script

```python
# evaluator.py (you need to implement call_llm function)

import openai

def call_llm(system_prompt: str, user_prompt: str, model: str = "gpt-4"):
    """Call OpenAI API"""
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
```

Then run:

```bash
python evaluator.py \
    --data data/nullptr_basic.jsonl \
    --model gpt-4 \
    --output results/gpt4/nullptr_results.jsonl
```

## Parser Options

### Include only functions with bugs

```bash
python parser.py \
    --test-file ../infer/tests/codetoanalyze/c/pulse/nullptr.c \
    --issues-exp ../infer/tests/codetoanalyze/c/pulse/issues.exp \
    --exclude-safe \
    --output data/nullptr_bugs_only.jsonl
```

### Keep original function names (no anonymization)

```bash
python parser.py \
    --test-file ../infer/tests/codetoanalyze/c/pulse/nullptr.c \
    --issues-exp ../infer/tests/codetoanalyze/c/pulse/issues.exp \
    --no-anonymize \
    --output data/nullptr_original_names.jsonl
```

## Example Prompts

### Basic Prompt

```
System: [Contents of system_prompt.txt]

User:
Analyze this C function:

```c
int* test_function_001() {
  int* p = (int*)malloc(sizeof(int));
  *p = 42;
  return p;
}
```

Return JSON: {"has_bug": true|false, "bugs": [...]}
```

### Expected LLM Response

```json
{
  "has_bug": true,
  "bugs": [
    {
      "bug_type": "NULLPTR_DEREFERENCE",
      "line": 3,
      "severity": "ERROR",
      "explanation": "malloc() can return NULL on failure. Line 3 dereferences p without null check."
    }
  ]
}
```

## Evaluation Metrics

The evaluator computes:

- **Precision**: TP / (TP + FP) - accuracy of reported bugs
- **Recall**: TP / (TP + FN) - coverage of actual bugs
- **F1 Score**: harmonic mean of precision and recall
- **Accuracy**: (TP + TN) / Total

Where:
- **TP** (True Positive): Correctly identified bug
- **FP** (False Positive): Incorrectly reported bug
- **FN** (False Negative): Missed an actual bug
- **TN** (True Negative): Correctly identified safe code

## Filtering Examples

### By Difficulty

```python
import json

with open('data/nullptr_basic.jsonl') as f:
    examples = [json.loads(line) for line in f]

# Get only basic difficulty
basic = [ex for ex in examples if ex['metadata']['difficulty'] == 'basic']
print(f"Basic examples: {len(basic)}")

# Get advanced (requires interprocedural)
advanced = [ex for ex in examples if ex['metadata']['requires_interprocedural']]
print(f"Interprocedural examples: {len(advanced)}")
```

### By Bug Type

```python
# Get only nullptr dereference bugs
nullptr_bugs = [ex for ex in examples
                if ex['metadata']['category'] == 'nullptr_dereference']

# Get safe functions (no bugs)
safe_funcs = [ex for ex in examples
              if ex['metadata']['category'] == 'safe']
```

## Batch Processing

Generate eval data for multiple test files:

```bash
#!/bin/bash

TEST_DIR="../infer/tests/codetoanalyze/c/pulse"
ISSUES_EXP="$TEST_DIR/issues.exp"

for file in nullptr memory_leak interprocedural; do
    echo "Processing $file.c..."
    python parser.py \
        --test-file "$TEST_DIR/$file.c" \
        --issues-exp "$ISSUES_EXP" \
        --output "data/${file}_eval.jsonl"
done
```

## Analyzing Results

After running the evaluator:

```python
import json

# Load results
with open('results/gpt4/nullptr_results.jsonl') as f:
    results = [json.loads(line) for line in f]

# Find all false positives
fps = [r for r in results
       if r['evaluation']['match_type'] == 'false_positive']

print(f"False Positives: {len(fps)}")
for fp in fps:
    print(f"  {fp['original_function_name']}")

# Find all false negatives
fns = [r for r in results
       if r['evaluation']['match_type'] == 'false_negative']

print(f"\nFalse Negatives: {len(fns)}")
for fn in fns:
    missed = [b['bug_type'] for b in fn['evaluation']['missed_bugs']]
    print(f"  {fn['original_function_name']}: missed {missed}")
```

## Tips

1. **Start Simple**: Begin with `nullptr_basic.jsonl` (basic bugs)
2. **Check Anonymization**: Ensure function names don't leak hints
3. **Batch Size**: Process 10-20 examples at a time for faster iteration
4. **Temperature**: Use temperature=0 for reproducible results
5. **Prompt Engineering**: Adjust system prompt based on common errors

## Advanced: Custom Test Sets

Create custom test sets by filtering:

```python
import json

# Load full dataset
with open('data/nullptr_basic.jsonl') as f:
    all_examples = [json.loads(line) for line in f]

# Create "easy" test set: only basic, non-interprocedural
easy = [ex for ex in all_examples
        if ex['metadata']['difficulty'] == 'basic'
        and not ex['metadata']['requires_interprocedural']]

# Save custom test set
with open('data/nullptr_easy.jsonl', 'w') as f:
    for ex in easy:
        f.write(json.dumps(ex) + '\n')

print(f"Created easy test set with {len(easy)} examples")
```

# Eval Harness Summary

## What Was Created

A complete evaluation framework for testing LLMs on static analysis tasks, based on Infer's Pulse analyzer test suite.

## Directory Structure

```
eval_harness/
├── README.md              # Overview and schema documentation
├── USAGE.md               # Detailed usage guide
├── EXAMPLES.md            # Example data and expected outputs
├── SUMMARY.md             # This file
├── system_prompt.txt      # System prompt for LLMs
├── parser.py              # Main parser script ✨
├── evaluator.py           # Evaluation framework (implement LLM call)
└── data/                  # Generated JSONL files
    ├── nullptr_basic.jsonl        (29 examples)
    └── memory_leak_basic.jsonl    (44 examples)
```

## Key Features

### 1. Function-Level Isolation ✅
- Each JSONL line = one independent function
- No file-level context needed
- LLM analyzes single function at a time

### 2. Anonymized Function Names ✅
- Original: `malloc_no_check_bad` → Anonymized: `test_function_001`
- Removes hints from function names
- Tests actual code analysis, not pattern matching

### 3. Complete Ground Truth ✅
- Bug type (NULLPTR_DEREFERENCE, MEMORY_LEAK, etc.)
- Line numbers (offset and absolute)
- Severity
- Trace information

### 4. Rich Metadata ✅
- Difficulty level (basic, intermediate, advanced)
- Requires interprocedural analysis (yes/no)
- Category (nullptr_dereference, memory_leak, safe, etc.)
- Source location info

## JSONL Schema

```json
{
  "id": "nullptr_001",
  "original_function_name": "malloc_no_check_bad",
  "anonymized_function_name": "test_function_001",
  "function_code": "int* test_function_001() {...}",
  "includes": ["#include <stdlib.h>"],
  "dependencies": [],
  "ground_truth": {
    "has_bug": true,
    "bugs": [{"bug_type": "NULLPTR_DEREFERENCE", ...}]
  },
  "metadata": {
    "difficulty": "basic",
    "category": "nullptr_dereference"
  }
}
```

## Quick Start

### Generate Eval Data

```bash
cd eval_harness

python parser.py \
    --test-file ../infer/tests/codetoanalyze/c/pulse/nullptr.c \
    --issues-exp ../infer/tests/codetoanalyze/c/pulse/issues.exp \
    --output data/nullptr_basic.jsonl
```

### Use in Your Code

```python
import json

# Load examples
with open('data/nullptr_basic.jsonl') as f:
    examples = [json.loads(line) for line in f]

# Load system prompt
with open('system_prompt.txt') as f:
    system_prompt = f.read()

# For each example
for ex in examples:
    # Construct prompt
    prompt = f"Analyze this C function:\n\n{ex['function_code']}\n\nReturn JSON."
    
    # Call your LLM
    response = your_llm(system_prompt, prompt)
    
    # Compare with ground truth
    if response['has_bug'] == ex['ground_truth']['has_bug']:
        print(f"✓ Correct")
    else:
        print(f"✗ Wrong")
```

## Statistics

### nullptr_basic.jsonl
- **29 examples** total
- **14 with bugs**, 15 safe
- Categories:
  - nullptr_dereference: 12
  - safe: 15
  - other: 2

### memory_leak_basic.jsonl
- **44 examples** total
- **16 with bugs**, 28 safe
- Categories:
  - memory_leak: 12
  - safe: 28
  - nullptr_dereference: 2
  - other: 2

## System Prompt Highlights

The system prompt ([system_prompt.txt](system_prompt.txt)):
- ✅ Defines analysis rules (malloc can fail, must free memory)
- ✅ Lists bug types to detect
- ✅ Specifies JSON output format
- ✅ Emphasizes precision (avoid false alarms)
- ✅ Instructs to ignore function names

## Parser Features

The parser ([parser.py](parser.py)):
- ✅ Extracts individual functions from C files
- ✅ Anonymizes function names
- ✅ Maps to ground truth from issues.exp
- ✅ Categorizes by difficulty and bug type
- ✅ Tracks interprocedural dependencies
- ✅ Excludes FP_/FN_ functions (known false positives/negatives)
- ✅ Generates JSONL output

## Evaluation Metrics

- **Precision**: TP / (TP + FP) - accuracy of reported bugs
- **Recall**: TP / (TP + FN) - coverage of actual bugs
- **F1 Score**: 2 * P * R / (P + R)
- **Accuracy**: (TP + TN) / Total

## Next Steps

1. **Implement LLM call** in `evaluator.py` (OpenAI, Anthropic, etc.)
2. **Run evaluation** on basic test sets
3. **Analyze results** - which bugs are hard for LLMs?
4. **Generate more data** from other test files (interprocedural.c, fopen.c, etc.)
5. **Iterate on prompts** based on common errors

## Example Usage

See [USAGE.md](USAGE.md) for detailed examples of:
- Filtering by difficulty
- Batch processing multiple files
- Analyzing results
- Creating custom test sets

## Files Reference

- **[README.md](README.md)**: Overview and schema
- **[USAGE.md](USAGE.md)**: Detailed usage guide with examples
- **[EXAMPLES.md](EXAMPLES.md)**: Concrete examples from generated data
- **[system_prompt.txt](system_prompt.txt)**: System prompt for LLMs
- **[parser.py](parser.py)**: Parser to generate eval data
- **[evaluator.py](evaluator.py)**: Evaluation framework (needs LLM integration)

## Contributing

To add more test files:

```bash
python parser.py \
    --test-file ../infer/tests/codetoanalyze/c/pulse/YOUR_FILE.c \
    --issues-exp ../infer/tests/codetoanalyze/c/pulse/issues.exp \
    --output data/YOUR_FILE_eval.jsonl
```

Recommended test files:
- ✅ nullptr.c (done)
- ✅ memory_leak.c (done)
- ⬜ interprocedural.c
- ⬜ latent.c
- ⬜ uninit.c
- ⬜ fopen.c

# Complete Pulse Evaluation Dataset

## 🎉 Generated Successfully!

**File:** `data/pulse_all_examples.jsonl`

All 54 C test files from `infer/tests/codetoanalyze/c/pulse/` have been processed.

## Statistics

### Overview
- **Total Examples:** 523
- **Source Files:** 51 unique C files
- **File Size:** 384K
- **Examples with Bugs:** 217 (41.5%)
- **Safe Examples:** 306 (58.5%)

### Bug Categories

| Category | Count | Percentage |
|----------|-------|------------|
| Safe (no bugs) | 306 | 58.5% |
| NULL Pointer Dereference | 112 | 21.4% |
| Other | 68 | 13.0% |
| Memory Leak | 18 | 3.4% |
| Uninitialized Value | 12 | 2.3% |
| Use After Free | 4 | 0.8% |
| Resource Leak | 3 | 0.6% |

### Top 10 Source Files by Example Count

| Source File | Examples |
|-------------|----------|
| pulse/infinite.c | 83 |
| pulse/memory_leak.c | 44 |
| pulse/fopen.c | 40 |
| pulse/uninit.c | 37 |
| pulse/nullptr.c | 29 |
| pulse/funptr.c | 21 |
| pulse/nullptr_more.c | 19 |
| pulse/angelism.c | 17 |
| pulse/interprocedural.c | 17 |
| pulse/assert_failure.c | 14 |

### All Source Files Processed

```
abduce.c (5), aliasing.c (2), angelism.c (17), arithmetic.c (10),
array_out_of_bounds.c (1), assert.c (1), assert_failure.c (14),
cleanup_attribute.c (5), compound_literal.c (3), dangling_deref.c (6),
enum.c (3), exit_example.c (7), field_taint.c (12), fopen.c (40),
frontend.c (4), frontend_compound_literal.c (2), frontend_struct_initlistexpr.c (8),
funptr.c (21), getcwd.c (4), infinite.c (83), initlistexpr.c (2),
integers.c (5), interprocedural.c (17), issues_abort_execution.c (3),
latent.c (11), list_api.c (6), list_checks.c (6), lists.c (7),
memcpy.c (4), memory_leak.c (44), memory_leak_more.c (6), nullptr.c (29),
nullptr_more.c (19), offsetof_expr.c (1), pthread_create.c (5),
pthread_mutex.c (4), recursion.c (11), recursion2.c (1), resource_leak.c (6),
sentinel_attribute.c (1), shift.c (6), sizeof.c (1), specialization.c (11),
struct_values.c (2), taint_var_arg.c (4), ternary.c (10), traces.c (5),
transitive-access.c (3), uninit.c (37), unsigned_values.c (4), var_arg.c (4)
```

## File Location

```
/Users/shubhamugare/infer/eval_harness/data/pulse_all_examples.jsonl
```

## Quick Access

### View First Example
```bash
head -1 data/pulse_all_examples.jsonl | python3 -m json.tool
```

### Count Examples
```bash
wc -l data/pulse_all_examples.jsonl
# Output: 523
```

### Statistics by Category
```python
import json
from collections import Counter

with open('data/pulse_all_examples.jsonl') as f:
    examples = [json.loads(line) for line in f]

categories = Counter(ex['metadata']['category'] for ex in examples)
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"{cat}: {count}")
```

### Filter Examples

#### Get Only Bug Examples
```python
import json

with open('data/pulse_all_examples.jsonl') as f:
    all_examples = [json.loads(line) for line in f]

bug_examples = [ex for ex in all_examples if ex['ground_truth']['has_bug']]
print(f"Bug examples: {len(bug_examples)}")  # 217
```

#### Get Only Safe Examples
```python
safe_examples = [ex for ex in all_examples if not ex['ground_truth']['has_bug']]
print(f"Safe examples: {len(safe_examples)}")  # 306
```

#### Get Specific Bug Type
```python
nullptr_bugs = [
    ex for ex in all_examples
    if ex['metadata']['category'] == 'nullptr_dereference'
]
print(f"NULL pointer bugs: {len(nullptr_bugs)}")  # 112
```

#### Get by Source File
```python
memory_leak_examples = [
    ex for ex in all_examples
    if ex['source_file'] == 'pulse/memory_leak.c'
]
print(f"From memory_leak.c: {len(memory_leak_examples)}")  # 44
```

## Example Entry Structure

```json
{
  "id": "nullptr_001",
  "source_file": "pulse/nullptr.c",
  "original_function_name": "malloc_no_check_bad",
  "anonymized_function_name": "test_function_001",
  "function_code": "int* test_function_001() {...}",
  "includes": ["#include <stdlib.h>"],
  "dependencies": [],
  "ground_truth": {
    "has_bug": true,
    "bugs": [{
      "bug_type": "NULLPTR_DEREFERENCE",
      "line_offset": 2,
      "absolute_line": 14,
      "severity": "ERROR",
      "trace": "..."
    }]
  },
  "metadata": {
    "difficulty": "advanced",
    "requires_interprocedural": false,
    "category": "nullptr_dereference",
    "start_line": 12,
    "end_line": 16
  }
}
```

## Usage Example

```python
import json

# Load system prompt
with open('system_prompt.txt') as f:
    system_prompt = f.read()

# Load all examples
with open('data/pulse_all_examples.jsonl') as f:
    examples = [json.loads(line) for line in f]

print(f"Evaluating {len(examples)} examples...")

# Evaluate each example
results = []
for i, ex in enumerate(examples, 1):
    # Construct prompt
    prompt = f"""Analyze this C function:

{ex['function_code']}

Return JSON: {{"has_bug": true|false, "bugs": [...]}}"""

    # Call your LLM
    response = your_llm_api(system_prompt, prompt)

    # Compare with ground truth
    correct = response['has_bug'] == ex['ground_truth']['has_bug']

    results.append({
        'id': ex['id'],
        'source_file': ex['source_file'],
        'correct': correct,
        'prediction': response,
        'ground_truth': ex['ground_truth']
    })

    if i % 50 == 0:
        print(f"Progress: {i}/{len(examples)}")

# Calculate metrics
accuracy = sum(1 for r in results if r['correct']) / len(results)
print(f"\nAccuracy: {accuracy:.2%}")
```

## Subsets Available

In addition to the complete dataset, smaller subsets are available:

- `data/nullptr_basic.jsonl` - 29 examples from nullptr.c
- `data/memory_leak_basic.jsonl` - 44 examples from memory_leak.c
- `data/interprocedural.jsonl` - 17 examples from interprocedural.c

## Recommended Evaluation Strategy

### Phase 1: Small Scale (30-50 examples)
Start with a focused subset to iterate quickly:
```python
# Get first 50 examples
subset = examples[:50]
```

### Phase 2: Category-Specific (50-100 examples)
Test on specific bug types:
```python
# Get all nullptr examples
nullptr_subset = [ex for ex in examples
                  if ex['metadata']['category'] == 'nullptr_dereference']
```

### Phase 3: Full Evaluation (523 examples)
Run on complete dataset:
```python
# Use all 523 examples
full_evaluation = examples
```

## Files Reference

- **Generation script:** `generate_all.sh`
- **Parser:** `parser.py`
- **System prompt:** `system_prompt.txt`
- **Evaluator template:** `evaluator.py`
- **Complete dataset:** `data/pulse_all_examples.jsonl` ← **THIS FILE**

## Next Steps

1. **Test on small subset** (50 examples) to verify your LLM integration
2. **Analyze initial results** to identify common error patterns
3. **Iterate on prompts** based on findings
4. **Run full evaluation** on all 523 examples
5. **Compare across models** (GPT-4, Claude, Llama, etc.)

---

**Generated:** 2024-11-08
**Total Examples:** 523
**Total Source Files:** 51
**Status:** ✅ Ready for Evaluation

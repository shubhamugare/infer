# 🚀 Quick Start Guide

## Complete Dataset Generated!

**Main File:** `data/pulse_all_examples.jsonl`

**📊 523 examples from 51 C source files**

## Immediate Use

```python
import json

# Load examples
with open('data/pulse_all_examples.jsonl') as f:
    examples = [json.loads(line) for line in f]

# Load system prompt
with open('system_prompt.txt') as f:
    system_prompt = f.read()

# Pick first example
ex = examples[0]

# What you send to LLM
user_prompt = f"Analyze:\n\n{ex['function_code']}"

# Ground truth to compare against
print(ex['ground_truth'])
# {'has_bug': false, 'bugs': []}
```

## File Locations

| File | Path | Description |
|------|------|-------------|
| **Complete Dataset** | `data/pulse_all_examples.jsonl` | **523 examples ← USE THIS** |
| System Prompt | `system_prompt.txt` | LLM instructions |
| Parser | `parser.py` | Generator script |
| Generator | `generate_all.sh` | Batch processor |

## Key Stats

- **Total:** 523 examples
- **With Bugs:** 217 (42%)
- **Safe:** 306 (58%)
- **Files:** 51 unique source files
- **Categories:** nullptr (112), memory_leak (18), uninit (12), use_after_free (4), resource_leak (3), other (68), safe (306)

## Example Entry

```json
{
  "id": "abduce_005",
  "source_file": "pulse/abduce.c",
  "original_function_name": "set_ptr_param_array_get_null_bad",
  "anonymized_function_name": "set_ptr_param_array_get_null",
  "function_code": "void set_ptr_param_array_get_null() {...}",
  "ground_truth": {"has_bug": true, "bugs": [{"bug_type": "NULLPTR_DEREFERENCE", ...}]},
  "metadata": {"category": "nullptr_dereference", ...}
}
```

**Note:** Function names are anonymized by removing hint suffixes (`_bad`, `_ok`, `_good`) and prefixes (`FP_`, `FN_`) while preserving the semantic/descriptive part of the name. This helps LLMs focus on code analysis rather than name-based hints.

## Filter Examples

```python
# Only bugs
bugs = [ex for ex in examples if ex['ground_truth']['has_bug']]
# 217 examples

# Only safe
safe = [ex for ex in examples if not ex['ground_truth']['has_bug']]
# 306 examples

# Specific type
nullptrs = [ex for ex in examples
            if ex['metadata']['category'] == 'nullptr_dereference']
# 112 examples
```

## See Also

- **[ALL_EXAMPLES_SUMMARY.md](ALL_EXAMPLES_SUMMARY.md)** - Detailed statistics
- **[USAGE.md](USAGE.md)** - Comprehensive usage guide
- **[SUMMARY.md](SUMMARY.md)** - Project overview

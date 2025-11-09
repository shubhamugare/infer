# Dataset Enhancement: Interprocedural Context

## What Changed

The dataset has been enhanced to provide complete context for interprocedural examples, enabling LLMs to detect bugs that require understanding function calls and data structures.

## Changes Made

### 1. Parser Enhancement (`parser.py`)

**New Functions:**
- `extract_struct_definitions()` - Extracts all struct definitions from source files
- `find_referenced_structs()` - Recursively finds struct dependencies (including nested structs)
- `get_dependency_code()` - Retrieves full code for called functions

**Updated Logic:**
- The `includes` field now contains:
  - Original `#include` statements
  - All referenced struct definitions (with nested dependencies)
- The `dependencies` field now contains:
  - Full function code for all called functions (not just names)

### 2. System Prompt Update (`system_prompt.txt`)

Added guidance on using the context:
```
You will be provided with:
1. The main function to analyze
2. Context (includes and struct definitions) - Use these to understand data structures
3. Dependencies (called functions) - Use these to understand interprocedural behavior

For interprocedural analysis:
- Consider what dependency functions do to their parameters
- Track initialization, modification, and usage across function boundaries
- For struct fields, track which specific fields are initialized vs. accessed
```

### 3. Dataset Statistics

- **Total examples:** 523
- **Interprocedural examples:** 137 (26.2%)
- **Examples with function dependencies:** 137 (26.2%)
- **Examples with struct definitions:** 74 (14.1%)
- **Examples with both:** 19 (3.6%)

**Dependency depth:**
- 120 examples with 1 dependency function
- 16 examples with 2 dependency functions
- 1 example with 3 dependency functions

**Struct complexity:**
- 69 examples with 1 struct definition
- 5 examples with 2 struct definitions (nested)

## Example: Before vs After

### Before Enhancement

```json
{
  "function_code": "void nested_struct() {\n  struct uninit_nested x;\n  x.g1.f2 = 42;\n  read_g1_f1(&x);\n}",
  "includes": [
    "#include <assert.h>",
    "#include <stdlib.h>"
  ],
  "dependencies": ["read_g1_f1"]
}
```

**Problem:** LLM cannot determine:
- What is `uninit_nested`?
- What fields does it have?
- What does `read_g1_f1()` do?
- Is `g1.f1` initialized?

### After Enhancement

```json
{
  "function_code": "void nested_struct() {\n  struct uninit_nested x;\n  x.g1.f2 = 42;\n  read_g1_f1(&x);\n}",
  "includes": [
    "#include <assert.h>",
    "#include <stdlib.h>",
    "struct uninit_nested {\n  struct uninit_s g1;\n  int g2;\n};",
    "struct uninit_s {\n  int f1;\n  int f2;\n};"
  ],
  "dependencies": [
    "void read_g1_f1(struct uninit_nested* x) { int y = x->g1.f1; }"
  ]
}
```

**Solution:** LLM now knows:
- `uninit_nested` has field `g1` of type `uninit_s` and field `g2`
- `uninit_s` has two separate fields: `f1` and `f2`
- The function initializes `g1.f2` but NOT `g1.f1`
- `read_g1_f1()` reads the uninitialized field `g1.f1` → **UNINITIALIZED_VALUE bug!**

## Benefits

1. **Interprocedural Analysis:** LLMs can now track data flow across function boundaries
2. **Struct Field Tracking:** Complete struct definitions enable field-level analysis
3. **Nested Dependencies:** Recursive struct extraction handles complex data structures
4. **Better Evaluation:** More realistic assessment of LLM static analysis capabilities

## Dataset Access

The enhanced dataset is available at:
```
https://huggingface.co/datasets/shubhamugare/infer-pulse-eval
```

Load with:
```python
from datasets import load_dataset
dataset = load_dataset("shubhamugare/infer-pulse-eval")
```

## Next Steps for Evaluation

When evaluating LLMs:
1. Include both `includes` and `dependencies` in the prompt context
2. Ensure the model understands it should analyze helper functions
3. Consider tracking performance separately for:
   - Intraprocedural bugs (single function)
   - Interprocedural bugs (require dependencies)
   - Struct-dependent bugs (require struct definitions)

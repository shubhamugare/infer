# Line Offset Calculation in Dataset

## How Line Numbers Work

### Line Offset (0-indexed from function start)

The `line_offset` field in the dataset is **0-indexed** and counts from the **first line of the function**, which is the function signature/declaration line.

**Line 0** = The function declaration/signature line
**Line 1** = First line inside the function body
**Line 2** = Second line inside the function body
...and so on.

## Examples

### Example 1: Simple Bug

```c
Line 0: void set_ptr_param_array_get_null() {
Line 1:   // A null pointer dereference is expected here
Line 2:   set_ptr_param_array(NULL);  <-- Bug at line_offset: 2
Line 3: }
```

**Bug location:** `line_offset: 2`
- This is the 3rd line when counting from 0
- It's the 2nd line inside the function body

### Example 2: Bug on First Line of Body

```c
Line 0: void call_by_ref_actual_already_in_footprint() {
Line 1:   by_ref_actual_already_in_footprint2(NULL); // Bug  <-- Bug at line_offset: 1
Line 2: }
```

**Bug location:** `line_offset: 1`
- This is the 2nd line when counting from 0
- It's the 1st line inside the function body

### Example 3: Multi-line Function

```c
Line 0: int* malloc_no_check(int size) {
Line 1:   int* ptr = malloc(size);
Line 2:   *ptr = 42;  <-- Bug at line_offset: 2 (NULL dereference)
Line 3:   return ptr;
Line 4: }
```

**Bug location:** `line_offset: 2`
- Dereferencing `ptr` without checking if malloc returned NULL

## Formula

```
absolute_line = start_line + line_offset
```

Where:
- `start_line`: The line number in the original source file where the function starts
- `line_offset`: The offset from line 0 (the function declaration)
- `absolute_line`: The actual line number in the original source file

## In the Dataset

Each bug in `ground_truth.bugs` has:

```json
{
  "bug_type": "NULLPTR_DEREFERENCE",
  "line_offset": 2,           // 0-indexed from function start
  "absolute_line": 56,         // Line number in original file
  "severity": "ERROR",
  "trace": "..."
}
```

## For LLM Evaluation

When prompting an LLM, you typically show the function code. The LLM should return line numbers in the same format:

**Input to LLM:**
```c
void set_ptr_param_array_get_null() {
  // A null pointer dereference is expected here
  set_ptr_param_array(NULL);
}
```

**Expected LLM Response:**
```json
{
  "has_bug": true,
  "bugs": [
    {
      "type": "NULLPTR_DEREFERENCE",
      "line": 2,  // 0-indexed, counting function signature as line 0
      "explanation": "Passing NULL without check"
    }
  ]
}
```

## Important Notes

1. **Line 0 is the function signature**, not the opening brace or first statement
2. **0-indexed**: First line = 0, not 1
3. **Includes empty lines and comments** in the count
4. The line number indicates where the bug **manifests** (e.g., where the dereference happens), not necessarily where the root cause is

## Python Code to Extract Line

```python
from datasets import load_dataset

dataset = load_dataset("shubhamugare/infer-pulse-eval")
example = dataset['test'][0]

if example['has_bug']:
    bug = example['bugs'][0]
    line_offset = bug['line_offset']

    # Get the specific line
    lines = example['function_code'].split('\n')
    buggy_line = lines[line_offset]

    print(f"Bug at line {line_offset}: {buggy_line}")
```

## Visual Guide

```
        Function Code               Line Offset    Description
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
void function_name() {                    0        Function signature
  int x = 0;                              1        First line in body
  x++;                                    2        Second line in body
  return x;                               3        Third line in body
}                                         4        Closing brace
```

If a bug is at `line_offset: 2`, it's at the line `x++;` (third line from top, but index 2 when 0-indexed).

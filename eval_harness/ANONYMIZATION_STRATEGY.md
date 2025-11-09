# Function Name Anonymization Strategy

## Overview

Function names in the evaluation dataset are "anonymized" to remove hint suffixes and prefixes that directly indicate whether a bug exists, while **preserving the semantic meaning** of the function name.

## Why This Approach?

**Problem with full anonymization** (`malloc_no_check_bad` → `test_function_001`):
- Loses all semantic context about what the function does
- Makes analysis harder and less realistic
- LLMs benefit from descriptive function names in real-world scenarios

**Solution - Smart hint removal** (`malloc_no_check_bad` → `malloc_no_check`):
- Preserves semantic meaning (what the function does)
- Removes only the evaluation hints (_bad, _ok, etc.)
- Maintains realistic code analysis conditions

## Transformation Rules

### Prefixes Removed
- `FP_` (false positive marker)
- `FN_` (false negative marker)

### Suffixes Removed
- `_bad` (indicates bug expected)
- `_ok` (indicates no bug expected)
- `_good` (indicates no bug expected)
- `_latent` (indicates latent issue)

### What's Preserved
Everything else! The descriptive part of the function name remains intact.

## Examples

| Original Name | Anonymized Name | Semantic Meaning Preserved |
|--------------|-----------------|---------------------------|
| `malloc_no_check_bad` | `malloc_no_check` | ✅ malloc without checking |
| `create_null_path_ok` | `create_null_path` | ✅ creates a null path |
| `FP_some_function` | `some_function` | ✅ function purpose clear |
| `use_after_free_simple_bad` | `use_after_free_simple` | ✅ simple use pattern |
| `basic_malloc_ok` | `basic_malloc` | ✅ basic allocation |
| `passByRefTwiceOk` | `passByRefTwice` | ✅ pass by reference twice |

## Implementation

See `parser.py` function `anonymize_function_name()`:

```python
def anonymize_function_name(original_name: str, index: int) -> str:
    """Remove hint suffixes while preserving semantic meaning."""
    name = original_name

    # Remove hint prefixes
    if name.startswith('FP_'):
        name = name[3:]
    elif name.startswith('FN_'):
        name = name[3:]

    # Remove hint suffixes
    hint_suffixes = ['_bad', '_ok', '_good', '_latent']
    for suffix in hint_suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break

    return name
```

## Dataset Statistics

Out of 523 total examples:
- **~40%** had hint suffixes/prefixes removed
- **~60%** had no hints in the name (kept as-is)

Examples:
- `_bad` suffix: ~150 functions
- `_ok` suffix: ~60 functions
- No hints: ~313 functions (e.g., `set_ptr`, `const_local_no_abduce`)

## Benefits

1. **Realistic evaluation**: Function names provide context like real code
2. **Semantic hints removed**: No direct "this is bad" indicators
3. **Better LLM performance**: Descriptive names help with understanding
4. **Maintains difficulty**: Still requires actual code analysis
5. **Preserves intent**: Original author's naming shows function purpose

## Note on "Self-Documenting" Names

Some function names like `use_after_free_simple` might seem like they give away the bug type. However:

- Real codebases often have descriptive names
- The name describes the *pattern*, not whether it's *buggy*
- LLM still needs to analyze if the pattern is *correctly* implemented
- Example: `use_after_free_simple` could be a test showing *how to avoid* UAF bugs

This makes the evaluation more realistic while avoiding direct "answer hints" like `_bad`.

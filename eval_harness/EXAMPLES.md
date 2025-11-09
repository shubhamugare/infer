# Example Evaluation Data

This file shows actual examples from the generated JSONL files.

## Example 1: Simple NULL Pointer Dereference (Has Bug)

**Original Function Name**: `malloc_no_check_bad`
**Anonymized**: `test_function_001`

**What the LLM should detect**:
- Line 3: `*p = 42;` dereferences `p` without checking if malloc returned NULL
- Bug type: NULLPTR_DEREFERENCE

---

## Example 2: Safe Function with Assert (No Bug)

**Original Function Name**: `malloc_assert_ok`
**Anonymized**: `test_function_002`

**What the LLM should detect**:
- No bugs! The `assert(p)` ensures `p` is not NULL before dereference
- Memory is properly freed

---

## Example 3: Memory Leak (Has Bug)

**Original Function Name**: `malloc_no_free_bad`
**Anonymized**: `test_function_001`

**What the LLM should detect**:
- Memory allocated with `malloc` is never freed
- Becomes unreachable when function returns
- Bug type: MEMORY_LEAK

## Statistics from Generated Files

### nullptr_basic.jsonl
- Total examples: 29
- Functions with bugs: 14
- Safe functions: 15

### memory_leak_basic.jsonl
- Total examples: 44
- Functions with bugs: 16
- Safe functions: 28

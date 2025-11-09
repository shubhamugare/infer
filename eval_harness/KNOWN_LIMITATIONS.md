# Known Limitations and False Negatives

## Summary

The dataset excludes **49 functions** that represent known issues with Infer:
- **35 FN_ functions**: False Negatives - Real bugs that Infer misses
- **14 FP_ functions**: False Positives - Infer reports bugs that don't exist

## 1. False Negatives (FN_) - Excluded from Dataset

These are **real bugs** that Infer's Pulse analyzer cannot detect due to known limitations. They are **excluded** from the evaluation dataset.

### Count: 35 functions

### Categories of Missed Bugs:

#### Array Bounds (2 examples)
```c
void FN_const_bound_too_large_bad() {
  int a[7];
  a[7] = 4;  // Out of bounds - Infer misses this
}
```

#### Divide by Zero (1 example)
```c
int FN_const_divide_by_zero_bad() {
  int x = 0;
  int y = 5;
  return y / x;  // Division by zero - Infer misses this
}
```

#### Complex Loop Analysis (6+ examples)
- Nested loops with complex conditions
- Loops with goto statements
- Loops with bitshift/modulus patterns
- Examples: `FN_nested_loop_cond_bad`, `FN_while_ge_bad`, `FN_goto_in_loop_bad`

#### Attribute-based Issues (1 example)
```c
void FN_wrong_cleanup_malloc_bad() {
  __attribute__((cleanup(no_cleanup))) int* x;
  x = malloc(sizeof(int));  // Leak - cleanup attribute doesn't work
}
```

#### Conditional Latent Issues (3+ examples)
- Bugs that depend on specific input values
- Examples: `FN_call_if_negative_then_crash_with_negative_bad`

#### Integer Conversions and Floating Point (3 examples)
- `FN_even_can_be_even_float_conv_bad`
- `FN_int_conversions_feasible_bad`
- `FN_call_float_comparison_bad`

#### Use-After-Free in Complex Scenarios (2+ examples)
- `FN_nonlatent_use_after_free_bad`
- `FN_crash_after_six_nodes_bad`

#### Other (remaining examples)
- Memory leaks in complex realloc patterns
- Taint propagation issues
- Various edge cases

### Why These Are Excluded

These functions are excluded because:
1. **Ground truth is uncertain**: We know these have bugs, but using Infer's absence of reporting as "safe" would be misleading
2. **Not useful for LLM evaluation**: LLMs might correctly identify these bugs, which would be counted as "false positives" against Infer's ground truth
3. **Keeps dataset clean**: Only includes cases where Infer's ground truth is reliable

## 2. False Positives (FP_) - Excluded from Dataset

These are functions where Infer **incorrectly reports bugs** that don't actually exist.

### Count: 14 functions

These represent over-approximations where Infer's conservative analysis flags safe code as buggy. They are also **excluded** to maintain dataset quality.

## 3. LATENT Bugs - Included in Dataset

### Count: 10 functions with LATENT bugs

**These ARE included** in the dataset with `has_bug=true`.

LATENT bugs are **real bugs** that only manifest when the function is called with specific inputs:

```c
void if_negative_then_crash_latent(int x) {
  int* p = NULL;
  if (x < 0) {
    p = NULL;
  }
  *p = 42;  // Bug: dereferences NULL when x < 0
}
```

This has bug type: `NULLPTR_DEREFERENCE_LATENT`

### Why LATENT bugs are included:
- They are real bugs (just conditional)
- Infer reports them in issues.exp
- LLMs should be able to detect them
- Good test of conditional reasoning

## 4. Safe Functions - Included in Dataset

### Count: 306 functions marked as safe

These functions have **no bugs reported** by Infer in `issues.exp`. They include:

1. **Truly safe code**: Functions with no bugs
2. **Latent helper functions**: Functions that are safe when called correctly (3 examples)
   - `latent_dereference` - dereferences parameter (safe if caller provides valid pointer)
   - `propagate_latent_2_latent` - calls latent function (safe if called correctly)
   - `propagate_latent_3_latent` - calls latent function (safe if called correctly)
3. **Code with proper null checks**: Functions that handle edge cases correctly

## Dataset Integrity

### What "safe" means in this dataset:
- **NOT**: "This code is guaranteed bug-free"
- **YES**: "Infer's Pulse analyzer reports no bugs for this function"

### What "has_bug=true" means:
- **NOT**: "This code will always crash"
- **YES**: "Infer's Pulse analyzer detected a bug (including LATENT bugs)"

## Statistics

```
Total functions in Pulse test suite: ~590
Excluded (FN_ prefix): 35 (known false negatives)
Excluded (FP_ prefix): 14 (known false positives)
Included in dataset: 523

Of included:
  - With bugs: 217 (41.5%)
    - Including LATENT: 10
  - Safe: 306 (58.5%)
```

## Implications for Evaluation

### When evaluating LLMs on this dataset:

**True Positives**: LLM detects bug AND Infer reports it
- This is good! The LLM agrees with Infer.

**False Positives**: LLM detects bug BUT Infer says safe
- Could be: LLM is wrong (actual FP)
- Could be: LLM is right and Infer missed it (like the 35 FN_ cases we excluded)
- Need manual review to distinguish

**True Negatives**: LLM says safe AND Infer says safe
- Good agreement

**False Negatives**: LLM says safe BUT Infer reports bug
- LLM missed a real bug

### Recommendation:

For fair evaluation, consider **manually reviewing** LLM "false positives" to check if they're actually correct bugs that Infer missed. The 35 excluded FN_ functions show that Infer has known blind spots.

## Known Infer Limitations (from FN_ analysis)

Infer's Pulse analyzer struggles with:
1. ✗ Array bounds checking (static indices)
2. ✗ Division by zero (even with constants)
3. ✗ Complex loop invariants
4. ✗ Goto statements in loops
5. ✗ Certain attribute-based patterns
6. ✗ Floating-point comparisons
7. ✗ Complex integer conversions
8. ✗ Some taint propagation scenarios
9. ✓ NULL pointer dereference (mostly works, but some FN)
10. ✓ Memory leaks (mostly works, but some FN with realloc)
11. ✓ Use-after-free (mostly works, but some FN in complex scenarios)

## References

- Excluded functions defined in: `infer/tests/codetoanalyze/c/pulse/*.c`
- Ground truth: `infer/tests/codetoanalyze/c/pulse/issues.exp`
- Parser exclusion logic: `eval_harness/parser.py` lines 304-306

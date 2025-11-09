# System Prompts for Evaluation

This directory contains two system prompts for evaluating LLMs on static analysis tasks, designed to trade off between recall and precision.

## Available Prompts

### 1. `system_prompt.txt` (Default - Balanced)

**Goal:** Balanced recall and precision

**Instruction:**
> "Only report bugs you are confident about"

**Use when:**
- You want a balanced evaluation
- You care equally about catching bugs and avoiding false positives
- Standard benchmarking scenario

**Expected behavior:**
- LLM reports bugs it finds with reasonable confidence
- May have some false positives if the model is too aggressive
- May have some false negatives if the model is too cautious

### 2. `system_prompt_conservative.txt` (Conservative - High Precision)

**Goal:** Maximize precision at the cost of recall

**Additional instruction:**
> "Only report bugs when you have HIGH CONFIDENCE that the bug definitely exists. When in doubt, err on the side of marking code as safe rather than reporting uncertain bugs."

**Key guidelines added:**
- If a bug requires assumptions about missing context → DO NOT report
- If the code pattern is ambiguous → DO NOT report
- Only report bugs with clear evidence in the provided code
- Better to miss a real bug (false negative) than report a non-existent bug (false positive)

**Use when:**
- LLM has high recall but low precision (many false positives)
- You want to reduce false positive rate
- You prioritize precision over recall
- Production scenarios where false alarms are costly

**Expected behavior:**
- LLM only reports bugs with strong evidence
- Lower false positive rate
- Higher false negative rate (may miss some real bugs)
- More conservative in reporting edge cases

## Trade-offs

| Metric | Default Prompt | Conservative Prompt |
|--------|----------------|---------------------|
| **Precision** | Moderate | Higher |
| **Recall** | Moderate | Lower |
| **False Positives** | More | Fewer |
| **False Negatives** | Fewer | More |
| **F1 Score** | Balanced | Precision-weighted |

## Choosing the Right Prompt

**Use Default (`system_prompt.txt`) if:**
- You're doing initial benchmarking
- You want to see what bugs the LLM can find
- You care about finding all bugs (high recall)
- You're okay with some false positives

**Use Conservative (`system_prompt_conservative.txt`) if:**
- Your LLM is too aggressive (high false positive rate)
- You observed: Recall > 80% but Precision < 60%
- You're using the LLM in production (where false alarms are costly)
- You want actionable bug reports (fewer false alarms to investigate)

## Example Scenario

**Observed behavior with default prompt:**
```
Precision: 55%  (many false positives)
Recall: 85%     (catches most bugs)
F1: 67%
```

**Expected improvement with conservative prompt:**
```
Precision: 75%  (fewer false positives)
Recall: 70%     (misses some edge cases)
F1: 72%
```

## Usage in Evaluation

When running evaluations, specify which prompt to use:

```python
# Default prompt
with open('system_prompt.txt', 'r') as f:
    system_prompt = f.read()

# Conservative prompt
with open('system_prompt_conservative.txt', 'r') as f:
    system_prompt = f.read()

# Then use in your LLM API call
response = llm.chat(
    system=system_prompt,
    user=f"Analyze this function:\n{function_code}"
)
```

## Differences Summary

The conservative prompt adds this paragraph:

```
IMPORTANT - Conservative Reporting:
Only report bugs when you have HIGH CONFIDENCE that the bug definitely exists.
When in doubt, err on the side of marking code as safe rather than reporting
uncertain bugs. Consider these guidelines:
- If a bug requires assumptions about missing context → DO NOT report
- If the code pattern is ambiguous → DO NOT report
- Only report bugs with clear evidence in the provided code
- Better to miss a real bug than to report a bug that doesn't exist
- Focus on definite bugs with clear evidence rather than potential issues
```

And changes one line in IMPORTANT section:
- Default: "Only report bugs you are confident about"
- Conservative: "Only report bugs you are HIGHLY CONFIDENT about"
- Conservative: "If code is safe OR if you're uncertain, return has_bug: false"

## Recommendation

1. **Start with default prompt** to establish baseline metrics
2. **Analyze results**: If Precision < 65% and Recall > 80%, switch to conservative
3. **Compare both prompts** to understand the precision-recall trade-off for your LLM
4. **Report both results** in your evaluation to show the full performance envelope

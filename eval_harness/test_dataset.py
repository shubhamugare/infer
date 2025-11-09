#!/usr/bin/env python3
"""
Test script to verify the uploaded Hugging Face dataset works correctly.
"""

from datasets import load_dataset

def test_dataset_load():
    """Test loading the dataset from Hugging Face."""

    print("=" * 80)
    print("Testing Hugging Face Dataset: shubhamugare/infer-pulse-eval")
    print("=" * 80)
    print()

    # Load dataset
    print("Loading dataset...")
    dataset = load_dataset("shubhamugare/infer-pulse-eval")

    print("✅ Dataset loaded successfully!")
    print()

    # Check splits
    print("Available splits:")
    for split_name in dataset.keys():
        print(f"  - {split_name}: {len(dataset[split_name])} examples")
    print()

    # Get test split
    test = dataset['test']

    # Print statistics
    print("Dataset Statistics:")
    print(f"  Total examples: {len(test)}")

    # Count bugs
    with_bugs = sum(1 for ex in test if ex['has_bug'])
    safe = len(test) - with_bugs
    print(f"  With bugs: {with_bugs} ({with_bugs/len(test)*100:.1f}%)")
    print(f"  Safe: {safe} ({safe/len(test)*100:.1f}%)")
    print()

    # Show first example
    print("First Example:")
    print("-" * 80)
    ex = test[0]
    print(f"ID: {ex['id']}")
    print(f"Source: {ex['source_file']}")
    print(f"Original name: {ex['original_function_name']}")
    print(f"Anonymized name: {ex['anonymized_function_name']}")
    print(f"Has bug: {ex['has_bug']}")
    if ex['has_bug']:
        print(f"Bug types: {ex['bug_types']}")
    print(f"Category: {ex['category']}")
    print(f"Difficulty: {ex['difficulty']}")
    print()
    print("Function code (first 300 chars):")
    print(ex['function_code'][:300])
    if len(ex['function_code']) > 300:
        print("...")
    print()

    # Show a bug example
    print("Example with Bug:")
    print("-" * 80)
    bug_example = next(ex for ex in test if ex['has_bug'])
    print(f"ID: {bug_example['id']}")
    print(f"Function: {bug_example['anonymized_function_name']}")
    print(f"Bug types: {bug_example['bug_types']}")
    print(f"Bug line offsets: {bug_example['bug_line_offsets']}")
    print()
    print("Function code:")
    print(bug_example['function_code'])
    print()

    # Test filtering
    print("Filtering Examples:")
    print("-" * 80)

    # Filter by bug type
    nullptr_bugs = [ex for ex in test if 'NULLPTR_DEREFERENCE' in ex['bug_types']]
    print(f"NULL pointer dereference examples: {len(nullptr_bugs)}")

    # Filter by category
    memory_leaks = [ex for ex in test if ex['category'] == 'memory_leak']
    print(f"Memory leak category: {len(memory_leaks)}")

    # Filter by difficulty
    advanced = [ex for ex in test if ex['difficulty'] == 'advanced']
    print(f"Advanced difficulty: {len(advanced)}")

    print()
    print("=" * 80)
    print("✅ All tests passed! Dataset is working correctly.")
    print("=" * 80)
    print()
    print("You can now use the dataset in your code:")
    print()
    print("  from datasets import load_dataset")
    print("  dataset = load_dataset('shubhamugare/infer-pulse-eval')")
    print("  test = dataset['test']")
    print()


if __name__ == '__main__':
    test_dataset_load()

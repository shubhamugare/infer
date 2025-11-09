# Dataset Changes Log

## 2025-01-XX: Removed Difficulty Field

### Change
Removed the `difficulty` field from the dataset metadata.

### Reason
The difficulty classification (basic/intermediate/advanced) was subjective and not essential for evaluation. Keeping the metadata minimal and focused on objective properties.

### What Changed
- **Removed from parser.py**: `determine_difficulty()` function
- **Removed from dataset**: `difficulty` field in metadata
- **Removed from upload script**: Difficulty statistics and schema field
- **Removed from README**: Difficulty distribution table

### Metadata Fields (Current)
- `category`: str - Bug category (nullptr_dereference, memory_leak, use_after_free, uninitialized_value, resource_leak, other, safe)
- `requires_interprocedural`: bool - Whether function calls other custom functions
- `start_line`: int - Start line in original source file
- `end_line`: int - End line in original source file

### Impact
- Dataset size: 523 examples (unchanged)
- Schema: Simplified, removed subjective classification
- Evaluations: Can still measure complexity via `requires_interprocedural` flag

### Migration
If you were using the `difficulty` field:
- Use `requires_interprocedural` to identify complex cases requiring cross-function analysis
- Use `category` to filter by bug type
- Calculate your own complexity metrics based on code characteristics

## 2025-01-XX: Added Interprocedural Context

### Change
Enhanced dataset to include complete context for interprocedural examples.

### What Changed
- **includes**: Now contains both #include statements AND struct definitions
- **dependencies**: Now contains full function code (not just names)
- Recursive struct dependency extraction (finds nested struct definitions)

### Impact
- 137 interprocedural examples now have complete function dependency code
- 74 examples include struct definitions
- 19 examples have both struct and function dependencies

See [DATASET_ENHANCEMENT.md](DATASET_ENHANCEMENT.md) for full details.

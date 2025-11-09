# Uploading to Hugging Face

This guide explains how to upload the Infer Pulse evaluation dataset to Hugging Face Hub.

## Prerequisites

Install required packages:
```bash
pip install datasets huggingface-hub
```

## Authentication

### Option 1: Interactive Login (Recommended)
```bash
source venv/bin/activate
python -c "from huggingface_hub import login; login()"
```

This will:
1. Prompt for your Hugging Face token
2. Save it securely for future use
3. No need to pass token to upload script

**Get your token**: https://huggingface.co/settings/tokens

### Option 2: Environment Variable
```bash
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
```

### Option 3: Pass Token Directly
```bash
python upload_to_huggingface.py --repo-id username/dataset-name --token hf_xxxxx
```

## Upload Dataset

### Basic Upload (Public Dataset)
```bash
python upload_to_huggingface.py --repo-id your-username/infer-pulse-eval
```

### Private Dataset
```bash
python upload_to_huggingface.py --repo-id your-username/infer-pulse-eval --private
```

### Custom Data File
```bash
python upload_to_huggingface.py \
    --repo-id your-username/infer-pulse-eval \
    --data path/to/custom_data.jsonl
```

## What Gets Uploaded

The script will:

1. **Load** the JSONL dataset (523 examples)
2. **Create test split**: All examples in test split (evaluation-only dataset)
3. **Convert format** to Hugging Face datasets structure
4. **Generate README.md** with:
   - Dataset description
   - Statistics and distribution tables
   - Usage examples
   - Citation information
5. **Upload** to Hugging Face Hub

## Dataset Structure on Hub

After upload, your dataset will have this structure:

```
your-username/infer-pulse-eval/
├── README.md              # Auto-generated documentation
└── test/                  # Test split (all 523 examples)
```

**Note:** This is an evaluation-only dataset, so all examples are in the test split.

## Using the Uploaded Dataset

Once uploaded, anyone can load it:

```python
from datasets import load_dataset

# Load dataset
dataset = load_dataset("your-username/infer-pulse-eval")

# Access test split
test = dataset['test']

# Iterate over examples
for example in test:
    print(f"Function: {example['anonymized_function_name']}")
    print(f"Has bug: {example['has_bug']}")
    if example['has_bug']:
        print(f"Bug types: {example['bug_types']}")
    print(f"Code:\n{example['function_code']}\n")
```

## Dataset Schema

Each example has these fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `source_file` | string | Source file from Infer tests |
| `original_function_name` | string | Original name with hints |
| `anonymized_function_name` | string | Name with hints removed |
| `function_code` | string | Complete C function |
| `includes` | list[string] | Required #include statements |
| `dependencies` | list[string] | Helper code needed |
| `has_bug` | bool | Whether function has bugs |
| `bug_types` | list[string] | Bug type names |
| `bug_line_offsets` | list[int] | Line numbers (relative) |
| `bug_absolute_lines` | list[int] | Line numbers (absolute) |
| `bug_severities` | list[string] | Severity levels |
| `bug_traces` | list[string] | Detailed traces |
| `category` | string | Bug category or "safe" |
| `difficulty` | string | basic/intermediate/advanced |
| `requires_interprocedural` | bool | Needs inter-function analysis |
| `start_line` | int | Start line in source |
| `end_line` | int | End line in source |

## Example Workflow

```bash
# 1. Login to Hugging Face
source venv/bin/activate
python -c "from huggingface_hub import login; login()"

# 2. Upload dataset
cd /Users/shubhamugare/infer/eval_harness
python upload_to_huggingface.py --repo-id shubhamugare/infer-pulse-eval

# 3. Test loading it
python -c "
from datasets import load_dataset
ds = load_dataset('shubhamugare/infer-pulse-eval')
print(f'Test: {len(ds[\"test\"])} examples')
print(f'First example: {ds[\"test\"][0][\"anonymized_function_name\"]}')
"
```

## Updating the Dataset

To update an existing dataset:

```bash
# Just run the upload command again with the same repo-id
python upload_to_huggingface.py --repo-id your-username/infer-pulse-eval

# It will overwrite the existing dataset
```

## Troubleshooting

### Error: "Repository not found"
- Create the repository first on https://huggingface.co/new-dataset
- Or let the script create it automatically (if you have permissions)

### Error: "Authentication required"
- Run `huggingface-cli login` first
- Or set `HF_TOKEN` environment variable
- Or pass `--token` to the script

### Error: "Permission denied"
- Check that the repo-id uses your username
- Verify your token has write permissions

### Rate Limiting
- Hugging Face has upload limits
- The dataset is ~384KB, well within limits
- If issues, try again in a few minutes

## Dataset Card Metadata

The generated README includes metadata for Hugging Face to properly categorize your dataset:

- **License**: MIT (same as Infer)
- **Task**: Text classification, text generation
- **Language**: English
- **Tags**: code, static-analysis, bug-detection, c, memory-safety
- **Size**: <1K examples

## Privacy Considerations

- **Public datasets** are visible to everyone
- **Private datasets** require authentication to access
- All code comes from Infer's public test suite
- No proprietary or sensitive code is included

## Citation

The README includes a BibTeX citation:

```bibtex
@misc{infer-pulse-eval-2024,
  title={Infer Pulse Static Analysis Evaluation Dataset},
  author={Extracted from Meta's Infer project},
  year={2024},
  url={https://github.com/facebook/infer}
}
```

## Next Steps After Upload

1. **Share** the dataset URL with your team
2. **Document** any evaluation protocols in the README
3. **Create** example notebooks showing usage
4. **Link** to any papers or blog posts using the dataset
5. **Monitor** downloads and usage statistics on Hugging Face

## Support

For issues with:
- **Upload script**: Open issue in this repo
- **Hugging Face platform**: Check https://huggingface.co/docs
- **Dataset content**: See original Infer repository

---

**Dataset URL after upload**: `https://huggingface.co/datasets/your-username/infer-pulse-eval`

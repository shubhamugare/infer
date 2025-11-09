# Setup Instructions

## Virtual Environment

A Python virtual environment has been created with all required packages installed.

### Packages Installed

- `huggingface-hub` (1.1.2) - Hugging Face Hub API and CLI
- `datasets` (4.4.1) - Hugging Face datasets library
- All dependencies (numpy, pandas, pyarrow, etc.)

### Activating the Virtual Environment

**Option 1: Use the helper script (recommended)**
```bash
./upload.sh --repo-id your-username/infer-pulse-eval
```

**Option 2: Manual activation**
```bash
# Activate virtual environment
source venv/bin/activate

# Use Python and installed packages
python upload_to_huggingface.py --repo-id your-username/infer-pulse-eval

# Deactivate when done
deactivate
```

## Uploading to Hugging Face

### Step 1: Login

First time only, login to Hugging Face:

**Option 1: Interactive login (recommended)**
```bash
# Activate venv first
source venv/bin/activate

# Login (will prompt for token)
python -c "from huggingface_hub import login; login()"

# Get your token from: https://huggingface.co/settings/tokens
```

**Option 2: Set environment variable**
```bash
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
```

**Option 3: Pass token to script**
```bash
./upload.sh --repo-id your-username/dataset --token hf_xxxxx
```

### Step 2: Upload Dataset

**Using helper script (easiest):**
```bash
./upload.sh --repo-id shubhamugare/infer-pulse-eval
```

**Manual method:**
```bash
source venv/bin/activate
python upload_to_huggingface.py --repo-id shubhamugare/infer-pulse-eval
```

**For private dataset:**
```bash
./upload.sh --repo-id shubhamugare/infer-pulse-eval --private
```

## Available Commands in Virtual Environment

Once activated (`source venv/bin/activate`):

- `python -c "from huggingface_hub import login; login()"` - Login to Hugging Face
- `python -c "from huggingface_hub import whoami; whoami()"` - Check current user
- `python upload_to_huggingface.py` - Upload dataset

## Troubleshooting

### "Not logged in"
Run:
```bash
source venv/bin/activate
python -c "from huggingface_hub import login; login()"
```

### "Repository not found"
The script will create the repository automatically on first upload.

### Need to reinstall packages
```bash
source venv/bin/activate
pip install --upgrade huggingface-hub datasets
```

## File Structure

```
eval_harness/
├── venv/                           # Virtual environment (gitignored)
├── upload.sh                       # Helper script to upload
├── upload_to_huggingface.py       # Main upload script
├── data/pulse_all_examples.jsonl  # Dataset to upload
└── system_prompt.txt              # System prompt for LLMs
```

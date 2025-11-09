# Quick Start: Upload Dataset to Hugging Face

## ✅ Setup Complete!

All dependencies are installed in a virtual environment at `venv/`.

## 🚀 Upload in 2 Steps

### 1. Login to Hugging Face

```bash
cd /Users/shubhamugare/infer/eval_harness
source venv/bin/activate
python -c "from huggingface_hub import login; login()"
```

When prompted, paste your token from: https://huggingface.co/settings/tokens

### 2. Upload Dataset

```bash
./upload.sh --repo-id shubhamugare/infer-pulse-eval
```

That's it! The script will:
- ✅ Load 523 examples from `data/pulse_all_examples.jsonl`
- ✅ Convert to Hugging Face format (test split)
- ✅ Generate comprehensive README.md
- ✅ Upload to `huggingface.co/datasets/shubhamugare/infer-pulse-eval`

## 📊 What Gets Uploaded

```
Dataset: shubhamugare/infer-pulse-eval
├── test/         (523 examples)
│   ├── 217 with bugs (42%)
│   └── 306 safe (58%)
└── README.md     (auto-generated with stats)
```

## 🔧 Advanced Options

**Private dataset:**
```bash
./upload.sh --repo-id shubhamugare/infer-pulse-eval --private
```

**Custom data file:**
```bash
./upload.sh --repo-id shubhamugare/infer-pulse-eval --data path/to/data.jsonl
```

**Pass token directly:**
```bash
./upload.sh --repo-id shubhamugare/infer-pulse-eval --token hf_xxxxx
```

## 📚 After Upload

Load your dataset anywhere:
```python
from datasets import load_dataset

dataset = load_dataset("shubhamugare/infer-pulse-eval")
test = dataset['test']

print(f"Total examples: {len(test)}")
print(f"First function: {test[0]['anonymized_function_name']}")
```

## 📖 More Info

- **[SETUP.md](SETUP.md)** - Detailed setup and troubleshooting
- **[HUGGINGFACE_UPLOAD.md](HUGGINGFACE_UPLOAD.md)** - Complete upload guide
- **[QUICKSTART.md](QUICKSTART.md)** - Dataset overview

## 🆘 Need Help?

**Not logged in?**
```bash
source venv/bin/activate
python -c "from huggingface_hub import whoami; whoami()"  # Check if logged in
python -c "from huggingface_hub import login; login()"    # Login if needed
```

**Script issues?**
```bash
source venv/bin/activate
python upload_to_huggingface.py --repo-id your-username/dataset-name
```

---

**Ready to upload?** Run: `./upload.sh --repo-id shubhamugare/infer-pulse-eval`

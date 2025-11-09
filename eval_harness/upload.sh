#!/bin/bash
# Helper script to upload dataset to Hugging Face
# Automatically activates virtual environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Check if --token is provided or HF_TOKEN is set
if [[ "$*" != *"--token"* ]] && [[ -z "$HF_TOKEN" ]]; then
    # Check if already logged in
    if ! python -c "from huggingface_hub import whoami; whoami()" 2>/dev/null; then
        echo ""
        echo "ERROR: Not logged in to Hugging Face."
        echo ""
        echo "Please login first by running:"
        echo "  source venv/bin/activate"
        echo "  python -c \"from huggingface_hub import login; login()\""
        echo ""
        echo "Or set HF_TOKEN environment variable:"
        echo "  export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx"
        echo ""
        echo "Or pass token to script:"
        echo "  ./upload.sh --repo-id your-username/dataset --token hf_xxxxx"
        echo ""
        echo "Get your token from: https://huggingface.co/settings/tokens"
        echo ""
        exit 1
    fi
fi

# Run upload script
echo "Starting upload..."
python upload_to_huggingface.py "$@"

echo ""
echo "Done!"

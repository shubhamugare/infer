#!/bin/bash
# Generate evaluation data from ALL C test files in pulse directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR/../infer/tests/codetoanalyze/c/pulse"
ISSUES_EXP="$TEST_DIR/issues.exp"
OUTPUT_FILE="$SCRIPT_DIR/data/pulse_all_examples.jsonl"

echo "=========================================="
echo "Generating Eval Data from All Pulse Tests"
echo "=========================================="
echo ""
echo "Test directory: $TEST_DIR"
echo "Issues file: $ISSUES_EXP"
echo "Output file: $OUTPUT_FILE"
echo ""

# Clean previous output
rm -f "$OUTPUT_FILE"

# Count C files
total_files=$(find "$TEST_DIR" -maxdepth 1 -name "*.c" -type f | wc -l | tr -d ' ')
echo "Found $total_files C files to process"
echo ""

# Process each C file
count=0
total_examples=0

for c_file in "$TEST_DIR"/*.c; do
    if [ -f "$c_file" ]; then
        count=$((count + 1))
        filename=$(basename "$c_file")

        echo "[$count/$total_files] Processing $filename..."

        # Generate to temporary file
        temp_file=$(mktemp)

        python3 "$SCRIPT_DIR/parser.py" \
            --test-file "$c_file" \
            --issues-exp "$ISSUES_EXP" \
            --output "$temp_file" 2>&1 | grep "Generated" || true

        # Append to main output file
        if [ -f "$temp_file" ]; then
            cat "$temp_file" >> "$OUTPUT_FILE"
            examples=$(wc -l < "$temp_file" | tr -d ' ')
            total_examples=$((total_examples + examples))
            rm "$temp_file"
        fi
    fi
done

echo ""
echo "=========================================="
echo "COMPLETE!"
echo "=========================================="
echo ""
echo "Total files processed: $count"
echo "Total examples generated: $total_examples"
echo ""
echo "Output file: $OUTPUT_FILE"
echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "View first example:"
echo "  head -1 $OUTPUT_FILE | python3 -m json.tool"
echo ""
echo "Count by category:"
echo '  python3 -c "import json; from collections import Counter; examples = [json.loads(line) for line in open(\"'$OUTPUT_FILE'\")]; print(Counter(ex[\"metadata\"][\"category\"] for ex in examples))"'
echo ""

#!/bin/bash

# -----------------------------
# Configuration
# -----------------------------
HMMBIN="/scratch/project_2002833/VG/software/hmmer-3.4/bin" # ← Change this to your actual path
HMM_DIR="hmm_models"
HMM_FILE="Pfam-A.hmm"
CSV_FILE="fungal_tf_domains.csv"
ACCESSION_LIST="accession_list.txt"
OUTPUT_HMM="$HMM_DIR/fungal_TF_selected.hmm"

# -----------------------------
# Check executables
# -----------------------------
HMMFETCH_BIN="$HMMBIN/hmmfetch"
HMMPRESS_BIN="$HMMBIN/hmmpress"

if [ ! -x "$HMMFETCH_BIN" ]; then
    echo "❌ hmmfetch not found or not executable at $HMMFETCH_BIN"
    exit 1
fi

if [ ! -x "$HMMPRESS_BIN" ]; then
    echo "❌ hmmpress not found or not executable at $HMMPRESS_BIN"
    exit 1
fi

echo "🛠 Using HMMER tools in: $HMMBIN"

# -----------------------------
# Check input files
# -----------------------------
if [ ! -f "$CSV_FILE" ]; then
    echo "❌ CSV file not found: $CSV_FILE"
    exit 1
fi

if [ ! -f "$HMM_FILE" ]; then
    echo "❌ Pfam-A HMM file not found: $HMM_FILE"
    exit 1
fi

# -----------------------------
# Step 1: Extract accession list
# -----------------------------
echo "📄 Extracting accessions from $CSV_FILE..."
cut -d',' -f1 "$CSV_FILE" | grep -E "^PF[0-9]{5}" | sort -u > "$ACCESSION_LIST"
echo "✅ Saved $(wc -l < "$ACCESSION_LIST") accessions to $ACCESSION_LIST"

# -----------------------------
# Step 2: Extract HMMs
# -----------------------------
echo "🚀 Extracting HMMs to $OUTPUT_HMM..."
"$HMMFETCH_BIN" -f "$HMM_FILE" "$ACCESSION_LIST" > "$OUTPUT_HMM"
echo "🎉 Done! Extracted HMMs saved to: $OUTPUT_HMM"

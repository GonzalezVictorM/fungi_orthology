#!/usr/bin/env bash
set -euo pipefail

# --- User settings ---
DATA_DIR="local_data"
DATA_DIR="$(readlink -f "$DATA_DIR")"

IN_DIR="$DATA_DIR/proteomes/test"
OUT_DIR="$DATA_DIR/interproscan_results"
LOG_DIR="$DATA_DIR/logs"

THREADS=16
FORMAT="TSV"
SEQTYPE="p"
APPLICATIONS="CDD,Pfam,PANTHER,SMART,SUPERFAMILY"

# Throttle: max number of *top-level* cluster_interproscan jobs in queue
MAX_ACTIVE=3

# --- Prep ---
mkdir -p "$OUT_DIR" "$LOG_DIR"
shopt -s nullglob
mapfile -t FA_FILES < <(printf '%s\0' "$IN_DIR"/*.fasta | xargs -0 -n1 -I{} realpath "{}")

if (( ${#FA_FILES[@]} == 0 )); then
    echo "No FASTA files found in $IN_DIR"
    exit 1
fi

echo "Found ${#FA_FILES[@]} FASTA files."
echo "Submitting with MAX_ACTIVE=$MAX_ACTIVE"

submitted=0
skipped=0

# Helper: count active jobs with our name prefix
job_count() {
    squeue -u "$USER" -h -o "%j" | awk '/^iprscan_/ {c++} END{print c+0}'
}

for FASTA in "${FA_FILES[@]}"; do
    echo
    echo "----------------------------------------"
    BASENAME="$(basename "$FASTA")"
    STEM="${BASENAME%.*}"
    OUT_BASENAME="$OUT_DIR/${STEM}"

    # Skip if final output exists
    if [[ -s "${OUT_BASENAME}.tsv.gz" ]] || \
        [[ -s "${OUT_BASENAME}.tsv"   ]] || \
        [[ -s "${OUT_BASENAME}"       ]]; then
        echo "[SKIP] $BASENAME -> output exists (${OUT_BASENAME}.tsv[.gz])"
        ((skipped++)) || true
        continue
    fi

    # Throttle top-level submissions
    while true; do
        ACTIVE=$(job_count)
        if (( ACTIVE < MAX_ACTIVE )); then
            break
        fi
        echo "[WAIT] Active iprscan jobs: $ACTIVE (limit $MAX_ACTIVE). Sleeping 60s..."
        sleep 60
    done

    # Clean '*' into a temp copy (headers kept)
    CLEANED="${OUT_DIR}/${STEM}.clean.fasta"
    sed -e '/^>/! s/\*//g' "$FASTA" > "$CLEANED"

    # Unique job name per proteome helps filtering
    JOB_NAME="iprscan_${STEM}"
    SUBMIT_LOG="${LOG_DIR}/${JOB_NAME}.submit.log"

    echo "[SUBMIT] $BASENAME as $JOB_NAME"
    {
        echo "===== cluster_interproscan submit ====="
        date
        echo "User:     $USER"
        echo "JobName:  $JOB_NAME"
        echo "Input:    $CLEANED"
        echo "Output:   $OUT_BASENAME"
        echo "Threads:  $THREADS"
        echo "Format:   $FORMAT"
        echo "SeqType:  $SEQTYPE"
        echo "Apps:     $APPLICATIONS"
    } > "$SUBMIT_LOG"

    if (
        cluster_interproscan \
            -i "$CLEANED" \
            -f "$FORMAT" \
            --cpu "$THREADS" \
            -o "$OUT_BASENAME" \
            -t "$SEQTYPE" \
            -appl "$APPLICATIONS" \
            --goterms \
            --pathways \
            >> "$SUBMIT_LOG" 2>&1
        ) & then
        ((submitted++))
        echo "[OK] Submitted $JOB_NAME (details: $SUBMIT_LOG)"
        # Optional: rm -f "$CLEANED" || true
    else
        echo "[WARN] Submission failed for $BASENAME (see $SUBMIT_LOG)"
    fi

    # Give SLURM a few seconds to register the job
    sleep 5

done

# Wait for all backgrounded submissions to finish
wait

echo
echo "=== Submission summary ==="
echo "Submitted: $submitted"
echo "Skipped:   $skipped"
echo "Active now (all jobs): $(squeue -u "$USER" -h | wc -l | tr -d ' ')"
echo "Active iprscan jobs:   $(job_count)"
echo "Outputs:   $OUT_DIR"
echo "Logs:      $LOG_DIR"

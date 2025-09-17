#!/usr/bin/env bash
set -euo pipefail

# --- User settings ---
DATA_DIR="local_data"
DATA_DIR="$(readlink -f "$DATA_DIR")"

IN_DIR="$DATA_DIR/proteomes/test"
OUT_DIR="$DATA_DIR/interproscan_results"
LOG_DIR="$DATA_DIR/logs"
THREADS=16                          # threads per InterProScan *subtask*
FORMAT="TSV"
SEQTYPE="p"
APPLICATIONS="CDD,Pfam,PANTHER,SMART,SUPERFAMILY"

# Throttle: max number of *top-level* cluster_interproscan jobs in queue
MAX_ACTIVE=2                       # tune to your project limits

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
  # Grep by name prefix to avoid counting unrelated jobs
  squeue -u "$USER" -h -o "%j" | grep -E "^iprscan_" | wc -l | tr -d ' '
}

for FASTA in "${FA_FILES[@]}"; do
  BASENAME="$(basename "$FASTA")"
  STEM="${BASENAME%.*}"
  OUT_BASENAME="$OUT_DIR/${STEM}"

  # Skip if final output exists
  if [[ -s "${OUT_BASENAME}.tsv.gz" || -s "${OUT_BASENAME}.tsv" || -s "${OUT_BASENAME}"]]; then
    echo "[SKIP] $BASENAME -> output exists (${OUT_BASENAME}.tsv[.gz])"
    ((skipped++))
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

  # Clean '*' into a temp copy (headers kept). Keep per-proteome temp under OUT_DIR.
  CLEANED="${OUT_DIR}/${STEM}.clean.fasta"
  sed -e '/^>/! s/\*//g' "$FASTA" > "$CLEANED"

  # Unique job name per proteome helps filtering
  JOB_NAME="iprscan_${STEM}"

  # Submit via the Puhti wrapper. It will create its own sub array.
  # NOTE: cluster_interproscan typically takes a basename for -o (no .tsv),
  # and writes logs in your cwd or a set log dir; adjust if your module differs.
  echo "[SUBMIT] $BASENAME -> ${OUT_BASENAME} (cpu=$THREADS)"
  module load interproscan >/dev/null 2>&1 || true

  # Most wrappers submit with sbatch internally and return fast.
  # We also tee stdout/stderr to logs for traceability.
  {
    echo "Submitting $JOB_NAME at $(date)"
    echo "Input:    $CLEANED"
    echo "Output:   $OUT_BASENAME"
    echo "Threads:  $THREADS"
    echo "Apps:     $APPLICATIONS"
  } > "${LOG_DIR}/${JOB_NAME}.submit.log"

  # The actual wrapper call
  if cluster_interproscan \
        -i "$CLEANED" \
        -f "$FORMAT" \
        --cpu "$THREADS" \
        -o "$OUT_BASENAME" \
        -t "$SEQTYPE" \
        -appl "$APPLICATIONS" \
        --goterms \
        --pathways \
        --jobname "$JOB_NAME" \
        >> "${LOG_DIR}/${JOB_NAME}.submit.log" 2>&1; then
    ((submitted++))
  else
    echo "[WARN] Submission failed for $BASENAME (see ${LOG_DIR}/${JOB_NAME}.submit.log)"
    # keep going to the next file
  fi

done

echo "=== Submission summary ==="
echo "Submitted: $submitted"
echo "Skipped:   $skipped"
echo "Active now: $(squeue -u "$USER" -h | wc -l | tr -d ' ') jobs total; $(squeue -u "$USER" -h -o "%j" | grep -E "^iprscan_" | wc -l | tr -d ' ') iprscan."
echo "Outputs:   $OUT_DIR"
echo "Logs:      $LOG_DIR"

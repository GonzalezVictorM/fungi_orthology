#!/bin/bash
#SBATCH --account=project_2015320
#SBATCH --job-name=iprscan_batch
#SBATCH --output=local_data/logs/%x_%j.out
#SBATCH --error=local_data/logs/%x_%j.stderr
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=2G
#SBATCH --partition=small

set -euo pipefail

echo "=== Job started at $(date) ==="
echo "SLURM job ID:       ${SLURM_JOB_ID:-N/A}"
echo "Submission dir:     ${SLURM_SUBMIT_DIR:-N/A}"
echo "Working dir (pwd):  $(pwd)"

mkdir -p "${SLURM_SUBMIT_DIR:-.}/local_data/logs" || true

# === Threads/memory info  ===
#THREADS="${SLURM_CPUS_PER_TASK:-1}"
THREADS=16
echo "Threads (SLURM_CPUS_PER_TASK): $THREADS"    
echo "Mem per CPU: ${SLURM_MEM_PER_CPU:-unknown}" 
echo "Total mem:   ${SLURM_MEM_PER_NODE:-unknown}"

# === Load required modules ===
module load biokit
module load interproscan

# === Define directories ===
DATA_DIR="local_data"
DATA_DIR="$(readlink -f "$DATA_DIR")"

SET_DIR="$DATA_DIR/proteomes"
IN_DIR="$SET_DIR/final"
OUT_DIR="$DATA_DIR/interproscan_results"

mkdir -p "$OUT_DIR"

echo "Input dir:   $IN_DIR"
echo "Output dir:  $OUT_DIR"

# === InterProScan config ===
SEQTYPE="p"                            # protein
FORMAT="TSV"
APPLICATIONS="CDD,Pfam,PANTHER,SMART,SUPERFAMILY"

# === Iterate over all FASTA files ===
shopt -s nullglob
fa_list=("$IN_DIR"/*.fasta)

if (( ${#fa_list[@]} == 0 )); then
  echo "ERROR: No FASTA files found in $IN_DIR"
  exit 1
fi

processed=0
skipped=0
failed=0

for FASTA in "${fa_list[@]}"; do
  BASENAME="$(basename "$FASTA")"
  STEM="${BASENAME%.*}"
  OUT_BASENAME="$OUT_DIR/${STEM}"

  # Skip if any usable output already exists
  if [[ -s "${OUT_BASENAME}.tsv.gz" || -s "${OUT_BASENAME}.tsv" ]]; then
    echo "[SKIP] $BASENAME -> output exists (${OUT_BASENAME}.tsv[.gz])"
    ((skipped++))
    continue
  fi

  if [[ ! -s "$FASTA" ]]; then
    echo "[WARN] $BASENAME is missing or empty, skipping."
    ((skipped++))
    continue
  fi

  # Clean '*' from sequence lines to a temp file (headers kept)
  CLEANED="${SLURM_TMPDIR:-/tmp}/${STEM}.clean.fasta"
  sed -e '/^>/! s/\*//g' "$FASTA" > "$CLEANED"

  echo "[RUN ] $BASENAME -> $OUT_BASENAME (cpu=$THREADS, type=$SEQTYPE)"
  if cluster_interproscan \
        -i "$CLEANED" \
        -f "$FORMAT" \
        --cpu "$THREADS" \
        -o "$OUT_BASENAME" \
        -t "$SEQTYPE" \
        -appl "$APPLICATIONS" \
        --goterms \
        --pathways; then
    # Compress TSV if produced
    if [[ -s "${OUT_BASENAME}.tsv" ]]; then
      gzip -f "${OUT_BASENAME}.tsv" || true
    fi
    ((processed++))
    echo "[DONE] $BASENAME"
  else
    ((failed++))
    echo "[FAIL] $BASENAME (see SLURM stderr for details)"
  fi

  rm -f "$CLEANED" || true
done

echo "=== Summary ==="
echo "Processed: $processed"
echo "Skipped  : $skipped"
echo "Failed   : $failed"
echo "Outputs  : $OUT_DIR"
echo "=== Job ended at $(date) ==="
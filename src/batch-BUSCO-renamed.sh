#!/bin/bash

#SBATCH --account=project_2015320
#SBATCH --job-name=busco_batch
#SBATCH --output=local_data/logs/%x_%j.out
#SBATCH --error=local_data/logs/%x_%j.stderr
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=2G
#SBATCH --partition=small

set -euo pipefail

echo "=== Job started at $(date) ==="
echo "SLURM job ID:       ${SLURM_JOB_ID:-N/A}"
echo "Submission dir:     ${SLURM_SUBMIT_DIR:-N/A}"
echo "Working dir (pwd):  $(pwd)"

mkdir -p "${SLURM_SUBMIT_DIR:-.}/local_data/logs" || true

# === Define paths to executables ===
export PATH="/scratch/project_2015320/software/busco_env/bin:$PATH"

# Verify BUSCO is available
if ! command -v busco >/dev/null 2>&1; then       
  echo "ERROR: 'busco' not found on PATH." >&2    
  exit 127
fi
echo "BUSCO version: $(busco --version || true)"  

# === Threads/memory info  ===
THREADS="${SLURM_CPUS_PER_TASK:-1}"
echo "Threads (SLURM_CPUS_PER_TASK): $THREADS"    
echo "Mem per CPU: ${SLURM_MEM_PER_CPU:-unknown}" 
echo "Total mem:   ${SLURM_MEM_PER_NODE:-unknown}"

# === Define directories ===
DATA_DIR="local_data"
DATA_DIR="$(readlink -f "$DATA_DIR")"

SEQ_DIR="$DATA_DIR/proteomes/renamed"
OUT_DIR="$DATA_DIR/BUSCO_results"
DB_DIR="$DATA_DIR/busco_downloads"

mkdir -p "$OUT_DIR" "$DB_DIR"

echo "Input dir:   $SEQ_DIR"
echo "Output dir:  $OUT_DIR"
echo "Download dir:$DB_DIR"

# Input validation
if [[ ! -d "$SEQ_DIR" ]]; then
  echo "ERROR: Input directory not found: $SEQ_DIR" >&2
  exit 1
fi
if ! find "$SEQ_DIR" -type f \( -name '*.fa' -o -name '*.faa' -o -name '*.fasta' -o -name '*.fna' \) -print -quit | grep -q . ; then
  echo "WARNING: No FASTA-like files detected under $SEQ_DIR. BUSCO may do nothing." >&2
fi

# === Run the BUSCO pipeline ===
LINEAGE="fungi_odb12"      # change if needed
RUN_NAME="busco_renamed"   # just a label, not a path

echo "Running BUSCO pipeline..."
echo "busco -c $THREADS -i $SEQ_DIR -m prot -l $LINEAGE -f --out $RUN_NAME --out_path $OUT_DIR --download_path $DB_DIR"
busco -c $THREADS -i "$SEQ_DIR" -m prot -l "$LINEAGE" -f --out "$RUN_NAME" --out_path "$OUT_DIR" --download_path "$DB_DIR"

echo "Pipeline complete!"
echo "=== Job ended at $(date) ==="

#!/bin/bash
#SBATCH --account=project_2002833
#SBATCH --job-name=iprscan_batch
#SBATCH --output=local_data/logs/%x_%j.out
#SBATCH --error=local_data/logs/%x_%j.stderr
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=8G
#SBATCH --partition=small

echo "=== Job started at $(date) ==="
echo "SLURM job ID: $SLURM_JOB_ID"
echo "Working dir: $(pwd)"

# === Load required modules ===
module load biokit
module load interproscan

# === Define directories ===
DATA_DIR="local_data"
SET_DIR="$DATA_DIR/proteomes"
IN_DIR="$SET_DIR/iprscan"
OUT_DIR="$DATA_DIR/interproscan"
LOGS_DIR="$DATA_DIR/logs/msa_array"

mkdir -p "$OUT_DIR" "$LOGS_DIR"

# Resolve to absolute paths (safer for SLURM nodes)
IN_DIR="$(readlink -f "$IN_DIR")"
OUT_DIR="$(readlink -f "$OUT_DIR")"
SET_DIR="$(readlink -f "$SET_DIR")"
LOGS_DIR="$(readlink -f "$LOGS_DIR")"

# === Inputs ===
FASTA="$IN_DIR/Dicsqu464_2.fasta"
SEQTYPE="p"

# Sanity checks
if [[ ! -s "$FASTA" ]]; then
  echo "ERROR: FASTA not found or empty: $FASTA"
  exit 1
fi

BASENAME="$(basename "$FASTA")"
STEM="${BASENAME%.*}"
OUT_BASENAME="$OUT_DIR/${STEM}"

# === Configure the interproscan run ===
THREADS=$SLURM_CPUS_PER_TASK
FORMAT="TSV"
# APPLICATIONS="CDD,Pfam,FunFam,NCBIfam,PANTHER,PIRSR,PRINTS,SFLD,SMART,SUPERFAMILY"
APPLICATIONS="CDD,Pfam,PANTHER,SMART,SUPERFAMILY"

# Sentinel to avoid clobbering existing outputs
SENTINEL="${OUT_BASENAME}.tsv"
if [[ -s "$SENTINEL" ]]; then
  echo "Output exists ($SENTINEL); exiting."
  exit 0
fi

# === Run and measure ===
echo "Running InterProScan"
echo "Input    : $FASTA (seqtype=$SEQTYPE)"
echo "Threads  : $THREADS"
echo "Mem      : ${SLURM_MEM_PER_NODE:-${SLURM_MEM_PER_CPU:-?}}"
echo "Out base : $OUT_BASENAME"

cluster_interproscan -i "$FASTA" -f "$FORMAT" --cpu "$THREADS" -o "$OUT_BASENAME" -t "$SEQTYPE" -appl "$APPLICATIONS" --goterms --pathways

gzip -f "${OUT_BASENAME}.tsv" || true

echo "Pipeline complete!"
echo "=== Job ended at $(date) ==="

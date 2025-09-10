#!/bin/bash

#SBATCH --account=project_2002833
#SBATCH --job-name=busco_batch
#SBATCH --output=local_data/logs/%x_%j.out
#SBATCH --error=local_data/logs/%x_%j.stderr
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=2G 
#SBATCH --partition=small

echo "=== Job started at $(date) ==="
echo "SLURM job ID: $SLURM_JOB_ID"
echo "Working dir: $(pwd)"

# === Define paths to executables ===
export PATH="/scratch/project_2002833/VG/software/buscoenv/bin:$PATH"

# === Set number of threads from SLURM ===
THREADS=$SLURM_CPUS_PER_TASK

# === Define directories ===
DATA_DIR="local_data"
DATA_DIR="$(readlink -f "$IN_DIR")"

SEQ_DIR="$DATA_DIR/proteomes/renamed"
OUTPUT_DIR="$DATA_DIR/BUSCO_results/renamed" # A new directory name
echo "Input dir: $SEQ_DIR"

# === Create output directories ===
mkdir -p "$OUTPUT_DIR"

# === Run the BUSCO pipeline ===
echo "Running BUSCO pipeline..."

busco -c $THREADS -i "$SEQ_DIR" -m prot -l fungi_odb12 -f --out "$OUTPUT_DIR" 

echo "Pipeline complete!"
echo "=== Job ended at $(date) ==="

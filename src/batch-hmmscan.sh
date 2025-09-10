#!/bin/bash
#SBATCH --job-name=hmmscan_tf
#SBATCH --output=hmmscan_out_%j.txt
#SBATCH --error=hmmscan_err_%j.txt
#SBATCH --time=04:00:00
#SBATCH --partition=small
#SBATCH --ntasks=1
#SBATCH --nodes=1  
#SBATCH --cpus-per-task=4
#SBATCH --account=project_2002833
#SBATCH --mem=8000

# -----------------------------
# Load required modules
# -----------------------------
module load biokit  # loads HMMER on Puhti

# -----------------------------
# Config
# -----------------------------
WORK_DIR="/scratch/project_2002833/VG/bhr1_phylogeny"
HMM_FILE="${WORK_DIR}/hmm_models/fungal_TF_selected.hmm"
PROTEOME_DIR="${WORK_DIR}/proteome_files/renamed_files"
OUTPUT_DIR="${WORK_DIR}/hmmscan_results"

mkdir -p "$OUTPUT_DIR"

# -----------------------------
# Run hmmscan on all proteomes
# -----------------------------
for fasta in "$PROTEOME_DIR"/*.fasta; do
    base=$(basename "$fasta" .fasta)
    out="${OUTPUT_DIR}/${base}.domtblout"

    echo "🔍 Scanning $fasta..."
    hmmscan --cpu $SLURM_CPUS_PER_TASK \
            --domtblout "$out" \
            "$HMM_FILE" \
            "$fasta"
done

echo "✅ All scans completed. Results in: $OUTPUT_DIR"


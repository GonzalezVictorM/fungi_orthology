#!/bin/bash

#SBATCH --account=project_2002833
#SBATCH --job-name=phylo_pipeline
#SBATCH --output=local_data/logs/%x_%j.out
#SBATCH --error=local_data/logs/%x_%j.stderr
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=4G
#SBATCH --partition=small

echo "=== Job started at $(date) ==="
echo "SLURM job ID: $SLURM_JOB_ID"
echo "Working dir: $(pwd)"

# === Load MAFFT ===
module load mafft

# === Define paths to executables ===
TRIMAL_BIN="/scratch/project_2002833/VG/software/trimal-1.5.0/source/trimal"
IQTREE_BIN="/scratch/project_2002833/VG/software/iqtree-3.0.1-Linux/bin/iqtree3"

echo "Using biokit module MAFFT: "
mafft --version
echo "Using trimAl: $TRIMAL_BIN"
"$TRIMAL_BIN" --version
echo "Using IQ-TREE: $IQTREE_BIN"
"$IQTREE_BIN" --version

# === Set number of threads from SLURM ===
THREADS=$SLURM_CPUS_PER_TASK

# === Define directories ===
SEQ_DIR="local_data/phylogeny_analysis/seq_files"
ALIGN_DIR="local_data/phylogeny_analysis/seq_alignments"
TRIM_DIR="local_data/phylogeny_analysis/trimmed_alignments"
TREE_DIR="local_data/phylogeny_analysis/iqtree_files"
LOGS_DIR="local_data/logs"

# === Create output directories ===
mkdir -p "$ALIGN_DIR" "$TRIM_DIR" "$TREE_DIR" "$LOGS_DIR"

# === Step 1: Align with MAFFT ===
echo "Running MAFFT alignments..."
for file in "$SEQ_DIR"/*; do
    base=$(basename "$file")
    out="$ALIGN_DIR/${base%.fa}_mafft.fa"
    if [[ -f "$out" ]]; then
        echo "Skipping MAFFT for $file (output exists)"
        continue
    fi
    # echo "Running mafft --thread $THREADS --retree 2 --maxiterate 1000 --op 1.53 --ep 0.123  $file > $out"
    # mafft --thread $THREADS --retree 2 --maxiterate 1000 --op 1.53 --ep 0.123 "$file" > "$out"
    echo "Running mafft --thread $THREADS --retree 2 --maxiterate 1000 $file > $out"
    mafft --thread $THREADS --retree 2 --maxiterate 1000 "$file" > "$out"
done

# === Step 2: Trim alignments with trimAl ===
echo "Trimming alignments with trimAl..."
for file in "$ALIGN_DIR"/*; do
    base=$(basename "$file")
    out="$TRIM_DIR/${base%.fa}_80trim.fa"
    if [[ -f "$out" ]]; then
        echo "Skipping trimAl for $file (output exists)"
        continue
    fi
    echo "Running $TRIMAL_BIN -in $file -gt 0.8 -cons 10 -out $out"
    "$TRIMAL_BIN" -in "$file" -gt 0.8 -cons 10 -out "$out"
done

# === Step 3: Build trees with IQ-TREE ===
echo "Building trees from trimmed alignments..."
for file in "$TRIM_DIR"/*; do
    base=$(basename "$file" .fa)
    out="$TREE_DIR/$base.treefile"
    if [[ -f "$out" ]]; then
        echo "Skipping IQ-TREE for $file (output exists)"
        continue
    fi
    echo "Running $IQTREE_BIN -s $file -m MFP -T $THREADS -B 1000 -alrt 1000 -pre $TREE_DIR/$base"
    "$IQTREE_BIN" -s "$file" -m MFP -T $THREADS -B 1000 -alrt 1000 -pre "$TREE_DIR/$base"
done

# === Step 4: Build trees for septin alignments ===
echo "Building trees for 'septin' alignments..."
for file in "$ALIGN_DIR"/*septin*; do
    base=$(basename "$file" .fa)
    out="$TREE_DIR/${base}_septin.treefile"
    if [[ -f "$out" ]]; then
        echo "Skipping septin IQ-TREE for $file (output exists)"
       continue
    fi
    echo "Running $IQTREE_BIN -s $file -m MFP -T $THREADS -B 1000 -alrt 1000 -pre $TREE_DIR/${base}_septin"
    "$IQTREE_BIN" -s "$file" -m MFP -T $THREADS -B 1000 -alrt 1000 -pre "$TREE_DIR/${base}_septin"
done

echo "Pipeline complete!"
echo "=== Job ended at $(date) ==="

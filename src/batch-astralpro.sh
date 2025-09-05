#!/bin/bash
#SBATCH --account=project_2002833
#SBATCH --job-name=clean_astral_trees
#SBATCH --output=local_data/logs/%x_%j.out
#SBATCH --error=local_data/logs/%x_%j.stderr
#SBATCH --time=1:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8 
#SBATCH --mem-per-cpu=1G
#SBATCH --partition=small

# === Load the module ===
module load gcc
module load biopythontools

# === Create the directories ===
mkdir -p local_data/logs

# === Run the python code === 
python clean_astral_trees_par.py


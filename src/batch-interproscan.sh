#!/bin/bash
#SBATCH --account=project_2015320
#SBATCH --job-name=launch_iprscan
#SBATCH --output=local_data/logs/launch_iprscan_%J.out
#SBATCH --error=local_data/logs/launch_iprscan_%J.stderr
#SBATCH --time=48:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1 
#SBATCH --mem-per-cpu=2G
#SBATCH --partition=small

module load biokit

module load interproscan

chmod +x src/iprscan-launcher.sh

srun src/iprscan-launcher.sh
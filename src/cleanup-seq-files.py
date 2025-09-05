import os
import sys
from Bio import SeqIO

# Add project root to sys.path only here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import RENAMED_PROTEOMES_DIR, CLEAN_PROTEOMES_DIR
from src.utils.wrangleutils import validate_directories

# Define length limits
UPPER_LENGTH = 10000
LOWER_LENGTH = 50

def main():
    # Validate input directories
    validate_directories([RENAMED_PROTEOMES_DIR])

    # Create output directory if missing
    os.makedirs(CLEAN_PROTEOMES_DIR, exist_ok=True)

    # List all FASTA files
    proteome_files = [
        os.path.join(RENAMED_PROTEOMES_DIR, f)
        for f in os.listdir(RENAMED_PROTEOMES_DIR)
        if f.endswith(".fasta")
    ]

    if not proteome_files:
        raise FileNotFoundError(f"No FASTA files found in {RENAMED_PROTEOMES_DIR}.")

    for file_name in proteome_files:
        print(f"Processing file: {os.path.basename(file_name)}")
        sequences = list(SeqIO.parse(file_name, "fasta"))
        if not sequences:
            print(f"Warning: No sequences found in {os.path.basename(file_name)}. Skipping this file.")
            continue

        # Filter by length
        output_sequences = [
            seq for seq in sequences
            if LOWER_LENGTH <= len(seq) <= UPPER_LENGTH
        ]

        # Save filtered sequences
        output_file = os.path.join(CLEAN_PROTEOMES_DIR, os.path.basename(file_name))
        SeqIO.write(output_sequences, output_file, "fasta")
        print(f"Successfully filtered {len(sequences)} sequences from {os.path.basename(file_name)} into {len(output_sequences)} sequences saved to {output_file}")

    print("Filtering complete for all proteomes.")

if __name__ == "__main__":
    main()
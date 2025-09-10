import os
import sys
import csv
from Bio import SeqIO

# Add project root to sys.path only here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROTEOMES_DIR, FINAL_PROTEOMES_DIR, CLEAN_PROTEOMES_DIR
from src.utils.wrangleutils import validate_directories

# Define length limits
UPPER_LENGTH = 10000
LOWER_LENGTH = 50

def main():
    # Validate input directories
    validate_directories([FINAL_PROTEOMES_DIR])

    # Create output directory if missing
    os.makedirs(CLEAN_PROTEOMES_DIR, exist_ok=True)

    # List all FASTA files
    proteome_files = [
        os.path.join(FINAL_PROTEOMES_DIR, f)
        for f in os.listdir(FINAL_PROTEOMES_DIR)
        if f.endswith(".fasta")
    ]

    if not proteome_files:
        raise FileNotFoundError(f"No FASTA files found in {FINAL_PROTEOMES_DIR}.")
    # Prepare CSV log
    log_path = os.path.join(PROTEOMES_DIR, "cleaned_proteomes_log.csv")
    with open(log_path, "w", newline="") as log_f:
        writer = csv.writer(log_f)
        writer.writerow(["portal", "total_sequences", "kept_sequences", "dropped_sequences"])
        
        for file_name in proteome_files:
            portal = os.path.basename(file_name).replace(".fasta", "")
            print(f"Processing file: {os.path.basename(file_name)}")
            
            sequences = list(SeqIO.parse(file_name, "fasta"))
            if not sequences:
                print(f"Warning: No sequences found in {os.path.basename(file_name)}. Skipping this file.")
                # still log the portal with zeros
                writer.writerow([portal, 0, 0, 0])
                continue

            # Filter by length
            output_sequences = [
                seq for seq in sequences
                if LOWER_LENGTH <= len(seq) <= UPPER_LENGTH
            ]

            # Save filtered sequences
            output_file = os.path.join(CLEAN_PROTEOMES_DIR, os.path.basename(file_name))
            SeqIO.write(output_sequences, output_file, "fasta")

            total = len(sequences)
            kept = len(output_sequences)
            dropped = total - kept
            writer.writerow([portal, total, kept, dropped])

            print(
                f"Successfully filtered {total} sequences from {portal} into {kept} sequences "
                f"saved to {output_file}"
            )

    print("Filtering complete for all proteomes.")

if __name__ == "__main__":
    main()
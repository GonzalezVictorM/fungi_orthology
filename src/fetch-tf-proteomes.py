import os
import pandas as pd
from Bio import SeqIO

# -----------------------------
# Configuration
# -----------------------------
proteome_dir = "local_data/proteome_tfs"
proteome_tfs_dir = "local_data/proteome_tfs"
hmm_results_dir = "local_data/hmmscan_results"
input_csv = os.path.join(proteome_dir, "proteome_list_with_renamed_files.csv")
renamed_dir = os.path.join(proteome_dir, "renamed_files")
output_dir = os.path.join(proteome_dir, "clean")
os.makedirs(output_dir, exist_ok=True)

# -----------------------------
# Load data
# -----------------------------
proteome_data = pd.read_csv(input_csv)

# -----------------------------
# Function to parse domtblout file
# -----------------------------
def parse_domtblout(domtblout_path):
    """Parse HMMER3 domtblout file and return a set of unique gene IDs."""
    gene_ids = set()
    try:
        with open(domtblout_path, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                fields = line.strip().split()
                if len(fields) >= 4:
                    gene_id = fields[3]  # Target name (gene ID) is the first column
                    gene_ids.add(gene_id)
    except Exception as e:
        print(f"❌ Failed to parse domtblout {domtblout_path}: {e}")
    return gene_ids

# -----------------------------
# Process each proteome
# -----------------------------
for _, row in proteome_data.iterrows():
    # Get input FASTA file path
    input_fasta_path = row.get("renamed_file", "")
    portal_name = row.get("portal", "").strip()
    
    if not input_fasta_path or not os.path.isfile(input_fasta_path):
        print(f"File {input_fasta_path} could not be found.")
        continue
    
    if not portal_name:
        print(f"No portal name for {input_fasta_path}, skipping.")
        continue
    
    # Construct corresponding domtblout file path
    domtblout_file = f"{portal_name}.domtblout"
    domtblout_path = os.path.join(hmm_results_dir, domtblout_file)
    
    if not os.path.isfile(domtblout_path):
        print(f"domtblout file {domtblout_path} could not be found.")
        continue
    
    # Parse domtblout to get unique gene IDs
    tf_gene_ids = parse_domtblout(domtblout_path)
    if not tf_gene_ids:
        print(f"No transcription factors found in {domtblout_path}.")
        continue
    
    # Read FASTA file and extract sequences for matching gene IDs
    output_fasta_path = os.path.join(output_dir, f"{portal_name}_tfs.fasta")
    sequences_written = 0
    
    try:
        with open(output_fasta_path, 'w') as out_fasta:
            for record in SeqIO.parse(input_fasta_path, "fasta"):
                # Check if the sequence ID matches any gene ID from domtblout
                if record.id in tf_gene_ids:
                    SeqIO.write(record, out_fasta, "fasta")
                    sequences_written += 1
        
        if sequences_written > 0:
            print(f"✅ Wrote {sequences_written} sequences to {output_fasta_path}")
        else:
            print(f"No matching sequences found for {portal_name}.")
            if os.path.exists(output_fasta_path):
                os.remove(output_fasta_path)  # Remove empty file
        
    except Exception as e:
        print(f"❌ Failed to process {input_fasta_path}: {e}")

print("Processing complete.")
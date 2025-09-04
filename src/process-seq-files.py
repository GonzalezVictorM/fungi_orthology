import os
import pandas as pd
import sys
import shutil
import gzip
from Bio import SeqIO

# Add project root to sys.path only here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROTEOMES_DIR, COMPRESSED_PROTEOMES_DIR, EXTRACTED_PROTEOMES_DIR, SELECTED_FILES_METADATA_PATH, RENAMED_PROTEOMES_DIR, PROTEOME_LOG_PATH, PROCESSED_PROTEOMES_PATH
from src.utils.wrangleutils import validate_directories, find_missing_files, rename_fasta_headers, extract_files

def main():
    validate_directories([PROTEOMES_DIR, COMPRESSED_PROTEOMES_DIR])
    os.makedirs(EXTRACTED_PROTEOMES_DIR, exist_ok=True)
    os.makedirs(RENAMED_PROTEOMES_DIR, exist_ok=True)
    proteome_data = pd.read_csv(SELECTED_FILES_METADATA_PATH)
    proteome_file_list = os.listdir(COMPRESSED_PROTEOMES_DIR)
    expected_files = proteome_data["compressed_file"].dropna().astype(str)
    available_files = set(proteome_file_list)
    missing_files = find_missing_files(expected_files, available_files)
    if missing_files:
        missing_str = ", ".join(missing_files)
        sys.exit(f"❌ Missing files: {missing_str}")
    else:
        print("✅ All expected files are present.")
    proteome_data["extracted_file"] = extract_files(proteome_data, COMPRESSED_PROTEOMES_DIR, EXTRACTED_PROTEOMES_DIR)
    renamed_file_column, log_data = rename_fasta_headers(proteome_data, RENAMED_PROTEOMES_DIR)
    proteome_data["renamed_file"] = renamed_file_column
    proteome_data.to_csv(PROCESSED_PROTEOMES_PATH, index=False)
    print(f"📁 Updated CSV: {PROCESSED_PROTEOMES_PATH}")
    log_df = pd.DataFrame(log_data)
    log_df.to_csv(PROTEOME_LOG_PATH, index=False)
    print(f"📝 Log saved to: {PROTEOME_LOG_PATH}")

if __name__ == "__main__":
    main()



















# -----------------------------
# Define and validate paths
# -----------------------------


# Ensure required directories exist
required_dirs = [PROTEOMES_DIR, COMPRESSED_PROTEOMES_DIR]
for d in required_dirs:
    if not os.path.isdir(d):
        sys.exit(f"❌ Directory not found: {d}")

os.makedirs(EXTRACTED_PROTEOMES_DIR, exist_ok=True)

# -----------------------------
# Load CSV and file list
# -----------------------------
proteome_data = pd.read_csv(SELECTED_FILES_METADATA_PATH)

# List all files in compressed_dir
proteome_file_list = os.listdir(COMPRESSED_PROTEOMES_DIR)

# -----------------------------
# Find missing files
# -----------------------------
expected_files = proteome_data["compressed_file"].dropna().astype(str)
available_files = set(proteome_file_list)

missing_files = [f for f in expected_files if f not in available_files]

# -----------------------------
# Report missing files
# -----------------------------
if missing_files:
    missing_str = ", ".join(missing_files)
    sys.exit(f"❌ Missing files: {missing_str}")
else:
    print("✅ All expected files are present.")

# -----------------------------
# Extract each compressed file
# -----------------------------

# New column to store extracted file paths
extracted_files_column = []

for _, row in proteome_data.iterrows():
    compressed_name = row["compressed_file"]

    # Default value in case extraction fails
    extracted_path = ""

    if pd.isna(compressed_name):
        extracted_files_column.append(extracted_path)
        continue

    compressed_path = os.path.join(COMPRESSED_PROTEOMES_DIR, compressed_name)

    # Determine output file name (remove .gz or .zip etc.)
    if compressed_name.endswith(".gz"):
        output_name = compressed_name[:-3]  # strip .gz
        output_path = os.path.join(EXTRACTED_PROTEOMES_DIR, output_name)
        try:
            with gzip.open(compressed_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            print(f"✅ Extracted {compressed_name} to {output_path}")
            extracted_path = output_path
        except Exception as e:
            print(f"❌ Failed to extract {compressed_name}: {e}")

    elif compressed_name.endswith(".zip"):
        # Handle .zip (extract all)
        try:
            shutil.unpack_archive(compressed_path, EXTRACTED_PROTEOMES_DIR)
            print(f"✅ Extracted {compressed_name} to {EXTRACTED_PROTEOMES_DIR}")
            # Just store the dir in this case
            extracted_path = EXTRACTED_PROTEOMES_DIR
        except Exception as e:
            print(f"❌ Failed to extract {compressed_name}: {e}")

    else:
        print(f"⚠️ Skipping unsupported file: {compressed_name}")

    extracted_files_column.append(extracted_path)

# -----------------------------
# Add extracted file column
# -----------------------------
proteome_data["extracted_file"] = extracted_files_column

# -----------------------------
# Output directory for renamed FASTA files
# -----------------------------
os.makedirs(RENAMED_PROTEOMES_DIR, exist_ok=True)

# Prepare columns
renamed_file_column = []
log_data = []

# -----------------------------
# Process each extracted FASTA
# -----------------------------
for _, row in proteome_data.iterrows():
    input_path = row.get("extracted_file", "")
    if not input_path or not os.path.isfile(input_path):
        renamed_file_column.append("")
        log_data.append({
            "file": os.path.basename(input_path) if input_path else "MISSING",
            "total_sequences": 0,
            "renamed_sequences": 0,
            "first_id_before": "MISSING",
            "first_id_after": "MISSING"
        })
        continue

    portal_name = row.get("portal", "").strip()
    if portal_name:
        output_file_name = f"{portal_name}.fasta"
    else:
        output_file_name = os.path.basename(input_path)

    output_path = os.path.join(RENAMED_PROTEOMES_DIR, output_file_name)
    renamed_file_column.append(output_path)

    try:
        records = list(SeqIO.parse(input_path, "fasta"))
        total_seqs = len(records)
        renamed_count = 0
        first_original_id = records[0].id if records else ""
        first_renamed_id = ""

        for i, record in enumerate(records):
            original_id = record.id  # store before any change
            if record.id.startswith("jgi|"):
                parts = record.id.split("|")
                if len(parts) >= 3:
                    new_id = f"{parts[1]}-{parts[2]}"
                    record.id = new_id
                    record.description = new_id
                    renamed_count += 1
                    if i == 0:
                        first_renamed_id = new_id
            elif i == 0:
                # If not renamed but first, keep original as renamed
                first_renamed_id = original_id

        with open(output_path, "w") as fout:
            SeqIO.write(records, fout, "fasta")

        print(f"✅ Renamed {renamed_count}/{total_seqs} headers in: {output_path}")

        log_data.append({
            "file": os.path.basename(input_path),
            "total_sequences": total_seqs,
            "renamed_sequences": renamed_count,
            "first_id_before": first_original_id,
            "first_id_after": first_renamed_id
        })

    except Exception as e:
        print(f"❌ Failed to rename headers in {input_path}: {e}")
        renamed_file_column[-1] = ""
        log_data.append({
            "file": os.path.basename(input_path),
            "total_sequences": 0,
            "renamed_sequences": 0,
            "first_id_before": "ERROR",
            "first_id_after": "ERROR"
        })

# -----------------------------
# Save updated CSV with renamed file paths
# -----------------------------
proteome_data["renamed_file"] = renamed_file_column
proteome_data.to_csv(PROCESSED_PROTEOMES_PATH, index=False)
print(f"📁 Updated CSV: {PROCESSED_PROTEOMES_PATH}")

# -----------------------------
# Save detailed log
# -----------------------------
log_df = pd.DataFrame(log_data)
log_df.to_csv(PROTEOME_LOG_PATH, index=False)
print(f"📝 Log saved to: {PROTEOME_LOG_PATH}")
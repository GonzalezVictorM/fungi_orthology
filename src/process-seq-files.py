import os
import pandas as pd
import sys

# Add project root to sys.path only here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROTEOMES_DIR, PROTEOME_FILES_METADATA_PATH, PROCESSED_PROTEOMES_PATH, RENAMED_PROTEOMES_DIR
from src.utils.wrangleutils import validate_directories, find_missing_files, rename_fasta_headers, extract_files

COMPRESSED_PROTEOMES_DIR = os.path.join(PROTEOMES_DIR, "compressed")
EXTRACTED_PROTEOMES_DIR = os.path.join(PROTEOMES_DIR, "extracted")
CLEAN_PROTEOMES_DIR = os.path.join(PROTEOMES_DIR, "clean")

PROTEOME_LOG_PATH = os.path.join(PROTEOMES_DIR, "processed_proteomes_log.csv")


def main():
    validate_directories([PROTEOMES_DIR, COMPRESSED_PROTEOMES_DIR])
    os.makedirs(EXTRACTED_PROTEOMES_DIR, exist_ok=True)
    os.makedirs(RENAMED_PROTEOMES_DIR, exist_ok=True)
    proteome_data = pd.read_csv(PROTEOME_FILES_METADATA_PATH)
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

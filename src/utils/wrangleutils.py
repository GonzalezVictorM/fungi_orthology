import os
import sys
import shutil
import gzip
import pandas as pd
from Bio import SeqIO

def validate_directories(dirs):
    """
    Ensure that all directories in the list exist.

    Args:
        dirs (list): List of directory paths to validate.

    Exits:
        If any directory does not exist, prints an error and exits the program.
    """
    for d in dirs:
        if not os.path.isdir(d):
            sys.exit(f"❌ Directory not found: {d}")


def find_missing_files(expected_files, available_files):
    """
    Find files that are expected but not available.

    Args:
        expected_files (iterable): List or Series of expected filenames.
        available_files (set): Set of filenames that are present.

    Returns:
        list: Filenames that are missing.
    """
    return [f for f in expected_files if f not in available_files]

def extract_files(proteome_data, compressed_dir, extracted_dir):
    """
    Extract compressed proteome files (.gz or .zip) to a target directory.

    Args:
        proteome_data (pd.DataFrame): DataFrame containing file metadata.
        compressed_dir (str): Directory containing compressed files.
        extracted_dir (str): Directory to extract files to.

    Returns:
        list: Paths to the extracted files (empty string if extraction failed).
    """
    extracted_files_column = []
    for _, row in proteome_data.iterrows():
        compressed_name = row["compressed_file"]
        extracted_path = ""
        if pd.isna(compressed_name):
            extracted_files_column.append(extracted_path)
            continue
        compressed_path = os.path.join(compressed_dir, compressed_name)
        if compressed_name.endswith(".gz"):
            output_name = compressed_name[:-3]
            output_path = os.path.join(extracted_dir, output_name)
            try:
                with gzip.open(compressed_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                print(f"✅ Extracted {compressed_name} to {output_path}")
                extracted_path = output_path
            except Exception as e:
                print(f"❌ Failed to extract {compressed_name}: {e}")
        elif compressed_name.endswith(".zip"):
            try:
                shutil.unpack_archive(compressed_path, extracted_dir)
                print(f"✅ Extracted {compressed_name} to {extracted_dir}")
                extracted_path = extracted_dir
            except Exception as e:
                print(f"❌ Failed to extract {compressed_name}: {e}")
        else:
            print(f"⚠️ Skipping unsupported file: {compressed_name}")
        extracted_files_column.append(extracted_path)
    return extracted_files_column

def rename_fasta_headers(proteome_data, renamed_dir):
    """
    Rename FASTA sequence headers for extracted proteome files and log the changes.

    Args:
        proteome_data (pd.DataFrame): DataFrame containing file metadata and extracted file paths.
        renamed_dir (str): Directory to save renamed FASTA files.

    Returns:
        tuple:
            list: Paths to renamed FASTA files (empty string if renaming failed).
            list: Log data for each file (dicts with file info and renaming summary).
    """
    renamed_file_column = []
    log_data = []
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
        output_file_name = f"{portal_name}.fasta" if portal_name else os.path.basename(input_path)
        output_path = os.path.join(renamed_dir, output_file_name)
        renamed_file_column.append(output_path)
        try:
            records = list(SeqIO.parse(input_path, "fasta"))
            total_seqs = len(records)
            renamed_count = 0
            first_original_id = records[0].id if records else ""
            first_renamed_id = ""
            for i, record in enumerate(records):
                original_id = record.id
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
    return renamed_file_column, log_data

def build_phylogeny_data(df):
    """
    Extracts phylogenetic information from the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing organism metadata.

    Returns:
        pd.DataFrame: DataFrame with unique combinations of organism and ncbi taxonomy columns.
    """
    cols = ["organism"] + ["new_proteome"] + [col for col in df.columns if col.startswith("ncbi")]
    return df.loc[:, cols].drop_duplicates()

def split_phylogeny_data(phylogeny_data, missing_organisms):
    """
    Splits the phylogeny DataFrame into missing, complete, and incomplete subsets.

    Args:
        phylogeny_data (pd.DataFrame): DataFrame with phylogenetic and organism information.
        missing_organisms (iterable): Organisms with missing data.

    Returns:
        tuple:
            pd.DataFrame: Data for missing organisms.
            pd.DataFrame: Data for organisms with complete ncbi_taxon_id.
            pd.DataFrame: Data for organisms not in missing or complete (incomplete).
    """
    missing = phylogeny_data[phylogeny_data["organism"].isin(missing_organisms)]
    complete = phylogeny_data[
        phylogeny_data["ncbi_taxon_id"].notna() &
        (phylogeny_data["ncbi_taxon_id"].astype(str).str.strip() != "") &
        (phylogeny_data["ncbi_taxon_id"].astype(str).str.strip().str.len() >= 2)
        ].drop_duplicates()
    incomplete = phylogeny_data[
        ~phylogeny_data["organism"].isin(list(missing_organisms) + list(complete["organism"]))
    ].drop_duplicates()
    return missing, complete, incomplete

def find_duplicates(phylogeny_data_complete):
    """
    Identifies organisms with duplicate entries in the complete phylogeny data.

    Args:
        phylogeny_data_complete (pd.DataFrame): DataFrame with complete phylogeny information.

    Returns:
        tuple:
            pd.DataFrame: Rows for organisms with duplicate entries.
            pd.DataFrame: Rows for organisms with a single entry.
    """
    counts = phylogeny_data_complete.groupby("organism").size().reset_index(name="count")
    double_organisms = counts[counts["count"] > 1]["organism"]
    double_phylogeny = phylogeny_data_complete[phylogeny_data_complete["organism"].isin(double_organisms)]
    single_phylogeny = phylogeny_data_complete[~phylogeny_data_complete["organism"].isin(double_organisms)]
    return double_phylogeny, single_phylogeny

def check_organism_counts(single_phylogeny, double_phylogeny, missing, incomplete, all_organisms):
    all_organisms_series = pd.concat([
        single_phylogeny["organism"],
        double_phylogeny["organism"],
        missing["organism"],
        incomplete["organism"]
    ])
    all_count = len(pd.unique(all_organisms_series))
    assert all_count == len(all_organisms), "Organism count mismatch!"


def find_new_proteomes(
    df: pd.DataFrame,
    portals_table_path: str
) -> pd.DataFrame:
    """
    Annotate new proteomes in the current DataFrame compared to a previous version.

    Args:
        df (pd.DataFrame): The new MycoCosm DataFrame.
        portals_table_path (str): Path to the previous portals table CSV.

    Returns:
        pd.DataFrame: The input DataFrame with a new 'new_proteome' boolean column.
    """
    import warnings

    if not os.path.exists(portals_table_path):
        df['new_proteome'] = True
        return df

    old_df = pd.read_csv(portals_table_path, encoding='utf-8')

    # Ensure 'portal' and 'reference' columns exist in both
    required_cols = {'portal', 'reference'}
    if required_cols.issubset(old_df.columns) and required_cols.issubset(df.columns):
        old_portals = set(old_df['portal'])
        old_portals_with_ref = set(
            old_df[old_df['reference'].notna() & (old_df['reference'].astype(str).str.strip() != "")]['portal']
        )
        def is_new(row):
            portal = row['portal']
            has_ref = pd.notna(row['reference']) and str(row['reference']).strip() != ""
            if portal not in old_portals:
                return True
            if has_ref and portal not in old_portals_with_ref:
                return True
            return False
        df['new_proteome'] = df.apply(is_new, axis=1)
    else:
        warnings.warn("Missing 'portal' or 'reference' columns in one of the DataFrames. Marking all as new.")
        df['new_proteome'] = True
    return df

def case_get(d, *keys, default=None):
    """
    Case-insensitive dictionary get with fallbacks.

    Args:
        d (dict): Dictionary to search.
        *keys: Keys to try (in order).
        default: Value to return if none of the keys are found.

    Returns:
        Value from the dictionary if found (case-insensitive), else default.
    """
    for k in keys:
        if k in d:
            return d[k]
        k_low = str(k).lower()
        for dk in d:
            if str(dk).lower() == k_low:
                return d[dk]
    return default
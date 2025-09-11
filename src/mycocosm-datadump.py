import os
import sys
import logging

# Add project root to sys.path only here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MYCOCOSM_FUNGI_URL, DATA_DIR
from src.credentials import JGI_API_TOKEN
from src.utils.webutils import download_mycocosm_fungi_table, batch_fetch_json, parse_portal_jsons
from src.utils.wrangleutils import find_new_proteomes,build_phylogeny_data, split_phylogeny_data, find_duplicates, check_organism_counts

# === Logging setup ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# === Global variables ===
MYCOCOSM_DATA_DIR = os.path.join(DATA_DIR, 'mycocosm_data')
JSON_DIR = os.path.join(MYCOCOSM_DATA_DIR, 'json_files')
PORTALS_DIR = os.path.join(MYCOCOSM_DATA_DIR, "portal_phylogeny")
SELECTED_DIR = os.path.join(MYCOCOSM_DATA_DIR, "file_selection")

NEW_PORTALS_TABLE_PATH = os.path.join(MYCOCOSM_DATA_DIR, 'mycocosm_fungi_data_new.xlsx')
PORTALS_TABLE_PATH = os.path.join(MYCOCOSM_DATA_DIR, 'mycocosm_fungi_data.csv')
MYCOCOSM_FILES_METADATA_PATH = os.path.join(MYCOCOSM_DATA_DIR, 'mycocosm_files_metadata.csv')


# Authentication headers
headers = {
    "accept": "application/json",
    "Authorization": JGI_API_TOKEN
} 

if __name__ == "__main__":
    # Fetch the table from the website wrangle it for our use
    os.makedirs(MYCOCOSM_DATA_DIR, exist_ok=True)
    df = download_mycocosm_fungi_table(MYCOCOSM_FUNGI_URL, NEW_PORTALS_TABLE_PATH)
    os.makedirs(JSON_DIR, exist_ok=True)

    if df is not None:
        # Check for previous version before saving new CSV
        if os.path.exists(PORTALS_TABLE_PATH):
            df = find_new_proteomes(df, PORTALS_TABLE_PATH)
        else:
            df['new_proteome'] = True  # All are new if no previous file    
        df.to_csv(PORTALS_TABLE_PATH, index=False, encoding='utf-8')
        if "Published" not in df.columns or "portal" not in df.columns:
            logging.error("Required columns missing in DataFrame.")
            sys.exit(1)
        #  Select only published IDs
        published_rows = df[df["Published"].notna() & (df["Published"].str.strip() != "")]
        organism_ids = published_rows['portal'].tolist()
        new_organism_ids = published_rows[published_rows['new_proteome'] == True]['portal'].tolist()
        logging.info(f"Number of published rows: {len(organism_ids)}")
        logging.info(f"Number of new published rows: {len(new_organism_ids)}")
    else:
        logging.error("Failed to download MycoCosm fungi table.")
        sys.exit(1)

    # Fetch and parse JSON files for all published organism IDs
    batch_fetch_json(new_organism_ids, headers, JSON_DIR)

    metadata_df = parse_portal_jsons(organism_ids, JSON_DIR)
    # Map new_proteome from df to metadata_df using the correct column
    if 'organism' in metadata_df.columns and 'portal' in df.columns and 'new_proteome' in df.columns:
        portal_to_new = dict(zip(df['portal'], df['new_proteome']))
        metadata_df['new_proteome'] = metadata_df['organism'].map(portal_to_new).fillna(False)
    else:
        metadata_df['new_proteome'] = False
    metadata_df.to_csv(MYCOCOSM_FILES_METADATA_PATH, index=False)

    # Build phylogeny data and split into categories to make manual curation easier
    all_organisms = metadata_df["organism"].unique()
    retrieved_organisms = metadata_df[metadata_df["file_name"] != "NO FILES FOUND"]["organism"].unique()
    missing_organisms = metadata_df[metadata_df["file_name"] == "NO FILES FOUND"]["organism"].unique()
    
    phylogeny_data = build_phylogeny_data(metadata_df)
    phylogeny_data_missing, phylogeny_data_complete, phylogeny_data_incomplete = split_phylogeny_data(
        phylogeny_data, missing_organisms
    )
    double_phylogeny, single_phylogeny = find_duplicates(phylogeny_data_complete)

    check_organism_counts(single_phylogeny, double_phylogeny, phylogeny_data_missing, phylogeny_data_incomplete, all_organisms)
    
    os.makedirs(PORTALS_DIR, exist_ok=True)

    phylogeny_data_missing.to_csv(os.path.join(PORTALS_DIR, "missing_portals_phylopgeny.csv"), index=False)
    phylogeny_data_incomplete.to_csv(os.path.join(PORTALS_DIR, "portals_incomplete_phylogeny.csv"), index=False)
    single_phylogeny.to_csv(os.path.join(PORTALS_DIR, "portals_single_phylogeny.csv"), index=False)
    double_phylogeny.to_csv(os.path.join(PORTALS_DIR, "portals_double_phylogeny.csv"), index=False)
    
    logging.info(f"Phylogeny data saved in {PORTALS_DIR}")

    # Filter out the files we mostly care about: proteomes and CDS
    proteome_files = metadata_df[
        metadata_df['file_name'].str.contains('GeneCatalog', na=False) &
        metadata_df['file_name'].str.contains('aa.fasta', na=False) &
        metadata_df['file_type'].str.contains('protein', na=False, regex=False) &
        metadata_df['portal_display_location'].str.contains('Filtered Models ("best")', na=False, regex=False)
    ]
    double_proteomes, single_proteomes = find_duplicates(proteome_files)
    unusual_proteomes = metadata_df[
        ~metadata_df['organism'].isin(proteome_files['organism']) &
        metadata_df['file_type'].str.contains('protein', na=False, regex=False) &
        metadata_df['portal_display_location'].str.contains('Filtered Models ("best")', na=False, regex=False)
    ]
    missing_proteomes = metadata_df[
        ~metadata_df['organism'].isin(proteome_files['organism']) &
        ~metadata_df['organism'].isin(unusual_proteomes['organism'])
    ]

    cds_files = metadata_df[
        metadata_df['jat_label'].str.contains('cds_filtered', na=False) &
        ~metadata_df['file_name'].str.contains('alleles', na=False) &
        metadata_df['file_type'].str.contains('cds', na=False, regex=False) &
        metadata_df['portal_display_location'].str.contains('Filtered Models ("best")', na=False, regex=False)
    ]
    double_cds, single_cds = find_duplicates(cds_files)
    missing_cds = metadata_df[~metadata_df['organism'].isin(cds_files['organism'])]

    os.makedirs(SELECTED_DIR, exist_ok=True)
    proteome_files.to_csv(os.path.join(SELECTED_DIR, "proteome_files_all.csv"), index=False)
    double_proteomes.to_csv(os.path.join(SELECTED_DIR, "proteomes_files_double.csv"), index=False)
    single_proteomes.to_csv(os.path.join(SELECTED_DIR, "proteomes_files_single.csv"), index=False)
    unusual_proteomes.to_csv(os.path.join(SELECTED_DIR, "proteomes_files_unusual.csv"), index=False)
    missing_proteomes.to_csv(os.path.join(SELECTED_DIR, "proteomes_files_missing.csv"), index=False)
    cds_files.to_csv(os.path.join(SELECTED_DIR, "cds_files_all.csv"), index=False)
    double_cds.to_csv(os.path.join(SELECTED_DIR, "cds_files_double.csv"), index=False)
    single_cds.to_csv(os.path.join(SELECTED_DIR, "cds_files_single.csv"), index=False)
    missing_cds.to_csv(os.path.join(SELECTED_DIR, "cds_files_missing.csv"), index=False) 
    logging.info(f"Selected files data saved in {SELECTED_DIR}")

    logging.info("Data processing complete.")
    logging.info(f"Time to manually curate phylogeny data in {PORTALS_DIR} and select files in {SELECTED_DIR}.")  
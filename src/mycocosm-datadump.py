import os
import sys
import logging

# Add project root to sys.path only here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MYCOCOSM_FUNGI_URL, DATA_DIR
from credentials import JGI_API_TOKEN
from src.utils.webutils import download_mycocosm_fungi_table, batch_fetch_json, parse_portal_jsons

# === Logging setup ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# === Global variables ===
MYCOCOSM_DATA_DIR = os.path.join(DATA_DIR, 'mycocosm_data')
JSON_DIR = os.path.join(MYCOCOSM_DATA_DIR, 'json_files')
PORTALS_TABLE_PATH = os.path.join(MYCOCOSM_DATA_DIR, 'mycocosm_fungi_data.csv')
MYCOCOSM_FILES_METADATA_PATH = os.path.join(MYCOCOSM_DATA_DIR, 'mycocosm_fungi_files_metadata.csv')

# Authentication headers
headers = {
    "accept": "application/json",
    "Authorization": JGI_API_TOKEN
} 

if __name__ == "__main__":
    df = download_mycocosm_fungi_table(MYCOCOSM_FUNGI_URL)
    os.makedirs(JSON_DIR, exist_ok=True)

    if df is not None:
        df.to_csv(PORTALS_TABLE_PATH, index=False, encoding='utf-8')
        if "Published" not in df.columns or "portal" not in df.columns:
            logging.error("Required columns missing in DataFrame.")
            sys.exit(1)
        #  Select only published IDs
        published_rows = df[df["Published"].notna() & (df["Published"].str.strip() != "")]
        organism_ids = published_rows['portal'].tolist()
        logging.info(f"Number of published rows: {len(organism_ids)}")
    else:
        logging.error("Failed to download MycoCosm fungi table.")
        sys.exit(1)

    batch_fetch_json(organism_ids, headers, JSON_DIR)

    metadata_df = parse_portal_jsons(organism_ids, JSON_DIR)
    metadata_df.to_csv(MYCOCOSM_FILES_METADATA_PATH, index=False)
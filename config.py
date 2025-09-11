import os

# ---- Mycocosm configuration ----
## Genome table
MYCOCOSM_FUNGI_URL = "https://mycocosm.jgi.doe.gov/fungi/fungi.info.html"


## API configuration
JGI_API_BASE_URL = "https://files.jgi.doe.gov/mycocosm_file_list/"
FILES_PER_PAGE = 50  # Set to 50 files per page
REQUEST_DELAY = 1  # Delay in seconds between requests

# ---- Paths ----
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'local_data')
# JSON_DIR = os.path.join(DATA_DIR, 'json_files')
# PORTALS_DIR = os.path.join(DATA_DIR, "portal_phylogeny")
PROTEOMES_DIR = os.path.join(DATA_DIR, "proteomes")
RENAMED_PROTEOMES_DIR = os.path.join(PROTEOMES_DIR, "renamed")
FINAL_PROTEOMES_DIR = os.path.join(PROTEOMES_DIR, "final")
CLEAN_PROTEOMES_DIR = os.path.join(PROTEOMES_DIR, "clean")


# PORTALS_TABLE_PATH = os.path.join(DATA_DIR, 'mycocosm_fungi_data.csv')

# ORGANISM_IDS_PATH = os.path.join(DATA_DIR, 'selected_organism_ids.csv')
# MYCOCOSM_FILELIST_PATH = os.path.join(DATA_DIR, 'mycocosm_data.csv')
# ALL_FILES_METADATA_PATH = os.path.join(DATA_DIR, 'all_files_metadata.csv')
PROTEOME_FILES_METADATA_PATH = os.path.join(DATA_DIR, 'proteomes_all_list.csv')
PROCESSED_PROTEOMES_PATH = os.path.join(PROTEOMES_DIR, 'processed_proteomes_list.csv')
PROTEOME_FINAL_METADATA_PATH = os.path.join(DATA_DIR, 'proteomes_final_list.csv')
# PROTEOME_LOG_PATH = os.path.join(PROTEOMES_DIR, "renaming_summary_log.csv")
# PROTEOME_CUSTOMLOG_PATH = os.path.join(PROTEOMES_DIR, "renaming_custom_summary_log.csv")
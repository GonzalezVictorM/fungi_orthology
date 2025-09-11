import os
import sys
import re
import json
import glob
import pandas as pd

# Add project root to sys.path only here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATA_DIR, PROTEOME_FILES_METADATA_PATH
from src.utils.wrangleutils import validate_directories, find_missing_files, case_get

BUSCO_DIR = os.path.join(DATA_DIR, "BUSCO_results")
BUSCO_RES_DIR = os.path.join(BUSCO_DIR, "busco_renamed")
OUT_CSV = os.path.join(BUSCO_DIR, "busco_summary.csv")

def find_summary_json(folder: str) -> str | None:
    """
    Find the most recently modified BUSCO summary JSON file in a folder.

    Args:
        folder (str): Path to the BUSCO result folder.

    Returns:
        str | None: Path to the freshest short_summary*.json file, or None if not found.
    """
    candidates = glob.glob(os.path.join(folder, "short_summary*.json"))
    if not candidates:
        return None
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]

def parse_busco_json(json_path: str) -> dict:
    """
    Parse a BUSCO summary JSON file and extract relevant metrics.

    Args:
        json_path (str): Path to the BUSCO summary JSON file.

    Returns:
        dict: Dictionary of parsed BUSCO metrics and metadata.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    results  = data.get("results", {})
    lineage  = data.get("lineage_dataset", {})
    params   = data.get("parameters", {})
    versions = data.get("versions", {})

    # portal name from file like: short_summary.<stuff>.<portal>.fasta.json
    base = os.path.basename(json_path)
    m = re.search(r"short_summary\..*?\.\..*?\.(?P<portal>.+?)\.fasta\.json$", base)
    portal = m.group("portal") if m else None
    if not portal:
        # fallback: derive from parent folder name ending with ".fasta"
        parent = os.path.basename(os.path.dirname(json_path))
        portal = parent[:-6] if parent.endswith(".fasta") else parent

    rec = {
        "portal": portal,
        "portal_fasta": f"{portal}.fasta" if portal else None,
        "one_line_summary": case_get(results, "one_line_summary"),

        # Percentages
        "complete_pct":     case_get(results, "Complete percentage", "C"),
        "single_copy_pct":  case_get(results, "Single copy percentage", "S"),
        "duplicated_pct":   case_get(results, "Multi copy percentage", "D", "Duplicated percentage"),
        "fragmented_pct":   case_get(results, "Fragmented percentage", "F"),
        "missing_pct":      case_get(results, "Missing percentage", "M"),

        # Counts
        "complete_n":       case_get(results, "Complete BUSCOs"),
        "single_copy_n":    case_get(results, "Single copy BUSCOs"),
        "duplicated_n":     case_get(results, "Multi copy BUSCOs", "Duplicated BUSCOs"),
        "fragmented_n":     case_get(results, "Fragmented BUSCOs"),
        "missing_n":        case_get(results, "Missing BUSCOs"),
        "n_markers":        case_get(results, "n_markers", "n"),
        "domain":           case_get(results, "domain"),

        # Useful metadata (optional but nice to have)
        "lineage":               case_get(lineage, "name"),
        "lineage_n_markers":     case_get(lineage, "number_of_buscos"),
        "lineage_species":       case_get(lineage, "number_of_species"),
        "lineage_creation_date": case_get(lineage, "creation_date"),
        "busco_version":         case_get(versions, "busco"),
        "python_version":        ".".join(map(str, case_get(versions, "python", default=[]))) if case_get(versions, "python", default=[]) else None,
        "input_path":            case_get(params, "in"),
        "main_out":              case_get(params, "main_out"),
        "summary_path":          str(json_path),
        "_source":               "json",
    }
    return rec

def main():
    validate_directories([BUSCO_DIR, BUSCO_RES_DIR])

    proteome_data = pd.read_csv(PROTEOME_FILES_METADATA_PATH)
    portal_ids = proteome_data["portal"].dropna().astype(str).tolist()

    expected_folders = [pid + ".fasta" for pid in portal_ids]
    busco_folder_list = [
        f for f in os.listdir(BUSCO_RES_DIR)
        if f.endswith(".fasta") and os.path.isdir(os.path.join(BUSCO_RES_DIR, f))
    ]

    missing_folders = find_missing_files(expected_folders, busco_folder_list)
    if missing_folders:
        missing_str = ", ".join(missing_folders)
        sys.exit(f"❌ Missing folders: {missing_str}")
    else:
        print("✅ All expected folders are present.")

    records, missing_json = [], []

    for portal in portal_ids:
        results_path = os.path.join(BUSCO_RES_DIR, portal + ".fasta")
        json_path = find_summary_json(results_path)

        if not json_path or not os.path.exists(json_path):
            missing_json.append(portal)
            continue

        try:
            records.append(parse_busco_json(json_path))
        except Exception as e:
            records.append({
                "portal": portal,
                "portal_fasta": f"{portal}.fasta",
                "error": f"Failed to parse JSON: {e}",
                "_source": "json",
                "summary_path": str(json_path),
            })

    df = pd.DataFrame.from_records(records)
    if not df.empty:
        df.sort_values(by=["portal"], inplace=True, kind="stable")
        os.makedirs(BUSCO_DIR, exist_ok=True)
        df.to_csv(OUT_CSV, index=False)
        print(f"✅ Parsed {len(df)} BUSCO summaries -> {OUT_CSV}")
    else:
        print("⚠️ No BUSCO summaries parsed.")

    if missing_json:
        print(f"⚠️ No summary JSON found for {len(missing_json)} portals:")
        print(", ".join(missing_json))

if __name__ == "__main__":
    main()

# This code is to be added to the mycocosm-datadump as it does not require human interaction before receiving the datadump.
import os
import pandas as pd
from config import PORTALS_DIR, ALL_FILES_METADATA_PATH

def get_missing_and_retrieved_organisms(df):
    retrieved = df[df["file_name"] != "NO FILES FOUND"]["organism"].unique()
    missing = df[df["file_name"] == "NO FILES FOUND"]["organism"].unique()
    return retrieved, missing

def build_phylogeny_data(df):
    cols = ["organism"] + [col for col in df.columns if col.startswith("ncbi")]
    return df.loc[:, cols].drop_duplicates()

def split_phylogeny_data(phylogeny_data, missing_organisms):
    missing = phylogeny_data[phylogeny_data["organism"].isin(missing_organisms)]
    complete = phylogeny_data[phylogeny_data["ncbi_taxon_id"].notna()].drop_duplicates()
    incomplete = phylogeny_data[
        ~phylogeny_data["organism"].isin(list(missing_organisms) + list(complete["organism"]))
    ].drop_duplicates()
    return missing, complete, incomplete

def find_duplicates(phylogeny_data_complete):
    counts = phylogeny_data_complete.groupby("organism").size().reset_index(name="count")
    double_organisms = counts[counts["count"] > 1]["organism"]
    double_phylogeny = phylogeny_data_complete[phylogeny_data_complete["organism"].isin(double_organisms)]
    single_phylogeny = phylogeny_data_complete[~phylogeny_data_complete["organism"].isin(double_organisms)]
    return double_phylogeny, single_phylogeny

def check_organism_counts(single_phylogeny, double_phylogeny, missing, incomplete, all_organisms):
    all_count = len(
        pd.unique(
            list(single_phylogeny["organism"])
            + list(double_phylogeny["organism"])
            + list(missing["organism"])
            + list(incomplete["organism"])
        )
    )
    assert all_count == len(all_organisms), "Organism count mismatch!"

def write_outputs(out_dir, missing, incomplete, single_phylogeny, double_phylogeny):
    missing.to_csv(os.path.join(out_dir, "missing_portals_phylopgeny.csv"), index=False)
    incomplete.to_csv(os.path.join(out_dir, "portals_incomplete_phylogeny.csv"), index=False)
    single_phylogeny.to_csv(os.path.join(out_dir, "portals_single_phylogeny.csv"), index=False)
    double_phylogeny.to_csv(os.path.join(out_dir, "portals_double_phylogeny.csv"), index=False)

def main():
    os.makedirs(PORTALS_DIR, exist_ok=True)
    
    # Load all MycoCosm files metadata
    all_mycocosm_files = pd.read_csv(ALL_FILES_METADATA_PATH)

    all_organisms = all_mycocosm_files["organism"].unique()
    retrieved_organisms, missing_organisms = get_missing_and_retrieved_organisms(all_mycocosm_files)
    
    phylogeny_data = build_phylogeny_data(all_mycocosm_files)
    phylogeny_data_missing, phylogeny_data_complete, phylogeny_data_incomplete = split_phylogeny_data(
        phylogeny_data, missing_organisms
    )
    double_phylogeny, single_phylogeny = find_duplicates(phylogeny_data_complete)

    check_organism_counts(single_phylogeny, double_phylogeny, phylogeny_data_missing, phylogeny_data_incomplete, all_organisms)
    write_outputs(PORTALS_DIR, phylogeny_data_missing, phylogeny_data_incomplete, single_phylogeny, double_phylogeny)

if __name__ == "__main__":
    main()
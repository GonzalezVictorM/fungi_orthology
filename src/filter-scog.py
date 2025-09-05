import os
import shutil
import pandas as pd
import argparse
from config import ORTHOFINDER_TBLS_DIR, ORTHOFINDER_SEQS_DIR, ORTHOGROUPS_GENECOUNT_PATH, SPECIESTREE_SEQS_DIR
from utils.wrangle_utils import find_single_copy_orthogroups, copy_orthogroup_fastas

def main():
    """
    Parses command-line arguments, finds single-copy orthogroups,
    and copies their FASTA files to the target directory.
    """
    parser = argparse.ArgumentParser(description="Find single-copy orthogroups and copy their FASTA files.")
    parser.add_argument('--threshold', type=float, default=0.75, help='Fraction of genomes required to have a single gene (default: 0.75)')
    args = parser.parse_args()

    output_path = os.path.join(ORTHOFINDER_TBLS_DIR, 'single_copy_orthogroups.tsv')
    orthogroup_names = find_single_copy_orthogroups(ORTHOGROUPS_GENECOUNT_PATH, output_path, args.threshold)
    copy_orthogroup_fastas(orthogroup_names, ORTHOFINDER_SEQS_DIR, SPECIESTREE_SEQS_DIR)

if __name__ == "__main__":
    main()
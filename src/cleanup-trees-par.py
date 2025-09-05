#!/usr/bin/env python3
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from Bio import Phylo

BASE   = Path.cwd()
IN_DIR = BASE / "local_data/speciestree/gene_trees"
OUT_DIR= BASE / "local_data/speciestree/astral_clean_trees"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def process_one(path: Path) -> str:
    try:
        t = Phylo.read(str(path), "newick")        # one tree per file (IQ-TREE default)
        for clade in t.get_terminals():
            if clade.name:
                clade.name = clade.name.split("-", 1)[0]  # keep species only
        out_path = OUT_DIR / path.name
        Phylo.write(t, str(out_path), "newick")
        return f"OK  {path.name}"
    except Exception as e:
        return f"ERR {path.name}: {e}"

def main():
    files = sorted(IN_DIR.glob("*.treefile"))
    if not files:
        print(f"No .treefile files found in {IN_DIR}")
        return

    # Use SLURM_CPUS_PER_TASK if set, otherwise all local cores
    n_workers = int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1))
    print(f"Processing {len(files)} trees with {n_workers} workers")
    ok = err = 0

    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futs = {ex.submit(process_one, f): f for f in files}
        for i, fut in enumerate(as_completed(futs), 1):
            msg = fut.result()
            if msg.startswith("OK"):
                ok += 1
            else:
                err += 1
            # lightweight progress ping every 100 files
            if i % 100 == 0 or i == len(files):
                print(f"[{i}/{len(files)}] {ok} ok, {err} err")

    print(f"Done. {ok} succeeded, {err} failed. Output → {OUT_DIR}")

if __name__ == "__main__":
    main()


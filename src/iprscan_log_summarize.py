#!/usr/bin/env python3
"""
Summarize InterProScan cluster submit logs.

For each file matching: iprscan_*.submit.log
the script extracts:
- portal (from filename)
- total_subjobs (from "The job is split into N pieces")
- ok_subjobs (# of "subjob X OK")
- failed_subjobs (# of "subjob X FAILED")
- missing_subjobs (if total is known: total - ok - failed; else empty)

Usage:
  python iprscan_summarize.py /path/to/folder [-o output.csv]

Notes:
- If total_subjobs isn't present in a file, it's left blank in the CSV.
- Script is robust to extra whitespace and repeated lines.
"""

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

TOTAL_RE = re.compile(r"The job is split into\s+(\d+)\s+pieces", re.IGNORECASE)
SUBJOB_RE = re.compile(r"subjob\s+(\d+)\s+(OK|FAILED)", re.IGNORECASE)

def parse_log_file(p: Path) -> Dict[str, Optional[int]]:
    portal = p.name
    # Derive portal from filename patterns like: iprscan_<portal>.submit.log
    # We'll remove a leading "iprscan_" and trailing ".submit.log" if present.
    if portal.startswith("iprscan_"):
        portal = portal[len("iprscan_"):]
    if portal.endswith(".submit.log"):
        portal = portal[:-len(".submit.log")]

    try:
        text = p.read_text(errors="ignore")
    except Exception as e:
        return {
            "portal": portal,
            "total_subjobs": None,
            "ok_subjobs": None,
            "failed_subjobs": None,
            "missing_subjobs": None,
            "error": f"Could not read file: {e}",
            "path": str(p),
        }

    total_match = TOTAL_RE.search(text)
    total = int(total_match.group(1)) if total_match else None

    ok = 0
    failed = 0

    # Count OK / FAILED lines
    for m in SUBJOB_RE.finditer(text):
        status = m.group(2).upper()
        if status == "OK":
            ok += 1
        elif status == "FAILED":
            failed += 1

    missing = None
    if total is not None:
        missing = max(total - ok - failed, 0)

    return {
        "portal": portal,
        "total_subjobs": total,
        "ok_subjobs": ok,
        "failed_subjobs": failed,
        "missing_subjobs": missing,
        "error": "",
        "path": str(p),
    }

def find_logs(folder: Path) -> List[Path]:
    return sorted(folder.glob("iprscan_*.submit.log"))

def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize InterProScan submit logs")
    ap.add_argument("folder", type=Path, default=Path("local_data/logs/iprscan_logs"),
                    help="Folder containing iprscan_*.submit.log files (default: local_data/logs/iprscan_logs)")
    ap.add_argument("-o", "--output", type=Path, default=Path("local_data/logs/iprscan_summary.csv"),
                    help="Output CSV path (default: local_data/logs/iprscan_summary.csv)")
    ap.add_argument("--print", dest="do_print", action="store_true",
                    help="Print a pretty table to stdout")
    args = ap.parse_args()

    logs = find_logs(args.folder)
    if not logs:
        print(f"No files found in {args.folder} matching iprscan_*.submit.log")
        return

    rows: List[Dict[str, Optional[int]]] = [parse_log_file(p) for p in logs]

    # Write CSV
    fieldnames = ["portal", "total_subjobs", "ok_subjobs", "failed_subjobs", "missing_subjobs", "path", "error"]
    with args.output.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {args.output} with {len(rows)} rows.")

    if args.do_print:
        # Minimal dependency pretty table
        widths = {k: len(k) for k in fieldnames}
        for r in rows:
            for k in fieldnames:
                widths[k] = max(widths[k], len("" if r.get(k) is None else str(r.get(k))))

        def line(char="-"):
            print("+" + "+".join(char * (widths[k] + 2) for k in fieldnames) + "+")

        def cell_row(values: List[str]):
            print("| " + " | ".join(v.ljust(widths[fieldnames[i]]) for i, v in enumerate(values)) + " |")

        line("=")
        cell_row(fieldnames)
        line("=")
        for r in rows:
            values = [str(r.get(k, "")) if r.get(k) is not None else "" for k in fieldnames]
            cell_row(values)
            line("-")

if __name__ == "__main__":
    main()

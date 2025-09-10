#!/bin/bash

set -euo pipefail

input_file="local_data/proteomes_final_list.csv"
src_dir="local_data/proteomes/clean"
dst_dir="local_data/proteomes/final"
mkdir -p "$dst_dir"

portals=()

# Read the header to find the column index for 'portal' (1-based)
header=$(head -n 1 "$input_file")
IFS=',' read -ra columns <<< "$header"
for i in "${!columns[@]}"; do
    col="${columns[$i]%$'\r'}"   # strip possible CR
    if [[ "$col" == "portal" ]]; then
        portal_idx=$((i+1))
        break
    fi
done
if [[ -z "${portal_idx:-}" ]]; then
    echo "Error: 'portal' column not found in $input_file" >&2
    exit 1
fi

# Read the 'portal' column into the portals array
mapfile -t portals < <(tail -n +2 "$input_file" | awk -F',' -v idx="$portal_idx" '{print $idx}')

# Copy each portal.fasta file, stripping '*' from sequence lines
for portal in "${portals[@]}"; do
    portal="${portal%$'\r'}"  # strip possible CRs
    [[ -z "$portal" ]] && continue

    src_file="$src_dir/${portal}.fasta"
    out_file="$dst_dir/${portal}.fasta"

    if [[ -f "$src_file" ]]; then
        # Remove all '*' characters from NON-header lines (those not starting with '>')
        sed -e '/^>/! s/\*$//' "$src_file" > "$out_file"
    else
        echo "Warning: missing $src_file" >&2
    fi
done

echo "Done. Cleaned FASTA written to $dst_dir"
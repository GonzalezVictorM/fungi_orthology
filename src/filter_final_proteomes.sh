#!/bin/bash

input_file="local_data/proteomes_final_list.csv"
portals=()

# Read the header to find the column index for 'portal'
header=$(head -1 "$input_file")
IFS=',' read -ra columns <<< "$header"
for i in "${!columns[@]}"; do
    if [[ "${columns[$i]}" == "portal" ]]; then
        portal_idx=$i
        break
    fi
done

# Read the 'portal' column into the portals array
mapfile -t portals < <(tail -n +2 "$input_file" | awk -F',' -v idx=$((portal_idx+1)) '{print $idx}')

# Copy each portal.fasta file
src_dir="local_data/proteomes/renamed"
dst_dir="local_data/proteomes/final"
mkdir -p "$dst_dir"

for portal in "${portals[@]}"; do
    src_file="$src_dir/${portal}.fasta"
    if [[ -f "$src_file" ]]; then
        cp "$src_file" "$dst_dir/"
    fi
done
import os
import pandas as pd
from Bio import SeqIO
import re
import sys

# Add project root to sys.path only here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROTEOMES_DIR, PROCESSED_PROTEOMES_PATH, RENAMED_PROTEOMES_DIR

# -----------------------------
# Configuration
# -----------------------------
PROTEOME_CUSTOMLOG_PATH = os.path.join(PROTEOMES_DIR, "processed_proteomes_log_custom.csv")
os.makedirs(RENAMED_PROTEOMES_DIR, exist_ok=True)

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv(PROCESSED_PROTEOMES_PATH)
target_portals = {"Altbr1", "Pyrtr1"}
df = df[df["portal"].isin(target_portals)]

log_data = []

# -----------------------------
# Custom renaming logic
# -----------------------------
for _, row in df.iterrows():
    portal = row["portal"]
    input_path = row["renamed_file"]

    if not os.path.isfile(input_path):
        print(f"❌ File not found: {input_path}")
        continue

    output_path = os.path.join(RENAMED_PROTEOMES_DIR, f"{portal}.fasta")
    renamed_count = 0
    total = 0
    first_before = ""
    first_after = ""

    try:
        records = list(SeqIO.parse(input_path, "fasta"))
        total = len(records)

        for i, record in enumerate(records):
            original_id = record.id

            if i == 0:
                first_before = original_id

            if portal == "Altbr1":
                match = re.match(r"AB0*(\d+)\.\d+", original_id)
                if match:
                    new_id = f"Altbr1-{match.group(1)}"
                    record.id = new_id
                    record.description = new_id
                    renamed_count += 1
            elif portal == "Pyrtr1":
                match = re.match(r"PTRG_0*(\d+)", original_id)
                if match:
                    new_id = f"Pyrtr1-{match.group(1)}"
                    record.id = new_id
                    record.description = new_id
                    renamed_count += 1

            if i == 0:
                first_after = record.id

        SeqIO.write(records, output_path, "fasta")
        print(f"✅ {portal}: Renamed {renamed_count}/{total} → {output_path}")

        log_data.append({
            "portal": portal,
            "file": os.path.basename(output_path),
            "total_sequences": total,
            "renamed_sequences": renamed_count,
            "first_id_before": first_before,
            "first_id_after": first_after
        })

    except Exception as e:
        print(f"❌ Error processing {portal}: {e}")
        log_data.append({
            "portal": portal,
            "file": os.path.basename(input_path),
            "total_sequences": 0,
            "renamed_sequences": 0,
            "first_id_before": "ERROR",
            "first_id_after": "ERROR"
        })

# -----------------------------
# Save summary log
# -----------------------------
log_df = pd.DataFrame(log_data)
log_df.to_csv(PROTEOME_CUSTOMLOG_PATH, index=False)
print(f"📝 Custom renaming log saved: {PROTEOME_CUSTOMLOG_PATH}")
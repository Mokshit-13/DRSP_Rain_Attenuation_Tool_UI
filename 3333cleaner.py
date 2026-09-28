"""
==========================================================
Legacy Dataset Cleaner
----------------------------------------------------------
Removes rows where Ch-1 == 3333

Processes ONLY:
    NAR_D_M_YYYY.txt

Ignores:
    NAR_F_*.txt
    NAR_N_*.txt

Author : Dedeep
==========================================================
"""

from pathlib import Path
import pandas as pd
import re

# ==========================================================
# CHANGE THIS TO YOUR YEAR FOLDER
# ==========================================================

YEAR_FOLDER = r"F:\2017"

# ==========================================================
# File name pattern
# Only process:
# NAR_1_1_2017.txt
# NAR_31_12_2017.txt
# ==========================================================

FILE_PATTERN = re.compile(
    r"^NAR_\d{1,2}_\d{1,2}_\d{4}\.txt$",
    re.IGNORECASE
)

# ==========================================================
# Clean a single file
# ==========================================================

def clean_file(file_path):

    try:

        df = pd.read_csv(
            file_path,
            sep=r"\s+",
            header=None,
            names=["Time", "Ch-1", "Ch-2"],
            dtype=str,
            engine="python"
        )

        original_rows = len(df)

        # Convert Ch-1 to numeric
        df["Ch-1"] = pd.to_numeric(df["Ch-1"], errors="coerce")

        # Remove rows where Ch-1 == 3333
        df = df[df["Ch-1"] != 3333]

        removed_rows = original_rows - len(df)

        # Save back to original file
        df.to_csv(
            file_path,
            sep="\t",
            header=False,
            index=False
        )

        return removed_rows

    except Exception as e:
        print(f"ERROR : {file_path.name}")
        print(e)
        return None


# ==========================================================
# Main
# ==========================================================

def main():

    year_folder = Path(YEAR_FOLDER)

    if not year_folder.exists():
        print("Folder does not exist.")
        return

    txt_files = sorted(
        f for f in year_folder.rglob("*.txt")
        if FILE_PATTERN.match(f.name)
    )

    if len(txt_files) == 0:
        print("No legacy data files found.")
        return

    print("=" * 70)
    print("Cleaning Legacy Dataset (Removing Ch-1 == 3333)")
    print("=" * 70)

    total_removed = 0
    processed_files = 0

    for file in txt_files:

        removed = clean_file(file)

        if removed is not None:
            processed_files += 1
            total_removed += removed

            print(f"{file.name:<35} Removed: {removed}")

    print("\n" + "=" * 70)
    print("Cleaning Completed")
    print("=" * 70)
    print(f"Files Processed : {processed_files}")
    print(f"Total Rows Removed : {total_removed}")
    print("=" * 70)


if __name__ == "__main__":
    main()
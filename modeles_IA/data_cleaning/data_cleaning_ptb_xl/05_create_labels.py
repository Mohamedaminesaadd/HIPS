from pathlib import Path
import ast

import pandas as pd


# ==========================================================
# Configuration
# ==========================================================
path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)


DATABASE_PATH = PTBXL_DIR / "ptbxl_database.csv"
SCP_PATH = PTBXL_DIR / "scp_statements.csv"


TARGET_CLASSES = [
    "NORM",
    "MI",
    "STTC",
    "CD",
    "HYP",
]


# ==========================================================
# 1. Load files
# ==========================================================

df = pd.read_csv(DATABASE_PATH)

scp = pd.read_csv(
    SCP_PATH,
    index_col=0
)


# ==========================================================
# 2. Decode scp_codes
# ==========================================================

df["scp_codes"] = df["scp_codes"].apply(
    ast.literal_eval
)


# ==========================================================
# 3. Function:
#    SCP codes → diagnostic classes
# ==========================================================

def get_diagnostic_classes(scp_codes):

    diagnostic_classes = set()

    for code in scp_codes:

        # Check whether the SCP code exists
        # in scp_statements.csv

        if code not in scp.index:
            continue

        row = scp.loc[code]

        # Only keep diagnostic statements

        if row["diagnostic"] == 1:

            diagnostic_class = row[
                "diagnostic_class"
            ]

            if pd.notna(diagnostic_class):

                diagnostic_classes.add(
                    diagnostic_class
                )

    return sorted(diagnostic_classes)


# ==========================================================
# 4. Test the function
# ==========================================================

print("=" * 70)
print("SCP CODE → DIAGNOSTIC CLASS")
print("=" * 70)


for i in range(10):

    codes = df.iloc[i]["scp_codes"]

    classes = get_diagnostic_classes(
        codes
    )

    print(
        f"\nECG ID: {df.iloc[i]['ecg_id']}"
    )

    print(
        f"SCP codes: {codes}"
    )

    print(
        f"Diagnostic classes: {classes}"
    )
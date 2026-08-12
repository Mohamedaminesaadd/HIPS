from pathlib import Path
import ast

import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------


path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)


DATABASE_PATH = PTBXL_DIR / "ptbxl_database.csv"


# --------------------------------------------------
# 1. Load metadata
# --------------------------------------------------

df = pd.read_csv(DATABASE_PATH)


# --------------------------------------------------
# 2. Show original SCP codes
# --------------------------------------------------

print("=" * 60)
print("ORIGINAL SCP CODES")
print("=" * 60)

for i in range(5):

    print(
        f"ECG {df.iloc[i]['ecg_id']}: "
        f"{df.iloc[i]['scp_codes']}"
    )


# --------------------------------------------------
# 3. Convert strings → dictionaries
# --------------------------------------------------

df["scp_codes"] = df["scp_codes"].apply(
    ast.literal_eval
)


# --------------------------------------------------
# 4. Show decoded SCP codes
# --------------------------------------------------

print("\n" + "=" * 60)
print("DECODED SCP CODES")
print("=" * 60)

for i in range(5):

    codes = df.iloc[i]["scp_codes"]

    print(
        f"ECG {df.iloc[i]['ecg_id']}: "
        f"{codes}"
    )


# --------------------------------------------------
# 5. Check the type
# --------------------------------------------------

print("\n" + "=" * 60)
print("TYPE CHECK")
print("=" * 60)

print(
    type(df.iloc[0]["scp_codes"])
)


# --------------------------------------------------
# 6. Show individual codes
# --------------------------------------------------

print("\n" + "=" * 60)
print("INDIVIDUAL CODES")
print("=" * 60)

for i in range(5):

    codes = df.iloc[i]["scp_codes"]

    print(f"\nECG {df.iloc[i]['ecg_id']}")

    for code, score in codes.items():

        print(
            f"  {code} -> {score}"
        )
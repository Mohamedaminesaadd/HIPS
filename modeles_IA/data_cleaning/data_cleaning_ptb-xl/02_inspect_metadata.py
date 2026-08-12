from pathlib import Path

import pandas as pd


path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)


DATABASE_PATH = PTBXL_DIR / "ptbxl_database.csv"


# --------------------------------------------------
# 1. Load metadata
# --------------------------------------------------

df = pd.read_csv(DATABASE_PATH)


# --------------------------------------------------
# 2. Basic information
# --------------------------------------------------

print("=" * 60)
print("PTB-XL METADATA")
print("=" * 60)

print(f"\nNumber of ECG recordings: {len(df)}")

print(f"Number of columns: {len(df.columns)}")


# --------------------------------------------------
# 3. Dataset shape
# --------------------------------------------------

print("\nShape:")
print(df.shape)


# --------------------------------------------------
# 4. Columns
# --------------------------------------------------

print("\nColumns:")

for column in df.columns:
    print(f" - {column}")


# --------------------------------------------------
# 5. First 5 records
# --------------------------------------------------

print("\nFirst 5 records:")
print(df.head())


# --------------------------------------------------
# 6. Important columns
# --------------------------------------------------

important_columns = [
    "ecg_id",
    "patient_id",
    "age",
    "sex",
    "scp_codes",
    "filename_lr",
    "filename_hr",
    "strat_fold",
]

print("\nImportant columns:")
print(df[important_columns].head())